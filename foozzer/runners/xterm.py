#!/usr/bin/env python3

import os
import argparse
import logging

RUNNER_NAME = 'xterm'
XTERM_BIN = 'xterm'

log = logging.getLogger(__name__)

def get_module_info():
    return {RUNNER_NAME: ('linux example running xterm', XTermRunner)}

class XTermRunner():

    def __init__(self, args):
        pass

    def get_process_name(self):
        return XTERM_BIN

    def get_cmdline(self):
        return [XTERM_BIN]

    def setup(self):
        pass

    def run(self):
        pass

    def terminate(self):
        pass

