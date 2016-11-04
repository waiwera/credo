""" different ModelResults for different simulators """

import unittest
import os, sys

import numpy

from credo.waiwera import WaiweraModelResult
from credo.t2model import T2ModelResult

THIS_DIR = os.path.dirname(os.path.realpath(__file__))

class TestWaiweraModelResult(unittest.TestCase):
    def setUp(self):
        self.mres = WaiweraModelResult('test_super',
                                outputPath=THIS_DIR,
                                h5_filename='mres_waiwera_1.h5')

        self.mres2 = WaiweraModelResult('test_waiwera_2',
                                outputPath=THIS_DIR,
                                h5_filename='problem6.h5',
                                input_filename='problem6.json')

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

    def test_gethistory(self):
        expected = [101350.0, 1.0525784029355975E7]
        expected_times = [0.0, 1.0E15]

        phist = self.mres.getFieldHistoryAtCell('fluid_pressure', 800)
        for p,pe in zip(phist, expected):
            self.assertAlmostEqual(p, pe, places=7)

        times = self.mres.getTimes()
        for t,te in zip(times, expected_times):
            self.assertAlmostEqual(t, te, places=7)

    def test_getothers(self):
        # other non h5 data, these can be easily checked in 'problem6.dat'
        v = self.mres2.getFieldAtOutputIndex('geom_volume', 1234)
        self.assertListEqual(list(v[:100]), [2.4e8]*100)
        self.assertListEqual(list(v[100:125]), [4.8e8]*25)

        v = self.mres2.getFieldAtOutputIndex('rock_porosity', 1234)
        self.assertListEqual(list(v[:25]), [0.2]*25) # rck 1
        self.assertListEqual(list(v[25:100]), [0.25]*75) # rck 2
        self.assertListEqual(list(v[100:]), [0.2]*25) # rck 1

        v = self.mres2.getFieldAtOutputIndex('rock_permeability1', 1234)
        self.assertListEqual(list(v[:25]), [1.0e-13]*25) # rck 1
        self.assertListEqual(list(v[25:100]), [2.0e-13]*75) # rck 2
        self.assertListEqual(list(v[100:]), [1.0e-13]*25) # rck 1


class TestAUT2Model(unittest.TestCase):
    def setUp(self):
        # cc6 has eleme 1-80 as atmosphere blocks
        lstname = 'mres_aut2_cc6.listing'
        self.idxmap = range(80,1680)
        self.mres_map = T2ModelResult('test_aut2_map',
                                      lst_filename=lstname,
                                      ordering_map=self.idxmap)
        self.mres = T2ModelResult('test_aut2_map',
                                  lst_filename=lstname,
                                  ordering_map=None)
        from t2listing import t2listing
        self.lst = t2listing(lstname)

        ### mResult with data file
        datname = 'mdat_fivespot.dat'
        self.mres_w_dat = T2ModelResult('test_aut2_map',
                                        lst_filename=lstname,
                                        dat_filename=datname,
                                        ordering_map=None)
        from t2data import t2data
        self.dat = t2data(datname)

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

        porosity5 = self.dat.grid.blocklist[5].rocktype.porosity
        porosity_mres = self.mres_w_dat.getFieldAtOutputIndex('rock_porosity', 1234)
        self.assertEqual(len(porosity_mres), self.dat.grid.num_blocks)
        self.assertEqual(porosity5, porosity_mres[5])

        volume6 = self.dat.grid.blocklist[6].volume
        volume_mres = self.mres_w_dat.getFieldAtOutputIndex('geom_volume', 5678)
        self.assertEqual(len(volume_mres), self.dat.grid.num_blocks)
        self.assertEqual(volume6, volume_mres[6])

    def test_gethistory(self):
        ele = self.lst.element.row_name[-1]
        expected_times, expected = self.lst.history(('e', ele, 'Pressure'))
        phist = self.mres.getFieldHistoryAtCell('Pressure', 1679)
        phist_map = self.mres_map.getFieldHistoryAtCell('Pressure', 1599)
        times = self.mres.getTimes()

        self.assertEqual(type(phist), numpy.ndarray)
        self.assertEqual(type(expected), numpy.ndarray)

        for p,pmap,pe in zip(phist, phist_map, expected):
            self.assertEqual(p, pe)
            self.assertEqual(pmap, pe)

        for t,te in zip(times, expected_times):
            self.assertEqual(t, te)

class TestCustomField(unittest.TestCase):
    def setUp(self):
        self.lstname = 'mres_aut2_fivespot.listing'
        from t2listing import t2listing
        self.lst = t2listing(self.lstname)

    def test_simple(self):
        """ Tests basic custom variable usage.  Incls values at all cells and
        history of a single cell.
        """
        # example of ustom variable function, first argument is always
        # ModelResult object, the second is an integer index.
        def calc_p_in_bar(mResult, index):
            """ Implement this func to calculate customised variable.

            Within this function, users should try to use only the public
            methods of ModelResult, such as .getFieldAtOutputIndex() and
            .getFieldHistoryAtCell().  Also the names of fields should be the
            keys specified in field_map.  This would allow the function to be
            used in (almost) all ModelResults.
            """
            return mResult.getFieldAtOutputIndex('pressu', index) / 1.0e5

        def calc_p_hist_in_bar(mResult, index):
            return mResult.getFieldHistoryAtCell('pressu', index) / 1.0e5

        # then pass the function into the ModelResult (or ModelRun) as part of
        # the field name map
        field_map = {
            'pressu': 'Pressure',
            'p_in_bar': calc_p_in_bar,
            'p_hist_in_bar': calc_p_hist_in_bar,
        }
        mres = T2ModelResult('test_aut2_map',
                             lst_filename=self.lstname,
                             fieldname_map=field_map,
                             )

        # test final result table
        self.lst.index = -1
        p_f = self.lst.element['Pressure']
        b_f = p_f / 1.0e5
        self.assertEqual(mres.getFieldAtOutputIndex('pressu', -1)[30], p_f[30])
        self.assertEqual(mres.getFieldAtOutputIndex('p_in_bar', -1)[30], b_f[30])

        # test history
        ele = self.lst.element.row_name[30]
        ph_f = self.lst.history(('e', ele, 'Pressure'), short=False)[1]
        bh_f = ph_f / 1.0e5
        self.assertEqual(mres.getFieldHistoryAtCell('pressu', 30)[1], ph_f[1])
        self.assertEqual(mres.getFieldHistoryAtCell('p_hist_in_bar', 30)[1], bh_f[1])


if __name__ == '__main__':
    unittest.main()

