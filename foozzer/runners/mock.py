#!/usr/bin/env python3
"""
A mock runner to test the correct operation of mutators

Usage: ... [-h] -T TARGET -- [TARGET_ARGS]

Options:
    -h
    --help      show this help message and exit

    -t TARGET   target binary to run

    TARGET_ARGS optional list of command line parameters
                passed to the target binary

"""

# Copyright (c) 2020 tick <tickelton@gmail.com>
# SPDX-License-Identifier:	ISC

import argparse
import logging


RUNNER_NAME = 'mock'

log = logging.getLogger(__name__)

def get_module_info():
    """Returns data used by main function to discover plugins."""

    return {RUNNER_NAME: ('mock runner', MockRunner)}


class MockRunner():
    """
    Provides a mock implementation of a runner class.
    """

    def __init__(self, args):
        parser = argparse.ArgumentParser(prog=RUNNER_NAME)
        parser.add_argument(
            '-t',
            required=True,
            help='target binary to run'
        )
        parser.add_argument('target_args', nargs=argparse.REMAINDER)
        self._args = parser.parse_args(args)

    def get_process_name(self):
        """Returns the name of the process to be started."""

        return self._args.t

    def get_cmdline(self):
        """Returns the command line arguments the target process is to be started with."""

        return [self._args.t] + self._args.target_args[1:]

    def setup(self):
        return

    def run(self, input_file):
        """
        Runs a single fuzzing iteration.

        Debug code to inspect the environment and parameters of the
        runner can be added here.
        """

        log.info('Received input_file=%s', input_file)
        return True

    def terminate(self):
        """
        Terminates auxiliary processes.

        Currently unused.
        """
        return
