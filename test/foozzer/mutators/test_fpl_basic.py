import unittest
import os
import tempfile

import foozzer.mutators.fpl_basic

STATE_FILE = 'fpl_basic_state.txt'


class FPLBasicMutatorTests(unittest.TestCase):

    def setUp(self):
        self._working_dir = tempfile.TemporaryDirectory()
        self._indir = os.path.join(self._working_dir.name, 'in')
        self._outdir = os.path.join(self._working_dir.name, 'out')
        os.mkdir(self._indir)
        os.mkdir(self._outdir)

    def tearDown(self):
        self._working_dir.cleanup()

    def test_get_module_info(self):
        info = foozzer.mutators.fpl_basic.get_module_info()

        self.assertIn('fpl_basic', info.keys())
        self.assertEqual(info['fpl_basic'][0], 'BasicMutator Description')
        self.assertIs(info['fpl_basic'][1], foozzer.mutators.fpl_basic.FPLBasicMutator)

    def test_empty_in_dir(self):
        m = foozzer.mutators.fpl_basic.FPLBasicMutator(self._indir, self._outdir)
        with self.assertRaises(StopIteration):
            m.__next__()

    def test_infile_already_processed(self):
        pass

    def test_offset_gt_file_size(self):
        pass

    def test_mod_gt_mod_count(self):
        pass

