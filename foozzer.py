#!/usr/bin/env python3

import os
import re
import sys
import argparse
import subprocess
import pyautogui
import importlib
import pkgutil

import foozzer.mutators

from time import sleep
from shutil import copyfile
from subprocess import PIPE, STDOUT, Popen
from threading  import Thread
from queue import Queue, Empty



# binaries
VALGRIND = '/usr/bin/valgrind'
XTERM = '/usr/bin/xterm'
LS = '/usr/bin/ls'
FOOBAR = r'C:\Program Files (x86)\foobar2000\foobar2000.exe'
DRMEMORY = r'C:\Program Files (x86)\Dr. Memory\bin\drmemory.exe'
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
LOG_OUTFILE = r'D:\Workspace\foobar_fuzzing\out\log.txt'
PL_FUZZ_NAME = 'fuzz_pl.fpl'
ON_POSIX = 'posix' in sys.builtin_module_names
GUI_CHECK_INTERVAL = 0.1 # time to wait in between checks for UI element
GUI_CHECK_TIMEOUT = 30 # max number of GUI_CHECK_INTERVAL iterations


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

def startall(q):
    p = Popen([DRMEMORY, DRMEMORY_PARAMS, FOOBAR], stdout=PIPE, stderr=STDOUT, bufsize=1, universal_newlines=True, close_fds=ON_POSIX)
    t = Thread(target=enqueue_output, args=(p.stdout, q))
    #t.daemon = True # thread dies with the program
    t.start()
    sleep(1)
    if p.poll() != None:
        print('SOMETHING WENT WRONG!!')
        t.join()
        sys.exit(1)

    return p, t

def stop_processes():
    os.system("taskkill /t /im foobar2000.exe")
    sleep(2)
    os.system("taskkill /t /im drmemory.exe")

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

def discover_mutators():
    mutators = {}

    for finder, name, ispkg in iter_namespace(foozzer.mutators):
        mutators.update(importlib.import_module(name).get_module_info())

    return mutators

def main():

    mutators = discover_mutators()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-m',
        required=True,
        choices = [m for m in mutators.keys()],
        help='mutator to use'
    )
    args = parser.parse_args()

    playlist_mutator = mutators[args.m]

    stop_processes()

    q = Queue()

    p, t = startall(q)

    print('Opening logfile')
    log_outfile = open(LOG_OUTFILE, 'a')
    print('FPLInFILE()')
    fpl = playlist_mutator(PL_FUZZ, PL_TEMPLATE)

    i = 0
    print('Clearing queue initially')
    clear_queue(q, log_outfile)

    print('Waiting for start')
    gui_wait_start(log_outfile)
    print('Resetting playlists')
    reset_playlists()
    print('Dry run')
    log_outfile.flush()
    log_outfile.write('FOOZZER: DRY RUN\n')
    log_outfile.flush()
    print('copying generic playlist')
    copyfile(PL_GENERIC, PL_FUZZ)
    print('loading playlist')
    load_pl(PL_FUZZ_NAME)
    print('checking for info window')
    close_info()
    print('closing playlist')
    del_pl(MENU_FUZZ_PL)

    print('MAINLOOP START')
    while os.path.isfile(RUNFILE):
        try:
            print('clearing queue')
            clear_queue(q, log_outfile)

            print('checking if Dr.Memory is still running')
            if p.poll() != None:
                print('RESTARTING Dr.Memory')
                stopall(t)
                p, t = startall(q)
                gui_wait_start(log_outfile)

            if os.path.isfile(PAUSEFILE):
                print('pausing...')
            while os.path.isfile(PAUSEFILE):
                sleep(1)

            print('fpl.next()')
            fpl_iteration = fpl.next()
            if fpl_iteration == (-1, -1):
                print('mutations exhausted; exiting')
                break
            print('Iteration: t_offset={} mod_offset={}\n'.format(fpl_iteration[0], fpl_iteration[1]))
            log_outfile.flush()
            log_outfile.write('FOOZZER: Iteration: t_offset={} mod_offset={}\n'.format(fpl_iteration[0], fpl_iteration[1]))
            log_outfile.flush()
            print('loading playlist')
            load_pl(PL_FUZZ_NAME)
            print('closing info window')
            close_info()
            print('closing playlist')
            del_pl(MENU_FUZZ_PL)
        except FoozzerUIError as e:
            log_outfile.write('Resetting after UIError: {}'.format(e))
            print('Resetting after UIError: {}'.format(e))
            clear_queue(q, log_outfile)
            if p.poll() == None:
                p.terminate()
            stopall(t)
            p, t = startall(q)
            gui_wait_start(log_outfile)

        i += 1

    print('MAINLOOP END')
    if p.poll() == None:
        print('terminating')
        p.terminate()
        stopall(t)

    clear_queue(q, log_outfile)
    log_outfile.flush()
    log_outfile.write('FOOZZER: FINISHED')
    log_outfile.close()
    print('FINISHED')



if __name__ == '__main__':
    main()
