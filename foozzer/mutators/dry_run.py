#!/usr/bin/env python3
"""
Dry run mutator.

Copies the input file to the output directory
and initiates exactly one run with the
unmodified file.

Can be used to check if the fuzzing setup is
working in general and to rule out any problems
caused by faulty mutators.
"""

# Copyright (c) 2020 tick <tickelton@gmail.com>
# SPDX-License-Identifier:	ISC

import os
import logging

MUTATOR_NAME = 'dry_run'
OUTFILE_NAME = 'fuzz_pl.fpl'

log = logging.getLogger(__name__)

def get_module_info():
    """Returns data used by main function to discover plugins."""

    return {
        MUTATOR_NAME: (
            'Single run with the first file in the input directory and not mutations applied',
            DryRunMutator
        )
    }

class DryRunMutator:
    """
    The mutator class works as an iterator that produces a mutation
    of the input file on every iteration.

    In this particular case only a single iteration with an
    unmodified input file is performed.
    """

    def __init__(self, indir, outdir):
        self._infile_name = ''
        self._infile_path = ''
        self._once = False
        self._indir = indir
        self._outpath = os.path.join(outdir, OUTFILE_NAME)

        for (fname, fpath) in ((f, os.path.join(self._indir, f)) for f in os.listdir(self._indir)):
            if os.path.isfile(fpath):
                self._infile_name = fname
                self._infile_path = fpath

        if not self._infile_path:
            raise FileNotFoundError('No usable file in input directory')

    def __iter__(self):
        return self

    def __next__(self):
        if self._once:
            raise StopIteration()

        self._once = True

        with open(self._infile_path, 'rb') as infile:
            with open(self._outpath, 'wb') as outfile:
                outfile.write(infile.read())

        return OUTFILE_NAME, "Dry Run"
