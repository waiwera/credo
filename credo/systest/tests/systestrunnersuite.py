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

import os
import cPickle as pickle
import shutil
import tempfile
import unittest

from credo.systest import SysTestRunner, SysTestSuite, CREDO_PASS, CREDO_FAIL, CREDO_ERROR
from skeletonSysTest import SkeletonSysTest

class SysTestRunnerTestCase(unittest.TestCase):

    def setUp(self):
        self.basedir = os.path.realpath(tempfile.mkdtemp())
        self.stRunner = SysTestRunner()
        self.inputFiles = [os.path.join("input","TempDiffusion.xml")]
        self.skelTest1 = SkeletonSysTest("skelTest1",
            "output/SkeletonTest1",
            statusToReturn=CREDO_PASS("testPass"), nproc=1)
        self.skelTest2 = SkeletonSysTest("skelTest2",
            "output/SkeletonTest2",
            statusToReturn=CREDO_FAIL("testFail"), nproc=1)
        self.skelTest3 = SkeletonSysTest("skelTest3",
            "output/SkeletonTest3",
            statusToReturn=CREDO_ERROR("testError"), nproc=1)
        self.skelTest4 = SkeletonSysTest("skelTest4",
            "output/SkeletonTest4",
            statusToReturn=CREDO_PASS("testPass2"), nproc=1)
        for skelTest in [self.skelTest1, self.skelTest2, self.skelTest3,
                self.skelTest4]:
            skelTest.runPath = os.path.abspath(os.getcwd())

    def tearDown(self):
        self.stRunner = None
        shutil.rmtree(self.basedir)

    def test_runTests(self):
        sysTests = [self.skelTest1, self.skelTest2]
        testResults = self.stRunner.runTests(sysTests)
        self.assertEqual(len(testResults), 2)
        self.assertEqual(testResults[0].statusStr, CREDO_PASS.statusStr)
        self.assertEqual(testResults[1].statusStr, CREDO_FAIL.statusStr)

    def test_runSuite(self):
        skelSuite = SysTestSuite("StgFEM", "RegressionTests",
            sysTests=[self.skelTest1, self.skelTest2])
        testResults = self.stRunner.runSuite(skelSuite,
            outputSummaryDir="output/testRunSuite")
        self.assertEqual(len(testResults), 2)
        self.assertEqual(testResults[0].statusStr, CREDO_PASS.statusStr)
        self.assertEqual(testResults[1].statusStr, CREDO_FAIL.statusStr)

    def test_runSuite_withSubs(self):
        skelSuite = SysTestSuite("StgFEM", "RegressionTests",
            sysTests=[self.skelTest1, self.skelTest2])
        subSuite = SysTestSuite("StgFEM", "RegressionTests-sub")
        skelSuite.addSubSuite(subSuite)
        subSuite.sysTests.append(self.skelTest3)
        testResults = self.stRunner.runSuite(skelSuite,
            outputSummaryDir="output/testRunSuite_withSubs")
        self.assertEqual(len(testResults), 3)
        self.assertEqual(testResults[0].statusStr, CREDO_PASS.statusStr)
        self.assertEqual(testResults[1].statusStr, CREDO_FAIL.statusStr)
        self.assertEqual(testResults[2].statusStr, CREDO_ERROR.statusStr)

    def test_runSuite_subOnly(self):
        subSuite1 = SysTestSuite("StgFEM", "RegressionTests-sub1",
            sysTests=[self.skelTest1, self.skelTest2])
        subSuite2 = SysTestSuite("StgFEM", "RegressionTests-sub2",
            sysTests=[self.skelTest2, self.skelTest3])
        masterSuite = SysTestSuite("StgFEM", "RegressionTests",
            subSuites=[subSuite1, subSuite2])
        testResults = self.stRunner.runSuite(masterSuite,
            outputSummaryDir="output/testRunSuite_subOnly")
        self.assertEqual(len(testResults), 4)
        self.assertEqual(testResults[0].statusStr, CREDO_PASS.statusStr)
        self.assertEqual(testResults[1].statusStr, CREDO_FAIL.statusStr)
        self.assertEqual(testResults[2].statusStr, CREDO_FAIL.statusStr)
        self.assertEqual(testResults[3].statusStr, CREDO_ERROR.statusStr)

    def test_runSuites(self):
        suite1 = SysTestSuite("StgFEM", "RegressionTests",
            sysTests=[self.skelTest1, self.skelTest2])
        subSuite = SysTestSuite("StgFEM", "RegressionTests-sub")
        suite1.addSubSuite(subSuite)
        subSuite.sysTests.append(self.skelTest3)
        suite2 = SysTestSuite("StgFEM", "PerformanceTests",
            sysTests=[self.skelTest4])
        suite3 = SysTestSuite("PICellerator", "RegressionTests",
            sysTests=[self.skelTest2, self.skelTest4])
        testResults = self.stRunner.runSuites([suite1, suite2, suite3],
            outputSummaryDir="output/testRunSuites")

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SysTestRunnerTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
