#!/usr/bin/env python3

import os
import re
import configparser
import logging

MUTATOR_NAME = 'dry_run'
OUTFILE_NAME = 'fuzz_pl.fpl'

log = logging.getLogger(__name__)

def get_module_info():
    return {MUTATOR_NAME: ('Single run with the first file in the input directory and not mutations applied', DryRunMutator)}

class DryRunMutator:

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

