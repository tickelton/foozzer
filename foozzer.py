#!/usr/bin/env python3

import os
import re
import sys
import argparse
import subprocess
#import pyautogui
import importlib
import pkgutil
import logging

import foozzer.mutators
import foozzer.runners

from time import sleep
from shutil import copyfile
from subprocess import PIPE, STDOUT, Popen
from threading  import Thread
from queue import Queue, Empty

ON_POSIX = os.name == 'posix'


# binaries
VALGRIND = '/usr/bin/valgrind'
XTERM = '/usr/bin/xterm'
LS = '/usr/bin/ls'
FOOBAR = r'C:\Program Files (x86)\foobar2000\foobar2000.exe'
if ON_POSIX:
    DRMEMORY_BIN = 'drmemory'
else:
    DRMEMORY_BIN = r'drmemory.exe'
DRMEMORY_PARAMS = r'-batch'

# playlists
PL_GARBAGE = r'D:\Workspace\foobar_fuzzing\in\garbage.fpl'
PL_GENERIC = r'D:\Workspace\foobar_fuzzing\in\generic.fpl'
PL_FUZZ = r'D:\Workspace\foobar_fuzzing\in\fuzz_pl.fpl'
#PL_TEMPLATE = r'D:\Workspace\foobar_fuzzing\in\fuzzing_base.fpl'
PL_TEMPLATE = r'D:\Workspace\foobar_fuzzing\in\fuzzing_minimal.fpl'

# buttons
NEW_PLAYLIST = r'D:\Workspace\foozzer\images\new_playlist.png'
RM_PL = r'D:\Workspace\foozzer\images\remove_playlist.png'
START_NORMALLY = r'D:\Workspace\foozzer\images\start_normally.png'
TITLE_INFORMATION = r'D:\Workspace\foozzer\images\information3.png'
LOAD_PL = r'D:\Workspace\foozzer\images\load_playlist.png'
WINDOW_LOAD_PL = r'D:\Workspace\foozzer\images\window_load_playlist.png'
MENU_FILE = r'D:\Workspace\foozzer\images\file.png'
MENU_FUZZ_PL = r'D:\Workspace\foozzer\images\fuzz_pl.png'

# commands
CMD_STOP = '/stop'
CMD_LOAD_PL = '/command:"Load playlist..."'

# misc constants
RUNFILE = r'D:\Temp\foozzer.run'
PAUSEFILE = r'D:\Temp\foozzer.pause'
STATE_FILE = r'D:\Workspace\foobar_fuzzing\out\state.txt'
LOG_OUTFILE = 'log.txt'
PL_FUZZ_NAME = 'fuzz_pl.fpl'
#ON_POSIX = 'posix' in sys.builtin_module_names
GUI_CHECK_INTERVAL = 0.1 # time to wait in between checks for UI element
GUI_CHECK_TIMEOUT = 30 # max number of GUI_CHECK_INTERVAL iterations

# logging configuration
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.ERROR)


def run_cmd(cmd_str):
    subprocess.run([FOOBAR, cmd_str])

def del_pl(btn_pl_img):
    btn_pl = gui_wait_for(btn_pl_img)
    btn_pl_center = pyautogui.center(btn_pl)
    pyautogui.click(button='right', x=btn_pl_center.x, y=btn_pl_center.y)
    del_pl = gui_wait_for(RM_PL)
    del_pl_center = pyautogui.center(del_pl)
    pyautogui.click(x=del_pl_center.x, y=del_pl_center.y)

def load_pl(pl_name):
    btn_file = gui_wait_for(MENU_FILE)
    btn_file_center = pyautogui.center(btn_file)
    pyautogui.click(x=btn_file_center.x, y=btn_file_center.y)
    btn_load = gui_wait_for(LOAD_PL)
    btn_load_center = pyautogui.center(btn_load)
    pyautogui.click(x=btn_load_center.x, y=btn_load_center.y)
    gui_wait_for(WINDOW_LOAD_PL)
    pyautogui.write(pl_name)
    pyautogui.press('enter')

def close_info():
    for i in range(3):
        win_info = pyautogui.locateOnScreen(TITLE_INFORMATION)
        if win_info:
            pyautogui.click(x=win_info.left+win_info.width-5, y=win_info.top+5)
            return

