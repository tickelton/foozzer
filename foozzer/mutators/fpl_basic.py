#!/usr/bin/env python3

import os
import re
import logging

MUTATOR_NAME = 'fpl_basic'
STATE_FILE_NAME = MUTATOR_NAME + '_state.txt'
OUTFILE_NAME = 'fuzz_pl.fpl'

log = logging.getLogger(__name__)

def get_module_info():
    return {MUTATOR_NAME: ('BasicMutator Description', FPLBasicMutator)}

class FPLBasicMutator:
    _GARBAGE_PATTERN = b'Aa0Aa1Aa2Aa3Aa4Aa5Aa6Aa7Aa8Aa9Ab0Ab1Ab2Ab3Ab4Ab5Ab6Ab7Ab8Ab9Ac0Ac1Ac2Ac3Ac4Ac5Ac6Ac7Ac8Ac9Ad0Ad1Ad2Ad3Ad4Ad5Ad6Ad7Ad8Ad9Ae0Ae1Ae2Ae3Ae4Ae5Ae6Ae7Ae8Ae9Af0Af1Af2Af3Af4Af5Af6Af7Af8Af9Ag0Ag1Ag2Ag3Ag4Ag5Ag6Ag7Ag8Ag9Ah0Ah1Ah2Ah3Ah4Ah5Ah6Ah7Ah8Ah9Ai0Ai1Ai2Ai3Ai4Ai5Ai6Ai7Ai8Ai9Aj0Aj1Aj2Aj3Aj4Aj5Aj6Aj7Aj8Aj9Ak0Ak1Ak2Ak3Ak4Ak5Ak6Ak7Ak8Ak9Al0Al1Al2Al3Al4Al5Al6Al7Al8Al9Am0Am1Am2Am3Am4Am5Am6Am7Am8Am9An0An1An2An3An4An5An6An7An8An9Ao0Ao1Ao2Ao3Ao4Ao5Ao6Ao7Ao8Ao9Ap0Ap1Ap2Ap3Ap4Ap5Ap6Ap7Ap8Ap9Aq0Aq1Aq2Aq3Aq4Aq5Aq6Aq7Aq8Aq9Ar0Ar1Ar2Ar3Ar4Ar5Ar6Ar7Ar8Ar9As0As1As2As3As4As5As6As7As8As9At0At1At2At3At4At5At6At7At8At9Au0Au1Au2Au3Au4Au5Au6Au7Au8Au9Av0Av1Av2Av3Av4Av5Av6Av7Av8Av9Aw0Aw1Aw2Aw3Aw4Aw5Aw6Aw7Aw8Aw9Ax0Ax1Ax2Ax3Ax4Ax5Ax6Ax7Ax8Ax9Ay0Ay1Ay2Ay3Ay4Ay5Ay6Ay7Ay8Ay9Az0Az1Az2Az3Az4Az5Az6Az7Az8Az9Ba0Ba1Ba2Ba3Ba4Ba5Ba6Ba7Ba8Ba9Bb0Bb1Bb2Bb3Bb4Bb5Bb6Bb7Bb8Bb9Bc0Bc1Bc2Bc3Bc4Bc5Bc6Bc7Bc8Bc9Bd0Bd1Bd2Bd3Bd4Bd5Bd6Bd7Bd8Bd9Be0Be1Be2Be3Be4Be5Be6Be7Be8Be9Bf0Bf1Bf2Bf3Bf4Bf5Bf6Bf7Bf8Bf9Bg0Bg1Bg2Bg3Bg4Bg5Bg6Bg7Bg8Bg9Bh0Bh1Bh2Bh3Bh4Bh5Bh6Bh7Bh8Bh9Bi0B'

    _byte_mods = [
        b'\x00',
        b'\x01',
        b'\x41',
        b'\xff',
    ]

    _offset = 0
    _mod = 0
    _infile_size = 0
    _infile_name = ''
    _infile_path = ''
    _infiles_processed = []
    _processing_finished = False

    def __init__(self, indir, outdir):
        self._state_file_path = os.path.join(outdir, STATE_FILE_NAME)
        self._outdir = outdir 
        self._outpath = os.path.join(outdir, OUTFILE_NAME)
        self._indir = indir

        if os.path.isfile(self._state_file_path):
            with open(self._state_file_path, 'r') as fd:
                for line in fd.readlines():
                    match = re.search(r'offset=(\d+)', line)
                    if match:
                        self._offset = int(match.group(1))
                        continue
                    match = re.search(r'mod=(\d+)', line)
                    if match:
                        self._mod = int(match.group(1))
                        continue
                    match = re.search(r'infile=([a-zA-Z0-9_\.]+)', line)
                    if match:
                        self._infile_name = match.group(1)
                        self._infile_path = os.path.join(indir, self._infile_name)
                        continue
                    match = re.search(r'completed=([a-zA-Z0-9_\.]+)', line)
                    if match:
                        self._infiles_processed.append(match.group(1))
                        continue

        if  self._infile_path and os.path.isfile(self._infile_path):
            self._read_infile()

    def __iter__(self):
        return self

    def __next__(self):
        if self._offset > self._infile_size - 1 or not self._infile_path or not os.path.isfile(self._infile_path):
            self._next_infile()
            if self._processing_finished:
                self._write_state()
                raise StopIteration()
            else:
                self._read_infile()

        s_cur = 'infile={} offset={}, mod={}'.format(self._infile_name, self._offset, self._mod)
        self._write_state()

        with open(self._outpath, 'wb') as outfile:
            outfile.write(self._template)
            outfile.write(self._GARBAGE_PATTERN)
            outfile.seek(self._offset)
            outfile.write(self._byte_mods[self._mod])

        self._mod = (self._mod + 1 ) % len(self._byte_mods)
        if self._mod == 0:
            self._offset += 1

        self._write_state()

        return OUTFILE_NAME, s_cur

    def _write_state(self):
        with open(self._state_file_path, 'w') as fd:
            fd.write('offset={}\n'.format(self._offset))
            fd.write('mod={}\n'.format(self._mod))
            fd.write('infile={}\n'.format(self._infile_name))
            for f in self._infiles_processed:
                fd.write('completed={}\n'.format(f))

    def _next_infile(self):
        if self._infile_name:
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

