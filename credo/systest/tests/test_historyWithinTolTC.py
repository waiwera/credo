from __future__ import print_function
from builtins import zip
from builtins import range
import unittest

import unittest
import os, sys

import numpy

from credo.waiwera import WaiweraModelResult
from credo.t2model import T2ModelResult

from credo.systest import HistoryWithinTolTC

THIS_DIR = os.path.dirname(os.path.realpath(__file__))

class TestHistoryWithinTolTC(unittest.TestCase):
    def setUp(self):
        AUT2_FIELDMAP = {
            'Pressure': 'Pressure',
            'Temperature': 'Temperature',
            'Vapour saturation': 'Vapour saturation',
        }
        WAIWERA_FIELDMAP = {
            'Pressure': 'fluid_pressure',
            'Temperature': 'fluid_temperature',
            'Vapour saturation': 'fluid_vapour_saturation',
        }

        # these two sets all have 50 output times, made identical
        self.mres1 = WaiweraModelResult('waiwera',
                                      outputPath=THIS_DIR,
                                      h5_filename='deliv.h5',
                                      fieldname_map=WAIWERA_FIELDMAP)
        self.mres2 = T2ModelResult('aut2',
                                   lst_filename='deliv.listing',
                                   ordering_map=list(range(1,11)),
                                   fieldname_map=AUT2_FIELDMAP)

        # these two have different length of output results
        self.mres3 = WaiweraModelResult('waiwera',
                                      outputPath=THIS_DIR,
                                      h5_filename='deliv_38.h5',
                                      fieldname_map=WAIWERA_FIELDMAP)
        self.mres4 = T2ModelResult('aut2',
                                   lst_filename='deliv_39.listing',
                                   ordering_map=list(range(1,11)),
                                   fieldname_map=AUT2_FIELDMAP)

        print('waiwera n = ', len(self.mres3.getTimes()))
        print('aut2 n = ', len(self.mres4.getTimes()))

    def test_times_mechanism(self):
        # not specifying times should force interpolation onto expected times
        tc = HistoryWithinTolTC(fieldsToTest=["Temperature"],
                                defFieldTol=10.0,
                                fieldTols=None,
                                expected=self.mres3,
                                testCellIndex=4,
                                times=None
                                )
        status = tc.check(self.mres4)
        self.assertEqual(len(tc.times), len(self.mres3.getTimes()))

        # not specifying times should force interpolation onto expected times
        tc = HistoryWithinTolTC(fieldsToTest=["Temperature"],
                                defFieldTol=10.0,
                                fieldTols=None,
                                expected=self.mres4,
                                testCellIndex=4,
                                times=None
                                )
        status = tc.check(self.mres3)
        self.assertEqual(len(tc.times), len(self.mres4.getTimes()))

        # specifying times should force interpolation to suppliedtimes
        tc = HistoryWithinTolTC(fieldsToTest=["Temperature"],
                                defFieldTol=10.0,
                                fieldTols=None,
                                expected=self.mres4,
                                testCellIndex=4,
                                times=[0.0, 1.0, 2.0],
                                enforceLogic=False
                                )
        status = tc.check(self.mres3)
        self.assertEqual(len(tc.times), 3)

        # if compare to analtic solution, times will be set to result's
        def solution_fn(pos, t):
            """ dummy """
            return 100.0
        tc = HistoryWithinTolTC(fieldsToTest=["Temperature"],
                                defFieldTol=10.0,
                                fieldTols=None,
                                expected=solution_fn,
                                testCellIndex=4,
                                times=None
                                )
        status = tc.check(self.mres3)
        self.assertEqual(len(tc.times), len(self.mres3.getTimes()))


    def test_single_field(self):
        SHOW_PLOT = False

        def check_history(result, expected, field, tol, abs_err_tol=1.0):
            t1, p1 = result.getFieldHistoryAtCell(field, 4)
            t2, p2 = expected.getFieldHistoryAtCell(field, 4)
            tc = HistoryWithinTolTC(fieldsToTest=[field],
                                    defFieldTol=tol,
                                    fieldTols=None,
                                    expected=expected,
                                    absoluteErrorTol=abs_err_tol,
                                    testCellIndex=4,
                                    times=None
                                    )
            status = tc.check(result)

            if (not status) and SHOW_PLOT:
                from matplotlib import pyplot as plt
                plt.semilogx(t1,p1,'-r+',label=('result (%s)' % result.modelName))
                plt.semilogx(t2,p2,'--b*',label=('expected (%s)' % expected.modelName))
                plt.title('PASS = %s; %s; tol=%f' % (str(status), field, tol))
                plt.legend()
                plt.gca().relim()
                for i,(t,e) in enumerate(zip(tc.times,tc.fieldErrors[field])):
                    if e > tol:
                        plt.plot(t, p2[i], ' go', alpha=0.5, markersize=10)
                plt.show()

            return status

        self.assertEqual(check_history(self.mres1, self.mres2, "Temperature", 0.001), True)
        self.assertEqual(check_history(self.mres2, self.mres1, "Temperature", 0.001), True)

        self.assertEqual(check_history(self.mres1, self.mres2, "Pressure", 0.005), True)
        self.assertEqual(check_history(self.mres2, self.mres1, "Pressure", 0.005), True)

        # one of the pressure fails because aut2 results does not have result at
        # time zero hence interpolation cause the first pressure to be at time
        # 10000, already dropped from true start
        self.assertEqual(check_history(self.mres4, self.mres3, "Pressure", 0.005), False)

        self.assertEqual(check_history(self.mres1, self.mres2, "Vapour saturation", 0.0042), True)
        self.assertEqual(check_history(self.mres1, self.mres2, "Vapour saturation", 0.0041), False)

        self.assertEqual(check_history(self.mres2, self.mres1, "Vapour saturation", 0.0042), True)
        self.assertEqual(check_history(self.mres2, self.mres1, "Vapour saturation", 0.0041), False)

        # these would have a lot of trouble as the simulations have very different time stepping
        self.assertEqual(check_history(self.mres3, self.mres4, "Vapour saturation", 0.020), True)
        self.assertEqual(check_history(self.mres3, self.mres4, "Vapour saturation", 0.019), False)

        # these uses the old 1.0e-9 absolute error tolerance, so should behave as before
        self.assertEqual(check_history(self.mres1, self.mres2, "Vapour saturation", 0.028, 1.0e-9), True)
        self.assertEqual(check_history(self.mres1, self.mres2, "Vapour saturation", 0.027, 1.0e-9), False)


