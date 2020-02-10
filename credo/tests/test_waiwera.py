""" test ModelResult for Waiwera """

import unittest
import os, sys

import numpy as np

from credo.waiwera import WaiweraModelResult

THIS_DIR = os.path.dirname(os.path.realpath(__file__))

class TestWaiweraModelResult(unittest.TestCase):
    def setUp(self):
        self.mres = WaiweraModelResult('test_waiwera_MIS6',
                                       outputPath=THIS_DIR,
                                       h5_filename='problem6.h5',
                                       input_filename='problem6.json')

    def tearDown(self):
        pass

    def test_getfield(self):
        p = self.mres.getFieldAtOutputIndex('fluid_pressure', -1)
        self.assertEqual(len(p), 125)
        self.assertTrue(np.allclose(p[100], 1.26002e+07))

        p = self.mres.getFieldAtOutputIndex('fluid_pressure', 0)
        self.assertTrue(np.allclose(p[0], 3.98022e+06))

    def test_getposition(self):
        p = self.mres.getPositions()
        self.assertEqual(len(p), 125)

        expected = np.array([4500., 3600., -1500.])
        self.assertTrue(np.allclose(p[-1][:], expected))

    def test_gethistory(self):
        expected_t = np.array([0., 3.1540000e+07, 6.3080000e+07,
                               9.4620000e+07, 1.2616000e+08, 1.5770000e+08,
                               1.8924000e+08, 2.1560744e+08])

        expected_p = np.array([1.08546016e+07, 9.93034225e+06,
                               9.15027862e+06, 7.92924507e+06,
                               7.29322299e+06, 4.77191977e+06,
                               3.94400670e+06, 1.93398208e+03])
        
        t, p = self.mres.getFieldHistoryAtCell('fluid_pressure', 75)
        self.assertEqual(len(t), 142)
        self.assertTrue(np.allclose(t[::20], expected_t))
        self.assertTrue(np.allclose(p[::20], expected_p))

    def test_getothers(self):
        # other non h5 data, these can be easily checked in 'problem6.dat'
        v = self.mres.getFieldAtOutputIndex('geom_volume', 1234)
        self.assertListEqual(list(v[:100]), [2.4e8]*100)
        self.assertListEqual(list(v[100:125]), [4.8e8]*25)

        v = self.mres.getFieldAtOutputIndex('rock_porosity', 1234)
        self.assertListEqual(list(v[:25]), [0.2]*25) # rck 1
        self.assertListEqual(list(v[25:100]), [0.25]*75) # rck 2
        self.assertListEqual(list(v[100:]), [0.2]*25) # rck 1

        v = self.mres.getFieldAtOutputIndex('rock_permeability1', 1234)
        self.assertListEqual(list(v[:25]), [1.0e-13]*25) # rck 1
        self.assertListEqual(list(v[25:100]), [2.0e-13]*75) # rck 2
        self.assertListEqual(list(v[100:]), [1.0e-13]*25) # rck 1

if __name__ == '__main__':
    unittest.main()

