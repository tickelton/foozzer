import unittest

import foozzer.mutators.fpl_basic

class FPLBasicMutatorTests(unittest.TestCase):

    def test_get_module_info(self):
        info = foozzer.mutators.fpl_basic.get_module_info()

        self.assertIn('fpl_basic', info.keys())
        self.assertEqual(info['fpl_basic'][0], 'BasicMutator Description')
        self.assertIs(info['fpl_basic'][1], foozzer.mutators.fpl_basic.FPLBasicMutator)
