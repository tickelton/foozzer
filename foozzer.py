#!/usr/bin/env python3
"""
A cross platform fuzzing framework primarily targeting GUI applications.

usage: foozzer.py [-h] [--verbose] [-L] -i I -o O -D D -m MUTATOR -r RUNNER -- RUNNER_ARGS
  runner_args

Options:

    -h
    --help          show help message and exit

    -v
    --verbose       increase output verbosity (can be given multiple times)

    -L              describe available plugins

    -i I            input directory

    -o O            output directory

    -D D            Dr.Memory bin directory

    -m M            mutator to use

    -r R            runner to use

    RUNNER_ARGS     arguments passed to selected runner module

"""

import os
import sys
import argparse
import importlib
import pkgutil
import logging

from time import sleep
from subprocess import PIPE, STDOUT, Popen
from threading  import Thread
from queue import Queue, Empty

import foozzer.mutators
import foozzer.runners


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
    """Helper function for non-blocking reading of child STDOUT."""

    for line in iter(out.readline, ''):
        queue.put(line)
    out.close()

def clear_queue(queue, outfile):
    """Helper function for non-blocking reading of child STDOUT."""

    while True:
        # non-blocking readline
        try:
            line = queue.get_nowait()
        except Empty:
            break
        else:
            outfile.write(line)


def startall(queue, drmemory_bin, target_cmdline):
    """Starts fuzzee child process and thread for STDOUT queue."""

    drmem = Popen(
        [drmemory_bin, DRMEMORY_PARAMS, '--'] + target_cmdline,
        stdout=PIPE,
        stderr=STDOUT,
        bufsize=1,
        universal_newlines=True,
        close_fds=ON_POSIX
    )
    qthread = Thread(target=enqueue_output, args=(drmem.stdout, queue))
    #qthread.daemon = True
    qthread.start()
    sleep(1)
    if drmem.poll() is not None:
        logger.error('SOMETHING WENT WRONG!!')
        qthread.join()
        sys.exit(1)

    return drmem, qthread

def stop_processes(target):
    """Stops fuzzee and Dr.Memrory processes, if running."""

    if ON_POSIX:
        os.system('pkill {}'.format(target))
    else:
        os.system('taskkill /t /im {}'.format(target))
        sleep(2)
        os.system('taskkill /t /im drmemory.exe')

def stopall(qthread, target):
    """Stops child processes and queue thread."""

    stop_processes(target)
    sleep(5)
    qthread.join()

class ActionListPlugins(argparse.Action):
    """Argparser helper class to show plugins descriptions."""

    def __init__(self, option_strings, dest, const, **kwargs):
        self._descriptions = const
        super().__init__(option_strings, dest, **kwargs)
    def __call__(self, parser, namespace, values, option_string=None):
        for plugin_type in self._descriptions:
            print('\n{}:\n'.format(plugin_type))
            for k, val in self._descriptions[plugin_type].items():
                print('  {} : {}'.format(k, val))
            print('')
        sys.exit(0)

def iter_namespace(ns_pkg):
    """Helper function for plugin discovery."""

    return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + ".")

def discover_plugins(namespc):
    """
    Discovers mutator and runner plugins.

    Retrieves entry points of the modules and descriptions for help texts.
    """

    plugins = {}

    for finder, name, ispkg in iter_namespace(namespc):
        try:
            plugins.update(importlib.import_module(name).get_module_info())
        except AttributeError:
            # If the module does not provide a get_module_info function
            # it is probably an abstract base class or utility library.
            # Anyways, since in that case we have no way to determine its
            # correct entry point, we just ignore it.
            pass

    return plugins

def do_parse_args(args, mutators, runners):
    """Argument parsing helper function."""

    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', '-v', action='count', default=0)
    parser.add_argument(
		'-L',
		nargs=0,
		action=ActionListPlugins,
		help='describe available plugins',
		const={
            'Mutators': {n: mutators[n][0] for n in mutators},
            'Runners': {n: runners[n][0] for n in runners},
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
        choices = [m for m in mutators],
        help='mutator to use'
    )
    parser.add_argument(
        '-r',
        required=True,
        choices = [m for m in runners],
        help='runner to use'
    )
    parser.add_argument('runner_args', nargs=argparse.REMAINDER)
    return parser.parse_args(args)

def main(args=None):
    """foozzer.py main function"""

    mutators = discover_plugins(foozzer.mutators)
    runners = discover_plugins(foozzer.runners)

    args = do_parse_args(args, mutators, runners)
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

    queue = Queue()

    drmem, qthread = startall(queue, os.path.join(args.D, DRMEMORY_BIN), runner.get_cmdline())

    logger.info('Opening logfile')
    log_outfile = open(os.path.join(args.o, LOG_OUTFILE), 'a')
    logger.debug('FPLInFILE()')
    runfile_path = os.path.join(args.o, RUNFILE)
    pausefile_path = os.path.join(args.o, PAUSEFILE)
    mutator = input_mutator(args.i, args.o)

    i = 0
    logger.debug('Clearing queue initially')
    clear_queue(queue, log_outfile)

    stop_processes(target_process)

    runner.setup()
    log_outfile.flush()

    logger.info('MAINLOOP START')
    for input_file, state_msg in mutator:
        if not os.path.isfile(runfile_path):
            logger.info('Stopping due to missing run file: %s', runfile_path)
            break

        logger.debug('clearing queue')
        clear_queue(queue, log_outfile)

        logger.debug('checking if Dr.Memory is still running')
        if drmem.poll() is not None:
            logger.info('RESTARTING Dr.Memory')
            stopall(qthread, target_process)
            drmem, qthread = startall(
                queue,
                os.path.join(args.D, DRMEMORY_BIN),
                runner.get_cmdline()
            )
            runner.setup()

        if os.path.isfile(pausefile_path):
            logger.info('pausing...')
        while os.path.isfile(pausefile_path):
            sleep(1)

        logger.debug('Iteration: %s\n', state_msg)
        log_outfile.flush()
        log_outfile.write('FOOZZER: Iteration: {}\n'.format(state_msg))
        log_outfile.flush()
        # TODO: make it clear that an unsuccessful run requires a
        #       reset of the fuzzing process, e.g. by returning
        #       some meaningful value like 'RUNNER_{FAILURE|RESTART}'...
        if not runner.run(input_file):
            log_outfile.write('Resetting after Runner error')
            logger.warning('Resetting after Runner error')
            clear_queue(queue, log_outfile)
            if drmem.poll() is None:
                drmem.terminate()
            stopall(qthread, target_process)
            drmem, qthread = startall(
                queue,
                os.path.join(args.D, DRMEMORY_BIN),
                runner.get_cmdline()
            )
            runner.setup()

        i += 1

    logger.info('MAINLOOP END')
    if drmem.poll() is None:
        logger.debug('terminating')
        drmem.terminate()
        stopall(qthread, target_process)

    clear_queue(queue, log_outfile)
    log_outfile.flush()
    log_outfile.write('FOOZZER: FINISHED')
    log_outfile.close()
    logger.info('FINISHED')



if __name__ == '__main__':
    main()