class TestCurveFitting(unittest.TestCase):
    def setUp(self):
        pass

    def test_non_dimensionalise(self):
        from credo.systest.singleRunWithinTolTC import non_dimensionalise
        x1, x2 = [1.0, 5.0, 3.0], [2.0, 11.0]
        xx1, xx2 = [0.0, 0.4, 0.2], [0.1, 1.0]
        self.assertEqual((xx1,xx2), non_dimensionalise(x1,x2))

        x1, x2 = [0.0, 0.001, 0.002], [0.0011, 0.0012]
        xx1, xx2 = [0.0, 0.001, 0.002], [0.0011, 0.0012]
        self.assertEqual((xx1,xx2), non_dimensionalise(x1,x2))

        x1, x2 = [999.0, 999.001, 999.002], [999.0011, 999.0012]
        xx1, xx2 = [0.0, 0.001, 0.002], [0.0011, 0.0012]
        xxx1, xxx2 = non_dimensionalise(x1,x2)
        for a,b in zip(xx1+xx2, xxx1+xxx2):
            self.assertAlmostEqual(a, b)

    def test_dist_errors(self):
        from credo.systest.singleRunWithinTolTC import calc_dist_errors
        # within a square of 2.0 x 2.0, dist "~" is 1.0, hence scalled to 0.5
        #   b
        #   |
        #   |~a
        #   |
        # b-b
        xa, ya = [2.0], [1.5]
        xb, yb = [0, 1, 1], [0, 0, 2]
        self.assertEqual([0.5], calc_dist_errors(xa, ya, xb, yb))


if __name__ == '__main__':
    unittest.main()