def reset_playlists():
    while pyautogui.locateOnScreen(MENU_FUZZ_PL):
        del_pl(MENU_FUZZ_PL)
        sleep(1)

def gui_wait_start(log_fd):
    i = 0

    while not pyautogui.locateOnScreen(MENU_FILE) and not pyautogui.locateOnScreen(START_NORMALLY):
        if i > GUI_CHECK_TIMEOUT:
            raise FoozzerUIError('start failed')
        i += 1
        # initial start takes a while, so we just use triple the regular timeout
        sleep(GUI_CHECK_INTERVAL * 3)

    pos = pyautogui.locateOnScreen(START_NORMALLY)
    if pos:
        log_fd.write('ABNORMAL TERMINATION ! POTENTIAL BUG !!')
        pos_center = pyautogui.center(pos)
        pyautogui.click(x=pos_center.x, y=pos_center.y)
        gui_wait_for(MENU_FILE)


def gui_wait_for(element):
    i = 0

    while i < GUI_CHECK_TIMEOUT:
        pos = pyautogui.locateOnScreen(element)
        if pos:
            return pos
        i += 1
        sleep(GUI_CHECK_INTERVAL)

    raise FoozzerUIError('failed to locate {}'.format(element))

def enqueue_output(out, queue):
    for line in iter(out.readline, ''):
        queue.put(line)
    out.close()

def create_next_input(filename, template):
    outfile = open(filename, 'wb')
    infile = open(template, 'rb', buffering=0)

class FoozzerUIError(Exception):

    def __init__(self, message):
        self.message = message

def startall(q, drmemory_bin, target_cmdline):
    p = Popen(
        [drmemory_bin, DRMEMORY_PARAMS, '--'] + target_cmdline,
        stdout=PIPE,
        stderr=STDOUT,
        bufsize=1,
        universal_newlines=True,
        close_fds=ON_POSIX
    )
    t = Thread(target=enqueue_output, args=(p.stdout, q))
    #t.daemon = True # thread dies with the program
    t.start()
    sleep(1)
    if p.poll() != None:
        logger.error('SOMETHING WENT WRONG!!')
        t.join()
        sys.exit(1)

    return p, t

def stop_processes(target):
    if ON_POSIX:
        os.system('pkill {}'.format(target))
    else:
        os.system('taskkill /t /im {}'.format(target))
        sleep(2)
        os.system('taskkill /t /im drmemory.exe')

def stopall(t):
    stop_processes()
    sleep(5)
    t.join()

def clear_queue(q, outfile):
    while True:
        # read line without blocking
        try:  line = q.get_nowait() # or q.get(timeout=.1)
        except Empty:
            break
        else: # got line
            outfile.write(line)

def iter_namespace(ns_pkg):
    return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + ".")

class ActionListMutators(argparse.Action):
	def __init__(self, option_strings, dest, const, **kwargs):
		self._descriptions = const
		super(ActionListMutators, self).__init__(option_strings, dest, **kwargs)
	def __call__(self, parser, namespace, values, option_string=None):
		print('\navailable mutators:\n')
		for k in self._descriptions.keys():
			print('  {} : {}'.format(k, self._descriptions[k]))
		print('')
		sys.exit(0)

class ActionListPlugins(argparse.Action):
    def __init__(self, option_strings, dest, const, **kwargs):
        self._descriptions = const
        super(ActionListPlugins, self).__init__(option_strings, dest, **kwargs)
    def __call__(self, parser, namespace, values, option_string=None):
        for plugin_type in self._descriptions:
            print('\n{}:\n'.format(plugin_type))
            for k, v in self._descriptions[plugin_type].items():
                print('  {} : {}'.format(k, v))
            print('')
        sys.exit(0)

def discover_plugins(ns):
    plugins = {}

    for finder, name, ispkg in iter_namespace(ns):
        try:
            plugins.update(importlib.import_module(name).get_module_info())
        except(AttributeError):
            # If the module does not provide a get_module_info function
            # it is probably an abstract base class or utility library.
            # Anyways, since in that case we have no way to determine its
            # correct entry point, we just ignore it.
            pass

    return plugins

