""" test ModelResult for AUTOUGH2 """
from __future__ import division
from builtins import zip
from builtins import range
from past.utils import old_div

import unittest
import os, sys

import numpy as np

from credo.t2model import T2ModelResult

THIS_DIR = os.path.dirname(os.path.realpath(__file__))

class TestAUT2Model(unittest.TestCase):
    def setUp(self):
        # cc6 has eleme 1-80 as atmosphere blocks
        lstname = 'mres_aut2_cc6.listing'
        self.idxmap = list(range(80,1680))
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
        times, phist = self.mres.getFieldHistoryAtCell('Pressure', 1679)
        times, phist_map = self.mres_map.getFieldHistoryAtCell('Pressure', 1599)

        self.assertEqual(type(phist), np.ndarray)
        self.assertEqual(type(expected), np.ndarray)

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
            return old_div(mResult.getFieldAtOutputIndex('pressu', index), 1.0e5)

        def calc_p_hist_in_bar(mResult, index):
            t, phist = mResult.getFieldHistoryAtCell('pressu', index)
            return t, old_div(phist, 1.0e5)

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
        b_f = old_div(p_f, 1.0e5)
        self.assertEqual(mres.getFieldAtOutputIndex('pressu', -1)[30], p_f[30])
        self.assertEqual(mres.getFieldAtOutputIndex('p_in_bar', -1)[30], b_f[30])

        # test history
        ele = self.lst.element.row_name[30]
        ph_f = self.lst.history(('e', ele, 'Pressure'), short=False)[1]
        bh_f = old_div(ph_f, 1.0e5)
        t, phist = mres.getFieldHistoryAtCell('pressu', 30)
        self.assertEqual(phist[1], ph_f[1])
        t, phist = mres.getFieldHistoryAtCell('p_hist_in_bar', 30)
        self.assertEqual(phist[1], bh_f[1])

if __name__ == '__main__':
    unittest.main()
