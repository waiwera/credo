""" different ModelResults for different simulators """

import unittest
import os, sys

from credo.supermodel import SuperModelResult
from credo.t2model import T2ModelResult

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

class TestAUT2Model(unittest.TestCase):
    def setUp(self):
        # cc6 has eleme 1-80 as atmosphere blocks
        lstname = 'mres_aut2_cc6.listing'
        self.idxmap = range(80,1680)
        self.mres_map = T2ModelResult('test_aut2_map',
                                      lst_filename=lstname,
                                      indexMap=self.idxmap)
        self.mres = T2ModelResult('test_aut2_map',
                                  lst_filename=lstname,
                                  indexMap=None)
        from t2listing import t2listing
        self.lst = t2listing(lstname)

    def test_getfield(self):
        plst = self.lst.element['Pressure']
        pmap = self.mres_map.getFieldAtOutputIndex('Pressure', -1)
        pnom = self.mres.getFieldAtOutputIndex('Pressure', -1)

        self.assertEqual(len(plst), len(pnom))
        self.assertEqual(len(pmap), len(self.idxmap))

        self.assertEqual(list(pnom), list(plst))

        self.assertEqual(plst[80], pmap[0])
        self.assertEqual(plst[0], pnom[0])

        self.assertEqual(plst[-1], pmap[-1])
        self.assertEqual(plst[-1], pnom[-1])

if __name__ == '__main__':
    unittest.main()