def main():

    mutators = discover_plugins(foozzer.mutators)
    runners = discover_plugins(foozzer.runners)

    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', '-v', action='count', default=0)
    parser.add_argument(
		'-L',
		nargs=0,
		action=ActionListPlugins,
		help='describe available plugins',
		const={
            'Mutators': {n: mutators[n][0] for n in mutators.keys()},
            'Runners': {n: runners[n][0] for n in runners.keys()},
        }
	)
    parser.add_argument(
        '-i',
        required=True,
        help='input directory'
    )
    parser.add_argument(
        '-o',
        required=True,
        help='output directory'
    )
    parser.add_argument(
        '-D',
        required=True,
        help='Dr.Memory bin directory'
    )
    parser.add_argument(
        '-m',
        required=True,
        choices = [m for m in mutators.keys()],
        help='mutator to use'
    )
    parser.add_argument(
        '-r',
        required=True,
        choices = [m for m in runners.keys()],
        help='runner to use'
    )
    parser.add_argument('runner_args', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.verbose == 1:
        logger.setLevel(logging.WARNING)
    elif args.verbose == 2:
        logger.setLevel(logging.INFO)
    elif args.verbose > 2:
        logger.setLevel(logging.DEBUG)

    runner_class = runners[args.r][1]
    runner = runner_class(args.runner_args[1:])
    target_process = runner.get_process_name()
    input_mutator = mutators[args.m][1]

    #stop_processes(target_process)

    q = Queue()

    p, t = startall(q, os.path.join(args.D, DRMEMORY_BIN), runner.get_cmdline())

    logger.info('Opening logfile')
    log_outfile = open(os.path.join(args.o, LOG_OUTFILE), 'a')
    logger.debug('FPLInFILE()')
    mutator = input_mutator(args.i, args.o)

    i = 0
    logger.debug('Clearing queue initially')
    clear_queue(q, log_outfile)

    sleep(30)
    print('STOPPING!!!!!')
    stop_processes(target_process)
    log_outfile.close()
    sys.exit(2)

    logger.info('Waiting for start')
    gui_wait_start(log_outfile)
    logger.debug('Resetting playlists')
    reset_playlists()
    logger.info('Dry run')
    log_outfile.flush()
    log_outfile.write('FOOZZER: DRY RUN\n')
    log_outfile.flush()
    logger.debug('copying generic playlist')
    copyfile(PL_GENERIC, PL_FUZZ)
    logger.debug('loading playlist')
    load_pl(PL_FUZZ_NAME)
    logger.debug('checking for info window')
    close_info()
    logger.debug('closing playlist')
    del_pl(MENU_FUZZ_PL)

    logger.info('MAINLOOP START')
    while os.path.isfile(RUNFILE):
        for input_file, state_msg in mutator:
            try:
                logger.debug('clearing queue')
                clear_queue(q, log_outfile)

                logger.debug('checking if Dr.Memory is still running')
                if p.poll() != None:
                    logger.info('RESTARTING Dr.Memory')
                    stopall(t)
                    p, t = startall(q)
                    gui_wait_start(log_outfile)

                if os.path.isfile(PAUSEFILE):
                    logger.info('pausing...')
                while os.path.isfile(PAUSEFILE):
                    sleep(1)

                logger.debug('Iteration: {}}\n'.format(state_msg))
                log_outfile.flush()
                log_outfile.write('FOOZZER: Iteration: {}\n'.format(state_msg))
                log_outfile.flush()
                logger.debug('loading playlist')
                load_pl(input_file)
                logger.debug('closing info window')
                close_info()
                logger.debug('closing playlist')
                del_pl(MENU_FUZZ_PL)
            except FoozzerUIError as e:
                log_outfile.write('Resetting after UIError: {}'.format(e))
                logger.warning('Resetting after UIError: {}'.format(e))
                clear_queue(q, log_outfile)
                if p.poll() == None:
                    p.terminate()
                stopall(t)
                p, t = startall(q)
                gui_wait_start(log_outfile)

        i += 1

    logger.info('MAINLOOP END')
    if p.poll() == None:
        logger.debug('terminating')
        p.terminate()
        stopall(t)

    clear_queue(q, log_outfile)
    log_outfile.flush()
    log_outfile.write('FOOZZER: FINISHED')
    log_outfile.close()
    logger.info('FINISHED')



if __name__ == '__main__':
    main()
