""" different ModelResults for different simulators """

import unittest
import os, sys

from credo.supermodel import SuperModelResult

THIS_DIR = os.path.dirname(os.path.realpath(__file__))

class TestSuperModel(unittest.TestCase):
    def setUp(self):
        self.mres = SuperModelResult('test_super',
                                outputPath=THIS_DIR,
                                h5_filename='mres_supermodel_1.h5')

    def tearDown(self):
        pass

    def test_getfield(self):
        p = self.mres.getFieldAtOutputIndex('fluid_pressure', -1)
        self.assertEqual(len(p), 1600)
        self.assertAlmostEqual(p[800], 1.0525784029355975E7, places=7)

        p = self.mres.getFieldAtOutputIndex('fluid_pressure', 0)
        self.assertEqual(p[0], 101350.0)

    def test_getposition(self):
        p = self.mres.getPositions()
        self.assertEqual(len(p), 1600)

        expected = [249.99999999999997, 249.99999999999997, -99.99999999999999]
        for i in range(3):
            self.assertAlmostEqual(p[800][i], expected[i], places=7)

if __name__ == '__main__':
    unittest.main()

