import unittest
import os
import tempfile
import time
import configparser

import foozzer.mutators.fpl_basic

STATE_FILE = 'fpl_basic_state.txt'
INFILE_NAME = 'in.fpl'


class FPLBasicMutatorTests(unittest.TestCase):

    def setUp(self):
        self._working_dir = tempfile.TemporaryDirectory()
        self._indir = os.path.join(self._working_dir.name, 'in')
        self._outdir = os.path.join(self._working_dir.name, 'out')
        os.mkdir(self._indir)
        os.mkdir(self._outdir)

    def tearDown(self):
        self._working_dir.cleanup()

    def _read_state(self):
        sf = configparser.ConfigParser()
        sf.read(os.path.join(self._outdir, STATE_FILE))
        return sf

    def _create_trivial_infile(self):
        with open(os.path.join(self._indir, INFILE_NAME), 'w') as fd:
            fd.write('a')

    def _debug_show_working_dir(self):
        os.system('ls -R {}'.format(self._working_dir.name))
        os.system('cat {}'.format(os.path.join(self._indir, INFILE_NAME)))
        os.system('cat {}'.format(os.path.join(self._outdir, STATE_FILE)))

    def test_get_module_info(self):
        info = foozzer.mutators.fpl_basic.get_module_info()

        self.assertIn('fpl_basic', info.keys())
        self.assertEqual(info['fpl_basic'][0], 'BasicMutator Description')
        self.assertIs(info['fpl_basic'][1], foozzer.mutators.fpl_basic.FPLBasicMutator)

    def test_empty_in_dir(self):
        m = foozzer.mutators.fpl_basic.FPLBasicMutator(self._indir, self._outdir)
        with self.assertRaises(StopIteration):
            m.__next__()

    def test_single_infile(self):
        self._create_trivial_infile()
        m = foozzer.mutators.fpl_basic.FPLBasicMutator(self._indir, self._outdir)
        i = 0
        for x in m:
            i += 1
            sf = self._read_state()
            if i == 4:
                self.assertEqual(sf['DEFAULT'].getint('offset'), 1)
            else:
                self.assertEqual(sf['DEFAULT'].getint('offset'), 0)
            self.assertEqual(sf['DEFAULT'].getint('mod'), i%4)
            self.assertEqual(sf['DEFAULT']['infile'], INFILE_NAME)
            self.assertEqual(sf['DEFAULT']['completed'].split(sep='\n'), [''])

        self.assertEqual(i, 4)
        sf = self._read_state()
        self.assertEqual(sf['DEFAULT'].getint('offset'), 1)
        self.assertEqual(sf['DEFAULT'].getint('mod'), 0)
        self.assertEqual(sf['DEFAULT']['completed'].split(sep='\n'), ['', INFILE_NAME])

    def test_infile_already_processed(self):
        pass

    def test_offset_gt_file_size(self):
        pass

    def test_mod_gt_mod_count(self):
        pass

