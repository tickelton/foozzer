import unittest
import os
import tempfile
import time
import configparser

import foozzer.mutators.fpl_basic

STATE_FILE = 'fpl_basic_state.txt'
INFILE_NAME = 'in.fpl'
INFILE2_NAME = 'in2.fpl'


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

    def test_get_module_info(self):
        info = foozzer.mutators.fpl_basic.get_module_info()

        self.assertIn('fpl_basic', info.keys())
        self.assertEqual(info['fpl_basic'][0], 'BasicMutator Description')
        self.assertIs(info['fpl_basic'][1], foozzer.mutators.fpl_basic.FPLBasicMutator)

    def test_empty_in_dir(self):
        m = foozzer.mutators.fpl_basic.FPLBasicMutator(self._indir, self._outdir)
        with self.assertRaises(StopIteration):
            m.__next__()

    def test_trivial_infile(self):
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
        self._create_trivial_infile()
        self._write_state({
            'offset': 0,
            'mod': 0,
            'infile': INFILE_NAME,
            'completed': '\n'.join(['', INFILE_NAME])
        })

        m = foozzer.mutators.fpl_basic.FPLBasicMutator(self._indir, self._outdir)
        i = 0
        for x in m:
            i += 1
        self.assertEqual(i, 0)
        sf = self._read_state()
        self.assertEqual(sf['DEFAULT'].getint('offset'), 0)
        self.assertEqual(sf['DEFAULT'].getint('mod'), 0)
        self.assertEqual(sf['DEFAULT']['completed'].split(sep='\n'), ['', INFILE_NAME])

    def test_offset_gt_file_size(self):
        self._create_trivial_infile()
        self._write_state({
            'offset': 10,
            'mod': 0,
            'infile': INFILE_NAME,
            'completed': ''
        })

        m = foozzer.mutators.fpl_basic.FPLBasicMutator(self._indir, self._outdir)
        i = 0
        for x in m:
            i += 1
        self.assertEqual(i, 0)
        sf = self._read_state()
        self.assertEqual(sf['DEFAULT'].getint('offset'), 10)
        self.assertEqual(sf['DEFAULT'].getint('mod'), 0)
        self.assertEqual(sf['DEFAULT']['completed'].split(sep='\n'), ['', INFILE_NAME])

    def test_mod_gt_mod_count(self):
        self._create_trivial_infile()
        self._write_state({
            'offset': 0,
            'mod': 10,
            'infile': INFILE_NAME,
            'completed': ''
        })

        with self.assertRaises(ValueError):
            m = foozzer.mutators.fpl_basic.FPLBasicMutator(self._indir, self._outdir)

    def test_two_infiles(self):
        self._create_trivial_infile()
        self._create_infile_stub(1, INFILE2_NAME)
        m = foozzer.mutators.fpl_basic.FPLBasicMutator(self._indir, self._outdir)
        i = 0
        for x in m:
            i += 1
            sf = self._read_state()
            if i % 4 == 0:
                self.assertEqual(sf['DEFAULT'].getint('offset'), 1)
            else:
                self.assertEqual(sf['DEFAULT'].getint('offset'), 0)
            self.assertEqual(sf['DEFAULT'].getint('mod'), i%4)
            # NOTE: Too implementation specific ?
            #       Processing order might change.
            if i < 5:
                self.assertEqual(sf['DEFAULT']['infile'], INFILE2_NAME)
                self.assertEqual(sf['DEFAULT']['completed'].split(sep='\n'), [''])
            else:
                self.assertEqual(sf['DEFAULT']['infile'], INFILE_NAME)
                self.assertEqual(sf['DEFAULT']['completed'].split(sep='\n'), ['', INFILE2_NAME])

        self.assertEqual(i, 8)
        sf = self._read_state()
        self.assertEqual(sf['DEFAULT'].getint('offset'), 1)
        self.assertEqual(sf['DEFAULT'].getint('mod'), 0)
        # NOTE: Order does not really matter here.
        #       Maybe this should be two calls to assertIn() ?
        self.assertEqual(sf['DEFAULT']['completed'].split(sep='\n'), ['', INFILE2_NAME, INFILE_NAME])

# TODO: test empty file
#       test iterator return value !
