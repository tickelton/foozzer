import unittest
import os
import tempfile
import time
import configparser

import foozzer.mutators.bitflip

STATE_FILE = 'bitflip_state.txt'
INFILE_NAME = 'in.txt'
INFILE2_NAME = 'in2.txt'


class BitflipMutatorTests(unittest.TestCase):

    def setUp(self):
        self._working_dir = tempfile.TemporaryDirectory()
        self._indir = os.path.join(self._working_dir.name, 'in')
        self._outdir = os.path.join(self._working_dir.name, 'out')
        os.mkdir(self._indir)
        os.mkdir(self._outdir)

    def tearDown(self):
        self._working_dir.cleanup()

    def _read_state(self):
        sg = configparser.ConfigParser()
        sg.read(os.path.join(self._outdir, STATE_FILE))
        return sg

    def _write_state(self, data):
        config = configparser.ConfigParser()

        config['DEFAULT'] = data

        with open(os.path.join(self._outdir, STATE_FILE), 'w') as sh:
            config.write(sh)

    def _create_infile_stub(self, size=1, name=INFILE_NAME):
        with open(os.path.join(self._indir, name), 'w') as fd:
            fd.write('a' * size)

    def _create_trivial_infile(self):
        self._create_infile_stub()

    def _debug_show_working_dir(self):
        os.system('ls -R {}'.format(self._working_dir.name))
        print('')
        os.system('cat {}'.format(os.path.join(self._indir, INFILE_NAME)))
        print('')
        os.system('cat {}'.format(os.path.join(self._outdir, STATE_FILE)))
        print('')

    def _debug_show_outfile(self):
        print('xx')
        os.system('cat {}'.format(os.path.join(self._outdir, foozzer.mutators.bitflip.OUTFILE_NAME)))
        print('xx')

    def test_get_module_info(self):
        info = foozzer.mutators.bitflip.get_module_info()

        self.assertIn('bitflip', info.keys())
        self.assertEqual(info['bitflip'][0], 'Flips individual bits in the input file')
        self.assertIs(info['bitflip'][1], foozzer.mutators.bitflip.BitflipMutator)

    def test_empty_in_dir(self):
        m = foozzer.mutators.bitflip.BitflipMutator(self._indir, self._outdir)
        with self.assertRaises(StopIteration):
            m.__next__()

    def test_trivial_infile(self):
        self._create_trivial_infile()
        m = foozzer.mutators.bitflip.BitflipMutator(self._indir, self._outdir)
        i = 0
        for x in m:
            self.assertEqual(x[0], 'bitflip.out')
            self.assertEqual(x[1], 'infile={} offset=0, mod={}'.format(INFILE_NAME, i))
            i += 1
            sf = self._read_state()
            if i == 8:
                self.assertEqual(sf['DEFAULT'].getint('offset'), 1)
            else:
                self.assertEqual(sf['DEFAULT'].getint('offset'), 0)
            self.assertEqual(sf['DEFAULT'].getint('mod'), i%8)
            self.assertEqual(sf['DEFAULT']['infile'], INFILE_NAME)
            self.assertEqual(sf['DEFAULT']['completed'].split(sep='\n'), [''])

        self.assertEqual(i, 8)
        sf = self._read_state()
        self.assertEqual(sf['DEFAULT'].getint('offset'), 1)
        self.assertEqual(sf['DEFAULT'].getint('mod'), 0)
        self.assertEqual(sf['DEFAULT']['completed'].split(sep='\n'), ['', INFILE_NAME])

