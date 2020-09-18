#!/usr/bin/env python3
"""
Example mutator for flipping individual bits

The mutator iteratively flips every individual bit in
the input file.
"""

# Copyright (c) 2020 tick <tickelton@gmail.com>
# SPDX-License-Identifier:	ISC

import os
import configparser
import logging

MUTATOR_NAME = 'bitflip'
STATE_FILE_NAME = MUTATOR_NAME + '_state.txt'
OUTFILE_NAME = 'bitflip.out'

log = logging.getLogger(__name__)

def get_module_info():
    """Returns data used by main function to discover plugins."""

    return {MUTATOR_NAME: ('Flips individual bits in the input file', BitflipMutator)}

class BitflipMutator:
    """
    The mutator class works as an iterator that produces a mutation
    of the input file on every iteration.
    """

    def __init__(self, indir, outdir):
        self._infile_size = 0
        self._processing_finished = False
        self._infile_path = None
        self._state = configparser.ConfigParser()
        self._state_file_path = os.path.join(outdir, STATE_FILE_NAME)
        self._outdir = outdir
        self._outpath = os.path.join(outdir, OUTFILE_NAME)
        self._indir = indir
        self._state.read(self._state_file_path)

        self._offset = self._state['DEFAULT'].getint('offset', 0)
        self._mod = self._state['DEFAULT'].getint('mod', 0)
        if self._mod > 7:
            raise ValueError('mod index out of range; state file for wrong mutator ?')
        self._infile_name = self._state['DEFAULT'].get('infile', '')
        if self._infile_name:
            self._infile_path = os.path.join(indir, self._infile_name)
        self._infiles_processed = self._state['DEFAULT'].get('completed', '').split(sep='\n')

        if self._infile_path and os.path.isfile(self._infile_path):
            self._read_infile()

    def __iter__(self):
        return self

    def __next__(self):
        if (self._offset > self._infile_size - 1 or
                not self._infile_path or
                not os.path.isfile(self._infile_path) or
                self._infile_name in self._infiles_processed):
            self._next_infile()
            if self._processing_finished:
                self._write_state()
                raise StopIteration()
            self._read_infile()

        s_cur = 'infile={} offset={}, mod={}'.format(self._infile_name, self._offset, self._mod)
        self._write_state()

        with open(self._outpath, 'wb') as outfile:
            outfile.write(self._template)
            outfile.seek(self._offset)
            outfile.write(
                bytes([self._template[self._offset] & ~(1 << self._mod)])
            )

        self._mod = (self._mod + 1 ) % 8
        if self._mod == 0:
            self._offset += 1

        self._write_state()

        return OUTFILE_NAME, s_cur

    def _write_state(self):
        """
        Saves the current state to a file so fuzzing can be stopped
        and continued at a later time.
        """

        self._state['DEFAULT']['offset'] = str(self._offset)
        self._state['DEFAULT']['mod'] = str(self._mod)
        self._state['DEFAULT']['infile'] = self._infile_name
        self._state['DEFAULT']['completed'] = '\n'.join(self._infiles_processed)

        with open(self._state_file_path, 'w') as fd:
            self._state.write(fd)

    def _next_infile(self):
        """Finds the next suitable input file in the input directory."""

        if self._infile_name and not self._infile_name in self._infiles_processed:
            self._infiles_processed.append(self._infile_name)
        for (fname, fpath) in ((f, os.path.join(self._indir, f)) for f in os.listdir(self._indir)):
            if os.path.isfile(fpath) and fname not in self._infiles_processed:
                self._infile_name = fname
                self._infile_path = fpath
                self._offset = 0
                self._mod = 0
                return
        self._infile_name = ''
        self._processing_finished = True


    def _read_infile(self):
        with open(self._infile_path, 'rb') as infile:
            self._template = infile.read()
        self._infile_size = len(self._template)
