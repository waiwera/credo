import unittest

import unittest
import os, sys

import numpy

from credo.supermodel import SuperModelResult
from credo.t2model import T2ModelResult

from credo.systest import HistoryWithinTolTC

THIS_DIR = os.path.dirname(os.path.realpath(__file__))

class TestHistoryWithinTolTC(unittest.TestCase):
    def setUp(self):
        AUT2_FIELDMAP = {
            'Vapour saturation': 'Vapour saturation',
        }
        SUPER_FIELDMAP = {
            'Vapour saturation': 'fluid_vapour_saturation',
        }

        self.mres1 = SuperModelResult('test_waiwera',
                                      outputPath=THIS_DIR,
                                      h5_filename='deliv.h5',
                                      fieldname_map=SUPER_FIELDMAP)
        self.mres2 = T2ModelResult('test_aut2',
                                   lst_filename='deliv.listing',
                                   ordering_map=range(1,11),
                                   fieldname_map=AUT2_FIELDMAP)

    def test_a(self):
        p1 = self.mres1.getFieldHistoryAtCell('Vapour saturation', 4)
        t1 = self.mres1.getTimes()
        p2 = self.mres2.getFieldHistoryAtCell('Vapour saturation', 4)
        t2 = self.mres2.getTimes()

        tc_a = HistoryWithinTolTC(fieldsToTest=["Vapour saturation"],
                                defFieldTol=0.01,
                                fieldTols=None,
                                expected=self.mres2,
                                testCellIndex=4,
                                times=None
                                )
        print tc_a.check(self.mres1)

        tc_b = HistoryWithinTolTC(fieldsToTest=["Vapour saturation"],
                                defFieldTol=0.01,
                                fieldTols=None,
                                expected=self.mres1,
                                testCellIndex=4,
                                times=None
                                )
        print tc_b.check(self.mres2)

        from matplotlib import pyplot as plt
        plt.semilogx(t1,p1,'-r+',t2,p2,'--b*')
        plt.show()


if __name__ == '__main__':
    unittest.main()
