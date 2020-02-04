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
import shutil
import tempfile
import unittest

from credo.systest.api import CREDO_PASS, CREDO_FAIL, CREDO_ERROR
from credo.systest.systestsuite import SysTestSuite
from skeletonSysTest import SkeletonSingleModelSysTest

class SysTestSuiteTestCase(unittest.TestCase):

    def setUp(self):
        self.basedir = os.path.realpath(tempfile.mkdtemp())
        self.stSuite = SysTestSuite("StgFEM", "RegressionTests")
        self.inputFiles = [os.path.join("input","TempDiffusion.xml")]

    def tearDown(self):
        self.stSuite = None
        shutil.rmtree(self.basedir)

    def test_addStdTest(self):
        self.stSuite.addStdTest(SkeletonSingleModelSysTest, self.inputFiles,
            statusToReturn=CREDO_PASS("testPass"), nproc=1)
        sysTestsList = self.stSuite.sysTests
        self.assertEqual(len(self.stSuite.sysTests), 1)
        addedTest = sysTestsList[0]
        self.assertTrue(isinstance(addedTest, SkeletonSingleModelSysTest))
        self.assertEqual(addedTest.testType, "SkeletonSingleModelSysTest")
        self.assertEqual(addedTest.inputFiles, self.inputFiles)
        self.assertEqual(addedTest.testStatus, None)
        self.stSuite.addStdTest(SkeletonSingleModelSysTest, self.inputFiles,
            statusToReturn=CREDO_FAIL("testFail"), nproc=1)
        self.assertEqual(len(self.stSuite.sysTests), 2)
        secondTest = sysTestsList[1]
        self.assertTrue(isinstance(addedTest, SkeletonSingleModelSysTest))
        self.assertEqual(addedTest.testType, "SkeletonSingleModelSysTest")
        self.assertEqual(addedTest.inputFiles, self.inputFiles)
        self.assertEqual(addedTest.testStatus, None)

    def test_addSubSuite(self):
        subSuite1 = SysTestSuite("StgFEM", "RegressionTests-sub1")
        subSuite2 = SysTestSuite("StgFEM", "RegressionTests-sub2")
        self.stSuite.addSubSuite(subSuite1)
        self.stSuite.addSubSuite(subSuite2)
        self.assertEqual(len(self.stSuite.subSuites), 2)
        self.assertEqual(self.stSuite.subSuites[0], subSuite1)
        self.assertEqual(self.stSuite.subSuites[1], subSuite2)
        #Make sure don't get list confused etc
        self.assertRaises(TypeError, self.stSuite.addSubSuite,
            [subSuite1, subSuite2])

    def test_newSubSuite(self):
        subSuite1 = self.stSuite.newSubSuite("StgFEM", "RegressionTests-sub1")
        subSuite2 = self.stSuite.newSubSuite("StgFEM", "RegressionTests-sub2")
        self.assertEqual(len(self.stSuite.subSuites), 2)
        self.assertEqual(self.stSuite.subSuites[0], subSuite1)
        self.assertEqual(self.stSuite.subSuites[1], subSuite2)
        self.assertTrue(isinstance(self.stSuite.subSuites[0], SysTestSuite))
        self.assertTrue(isinstance(self.stSuite.subSuites[1], SysTestSuite))

    def test_addSubSuites(self):
        subSuite1 = SysTestSuite("StgFEM", "RegressionTests-sub1")
        subSuite2 = SysTestSuite("StgFEM", "RegressionTests-sub2")
        self.stSuite.addSubSuites([subSuite1, subSuite2])
        self.assertEqual(len(self.stSuite.subSuites), 2)
        self.assertEqual(self.stSuite.subSuites[0], subSuite1)
        self.assertEqual(self.stSuite.subSuites[1], subSuite2)
        # Now try add some tests to these suites
        self.stSuite.addStdTest(SkeletonSingleModelSysTest, self.inputFiles,
            statusToReturn=CREDO_FAIL("testFail"), nproc=1)
        subSuite2.addStdTest(SkeletonSingleModelSysTest, self.inputFiles,
            statusToReturn=CREDO_PASS("testPass"), nproc=1)
        self.assertEqual(len(self.stSuite.sysTests), 1)
        self.assertEqual(len(self.stSuite.subSuites[0].sysTests), 0)
        self.assertEqual(len(self.stSuite.subSuites[1].sysTests), 1)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SysTestSuiteTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
