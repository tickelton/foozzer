#!/usr/bin/env python3

import logging

RUNNER_NAME = 'foobar2k'

log = logging.getLogger(__name__)

def get_module_info():
    return {RUNNER_NAME: ('foobar2000 playlist fuzzer', FB2KRunner)}

class FB2KRunner():

    def __init__(self):
        pass

    def get_cmdline(self):
        pass

    def setup(self):
        pass

    def run(self):
        pass

    def terminate(self):
        pass

