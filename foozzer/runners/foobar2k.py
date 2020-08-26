#!/usr/bin/env python3

import os
import argparse
import logging

RUNNER_NAME = 'foobar2k'
FOOBAR_EXE = r'foobar2000.exe'

log = logging.getLogger(__name__)

def get_module_info():
    return {RUNNER_NAME: ('foobar2000 playlist fuzzer', FB2KRunner)}

class FB2KRunner():

    def __init__(self, args):
        parser = argparse.ArgumentParser(prog=RUNNER_NAME)
        parser.add_argument(
            '-F',
            required=True,
            help='directory containing {}'.format(FOOBAR_EXE)
        )
        self._args = parser.parse_args(args)

    def get_process_name(self):
        return FOOBAR_EXE

    def get_cmdline(self):
        return [os.path.join(self._args.F, FOOBAR_EXE)]

    def setup(self):
        pass

    def run(self):
        pass

    def terminate(self):
        pass

