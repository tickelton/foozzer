#!/usr/bin/env python3

import os
import sys
import argparse
import importlib
import pkgutil
import logging

import foozzer.mutators
import foozzer.runners

from time import sleep
from subprocess import PIPE, STDOUT, Popen
from threading  import Thread
from queue import Queue, Empty

ON_POSIX = os.name == 'posix'


# binaries
if ON_POSIX:
    DRMEMORY_BIN = 'drmemory'
else:
    DRMEMORY_BIN = 'drmemory.exe'
DRMEMORY_PARAMS = '-batch'

# misc constants
RUNFILE = 'foozzer.run'
PAUSEFILE = 'foozzer.pause'
LOG_OUTFILE = 'log.txt'

# logging configuration
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.ERROR)


def enqueue_output(out, queue):
    for line in iter(out.readline, ''):
        queue.put(line)
    out.close()

def create_next_input(filename, template):
    outfile = open(filename, 'wb')
    infile = open(template, 'rb', buffering=0)

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
    #t.daemon = True
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

def stopall(t, target):
    stop_processes(target)
    sleep(5)
    t.join()

def clear_queue(q, outfile):
    while True:
        # non-blocking readline
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

    stop_processes(target_process)

    q = Queue()

    p, t = startall(q, os.path.join(args.D, DRMEMORY_BIN), runner.get_cmdline())

    logger.info('Opening logfile')
    log_outfile = open(os.path.join(args.o, LOG_OUTFILE), 'a')
    logger.debug('FPLInFILE()')
    runfile_path = os.path.join(args.o, RUNFILE)
    pausefile_path = os.path.join(args.o, PAUSEFILE)
    mutator = input_mutator(args.i, args.o)

    i = 0
    logger.debug('Clearing queue initially')
    clear_queue(q, log_outfile)

    stop_processes(target_process)

    runner.setup()
    log_outfile.flush()

    logger.info('MAINLOOP START')
    for input_file, state_msg in mutator:
        if not os.path.isfile(runfile_path):
            logger.info('Stopping due to missing run file: {}'.format(runfile_path))
            break

        logger.debug('clearing queue')
        clear_queue(q, log_outfile)

        logger.debug('checking if Dr.Memory is still running')
        if p.poll() != None:
            logger.info('RESTARTING Dr.Memory')
            stopall(t, target_process)
            p, t = startall(q, os.path.join(args.D, DRMEMORY_BIN), runner.get_cmdline())
            runner.setup()

        if os.path.isfile(pausefile_path):
            logger.info('pausing...')
        while os.path.isfile(pausefile_path):
            sleep(1)

        logger.debug('Iteration: {}\n'.format(state_msg))
        log_outfile.flush()
        log_outfile.write('FOOZZER: Iteration: {}\n'.format(state_msg))
        log_outfile.flush()
        # TODO: make it clear that an unsuccessful run requires a
        #       reset of the fuzzing process, e.g. by returning
        #       some meaningful value like 'RUNNER_{FAILURE|RESTART}'...
        if not runner.run(input_file):
            log_outfile.write('Resetting after Runner error')
            logger.warning('Resetting after Runner error')
            clear_queue(q, log_outfile)
            if p.poll() == None:
                p.terminate()
            stopall(t, target_process)
            p, t = startall(q, os.path.join(args.D, DRMEMORY_BIN), runner.get_cmdline())
            runner.setup()

        i += 1

    logger.info('MAINLOOP END')
    if p.poll() == None:
        logger.debug('terminating')
        p.terminate()
        stopall(t, target_process)

    clear_queue(q, log_outfile)
    log_outfile.flush()
    log_outfile.write('FOOZZER: FINISHED')
    log_outfile.close()
    logger.info('FINISHED')



if __name__ == '__main__':
    main()
