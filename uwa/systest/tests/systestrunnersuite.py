import os
import cPickle as pickle
import shutil
import tempfile
import unittest

from uwa.systest import SysTestRunner, SysTestSuite, UWA_PASS, UWA_FAIL, UWA_ERROR
from skeletonSysTest import SkeletonSysTest

class SysTestRunnerTestCase(unittest.TestCase):

    def setUp(self):
        self.basedir = os.path.realpath(tempfile.mkdtemp())
        self.stRunner = SysTestRunner()
        self.inputFiles = [os.path.join("input","TempDiffusion.xml")]

    def tearDown(self):
        self.stRunner = None
        shutil.rmtree(self.basedir)

    def test_runTest(self):
        skelTest = SkeletonSysTest(self.inputFiles, "output/SkeletonTest1",
            statusToReturn=UWA_PASS("testPass"), nproc=1)
        testResult = self.stRunner.runTest(skelTest)
        self.assertEqual(testResult.statusStr, UWA_PASS.statusStr)
        skelTest = SkeletonSysTest(self.inputFiles, "output/SkeletonTest2",
            statusToReturn=UWA_FAIL("testFail"), nproc=1)
        testResult = self.stRunner.runTest(skelTest)
        self.assertEqual(testResult.statusStr, UWA_FAIL.statusStr)
    
    def test_runSuite(self):
        skelTest1 = SkeletonSysTest(self.inputFiles, "output/SkeletonTest1",
            statusToReturn=UWA_PASS("testPass"), nproc=1)
        skelTest2 = SkeletonSysTest(self.inputFiles, "output/SkeletonTest2",
            statusToReturn=UWA_FAIL("testFail"), nproc=1)
        skelSuite = SysTestSuite("StgFEM", "RegressionTests", 
            sysTests=[skelTest1, skelTest2])
        testResults = self.stRunner.runSuite(skelSuite)
        self.assertEqual(len(testResults), 2)
        self.assertEqual(testResults[0].statusStr, UWA_PASS.statusStr)
        self.assertEqual(testResults[1].statusStr, UWA_FAIL.statusStr)

    def test_runTests(self):
        skelTest1 = SkeletonSysTest(self.inputFiles, "output/SkeletonTest1",
            statusToReturn=UWA_PASS("testPass"), nproc=1)
        skelTest2 = SkeletonSysTest(self.inputFiles, "output/SkeletonTest2",
            statusToReturn=UWA_FAIL("testFail"), nproc=1)
        sysTests = [skelTest1, skelTest2]
        testResults = self.stRunner.runTests(sysTests)
        self.assertEqual(len(testResults), 2)
        self.assertEqual(testResults[0].statusStr, UWA_PASS.statusStr)
        self.assertEqual(testResults[1].statusStr, UWA_FAIL.statusStr)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SysTestRunnerTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
