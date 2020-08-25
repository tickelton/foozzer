import unittest
import os
import tempfile

import foozzer.mutators.dry_run

INFILE_NAME = 'in.fpl'


class DryRunMutatorTests(unittest.TestCase):

    def setUp(self):
        self._working_dir = tempfile.TemporaryDirectory()
        self._indir = os.path.join(self._working_dir.name, 'in')
        self._outdir = os.path.join(self._working_dir.name, 'out')
        os.mkdir(self._indir)
        os.mkdir(self._outdir)

    def tearDown(self):
        self._working_dir.cleanup()

    def _create_infile_stub(self, size=1, name=INFILE_NAME):
        with open(os.path.join(self._indir, name), 'w') as fd:
            fd.write('a' * size)

    def _create_trivial_infile(self):
        self._create_infile_stub()

    def test_get_module_info(self):
        info = foozzer.mutators.dry_run.get_module_info()

        self.assertIn('dry_run', info.keys())
        self.assertIs(info['dry_run'][1], foozzer.mutators.dry_run.DryRunMutator)

    def test_trivial_infile(self):
        self._create_trivial_infile()
        m = foozzer.mutators.dry_run.DryRunMutator(self._indir, self._outdir)

        infile_data = None
        with open(os.path.join(self._indir, INFILE_NAME), 'r') as fd:
            infile_data = fd.read()

        i = 0
        for x in m:
            i += 1
            self.assertEqual(x[1], 'Dry Run')
            outfile_data = None
            with open(os.path.join(self._outdir, x[0]), 'r') as fd:
                outfile_data = fd.read()
            self.assertEqual(infile_data, outfile_data)

        self.assertEqual(i, 1)

