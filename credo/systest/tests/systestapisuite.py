##  Copyright (C), 2010, Monash University
##  Copyright (C), 2010, Victorian Partnership for Advanced Computing (VPAC)
##
##  This file is part of the CREDO library.
##  Developed as part of the Simulation, Analysis, Modelling program of
##  AuScope Limited, and funded by the Australian Federal Government's
##  National Collaborative Research Infrastructure Strategy (NCRIS) program.
##
##  This library is free software; you can redistribute it and/or
##  modify it under the terms of the GNU Lesser General Public
##  License as published by the Free Software Foundation; either
##  version 2.1 of the License, or (at your option) any later version.
##
##  This library is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
##  Lesser General Public License for more details.
##
##  You should have received a copy of the GNU Lesser General Public
##  License along with this library; if not, write to the Free Software
##  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
##  MA  02110-1301  USA

import unittest

from credo.systest.api import *

# TODO: more testing of the SysTest class itself

class SysTestResultTestCase(unittest.TestCase):
    def setUp(self):
        self.passMsg = "All fields passed."
        self.passResult = CREDO_PASS(self.passMsg)
        self.failMsg = "One of the fields outside tolerance."
        self.failResult = CREDO_FAIL(self.failMsg)
        self.errorMsg = "Model failed to run."
        self.errorResult = CREDO_ERROR(self.errorMsg)

    def test_printBasic(self):
        resStr = "%s" % self.passResult
        self.assertEqual(resStr, CREDO_PASS.statusStr)
        resStr = "%s" % self.failResult
        self.assertEqual(resStr, CREDO_FAIL.statusStr)
        resStr = "%s" % self.errorResult
        self.assertEqual(resStr, CREDO_ERROR.statusStr)

    def test_printDetailMsg(self):
        self.assertEqual(self.passResult.detailMsg, self.passMsg)
        self.assertEqual(self.failResult.detailMsg, self.failMsg)
        self.assertEqual(self.errorResult.detailMsg, self.errorMsg)

class SysTestNamesHandling(unittest.TestCase):
    def testGetStdTestName(self):
        self.assertRaises(TypeError, getStdTestName, "AnalyticTest",
            "Multigrid.xml", nproc=1)
        testNameSingle = getStdTestName("AnalyticTest", ["Multigrid.xml"],
            nproc=1, paramOverrides=None, solverOpts=None, nameSuffix=None)
        self.assertEqual(testNameSingle,
            "Multigrid-analyticTest-np1")
        testNameSubdir = getStdTestName("AnalyticTest", ["input/Multigrid.xml"],
            nproc=1, paramOverrides=None, solverOpts=None, nameSuffix=None)
        self.assertEqual(testNameSubdir,
            "Multigrid-analyticTest-np1")
        testNameMulti = getStdTestName("AnalyticTest",
            ["Multigrid.xml", "Blah.xml"],
            nproc=1, paramOverrides=None, solverOpts=None, nameSuffix=None)
        self.assertEqual(testNameMulti, testNameSingle)
        testNameOvers = getStdTestName("AnalyticTest",
            ["Multigrid.xml"],
            nproc=1, paramOverrides={"dim":3,"components.rheo.pert":45.6},
            solverOpts=None, nameSuffix=None)
        self.assertEqual(testNameOvers,
            "Multigrid-analyticTest-np1-pert-45_6-dim-3")
        testNameSuffix = getStdTestName("AnalyticTest",
            ["Multigrid.xml"],
            nproc=1, paramOverrides={"dim":3,"components.rheo.pert":45.6},
            solverOpts=None, nameSuffix="hipert")
        self.assertEqual(testNameSuffix,
            "Multigrid-analyticTest-np1-hipert")

def suite():
    testResultSuite = unittest.TestSuite()
    testResultSuite.addTest(unittest.makeSuite(SysTestResultTestCase, 'test'))
    nameSuite = unittest.TestSuite()
    nameSuite.addTest(unittest.makeSuite(SysTestNamesHandling))
    multiSuite = unittest.TestSuite((testResultSuite, nameSuite))
    return multiSuite

if __name__ == '__main__':
    unittest.main()
