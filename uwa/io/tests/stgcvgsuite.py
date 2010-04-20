import os
import cPickle as pickle
import shutil
import tempfile
import unittest

from uwa.io import stgcvg 
from uwa.io.stgcvg import CvgFileInfo

class StgCVGTestCase(unittest.TestCase):

    def setUp(self):
        self.basedir = os.path.realpath(tempfile.mkdtemp())
        #os.makedirs(os.path.join(self.basedir,self.results_dir,'StGermain'))
            #self.results_xml = open(os.path.join(self.basedir, self.results_dir, 'StGermain', 'TEST-FooSuite.xml'), 'w')

    def tearDown(self):
        shutil.rmtree(self.basedir)

    def test_genConvergenceFileIndex(self):
        #TODO: should write the actual test convergence files,
        # perhaps in set-up
        cvgInfoEmpty = stgcvg.genConvergenceFileIndex(".")
        self.assertEqual(cvgInfoEmpty, {})
        cvgInfo = stgcvg.genConvergenceFileIndex("./output")
        self.assertEqual(len(cvgInfo), 2)
        self.assertEqual(cvgInfo['TemperatureField'].filename, \
            './output/CosineHillRotate-analysis.cvg')
        self.assertEqual(cvgInfo['TemperatureField'].dofColMap, {0:1,1:2})
        self.assertEqual(cvgInfo['VelocityField'].filename, \
            './output/Analytic2-analysis.cvg')
        self.assertEqual(cvgInfo['VelocityField'].dofColMap, {0:1})

    def test_getCheckStepsRange(self):
        cvgFile = open("./output/CosineHillRotate-analysis.cvg","r")
        range = stgcvg.getCheckStepsRange(cvgFile,'all')
        self.assertEqual(range, [0,1,2])
        range = stgcvg.getCheckStepsRange(cvgFile,'last')
        self.assertEqual(range, [2])
        range = stgcvg.getCheckStepsRange(cvgFile,(0,1))
        self.assertEqual(range, [0])
        range = stgcvg.getCheckStepsRange(cvgFile,(0,2))
        self.assertEqual(range, [0,1])
        range = stgcvg.getCheckStepsRange(cvgFile,(0,3))
        self.assertEqual(range, [0,1,2])
        # check errors
        self.assertRaises(ValueError, stgcvg.getCheckStepsRange, cvgFile,(0,4))
        self.assertRaises(TypeError, stgcvg.getCheckStepsRange, cvgFile,(0,4.7))
        self.assertRaises(TypeError, stgcvg.getCheckStepsRange, cvgFile,'bana')

    def test_getDofErrors_ByDof(self):
        cvgFileInfo = CvgFileInfo("./output/CosineHillRotate-analysis.cvg")
        cvgFileInfo.dofColMap={0:1,1:2}
        dofErrors = stgcvg.getDofErrors_ByDof(cvgFileInfo, steps='last')
        self.assertEqual(len(dofErrors), 2)
        self.assertEqual(dofErrors[0], 0.00612235812)
        self.assertEqual(dofErrors[1], 0.053)

        dofErrorArray = stgcvg.getDofErrors_ByDof(cvgFileInfo, steps='all')
        self.assertEqual(len(dofErrorArray), 2)
        self.assertEqual(len(dofErrorArray[0]), 3)
        self.assertEqual(dofErrorArray[0][0], 0.00616)
        self.assertEqual(dofErrorArray[0][1], 0.00614)
        self.assertEqual(dofErrorArray[0][2], 0.00612235812)
        self.assertEqual(dofErrorArray[1][0], 0.055)
        self.assertEqual(dofErrorArray[1][1], 0.054)
        self.assertEqual(dofErrorArray[1][2], 0.053)

        dofErrorArray = stgcvg.getDofErrors_ByDof(cvgFileInfo, steps=(0,2))
        self.assertEqual(len(dofErrorArray), 2)
        self.assertEqual(len(dofErrorArray[0]), 2)
        self.assertEqual(dofErrorArray[0][0], 0.00616)
        self.assertEqual(dofErrorArray[0][1], 0.00614)
        self.assertEqual(dofErrorArray[1][0], 0.055)
        self.assertEqual(dofErrorArray[1][1], 0.054)


    def test_getDofErrors_ByTimestep(self):
        cvgFileInfo = CvgFileInfo("./output/CosineHillRotate-analysis.cvg")
        cvgFileInfo.dofColMap={0:1,1:2}
        dofErrors = stgcvg.getDofErrors_ByStep(cvgFileInfo, steps='last')
        self.assertEqual(len(dofErrors), 2)
        self.assertEqual(dofErrors[0], 0.00612235812)
        self.assertEqual(dofErrors[1], 0.053)

        dofErrorArray = stgcvg.getDofErrors_ByStep(cvgFileInfo, steps='all')
        self.assertEqual(len(dofErrorArray), 3)
        self.assertEqual(len(dofErrorArray[0]), 2)
        self.assertEqual(len(dofErrorArray[1]), 2)
        self.assertEqual(len(dofErrorArray[2]), 2)
        self.assertEqual(dofErrorArray[0][0], 0.00616)
        self.assertEqual(dofErrorArray[0][1], 0.055)
        self.assertEqual(dofErrorArray[1][0], 0.00614)
        self.assertEqual(dofErrorArray[1][1], 0.054)
        self.assertEqual(dofErrorArray[2][0], 0.00612235812)
        self.assertEqual(dofErrorArray[2][1], 0.053)

        dofErrorArray = stgcvg.getDofErrors_ByStep(cvgFileInfo, steps=(0,2))
        self.assertEqual(len(dofErrorArray), 2)
        self.assertEqual(len(dofErrorArray[0]), 2)
        self.assertEqual(len(dofErrorArray[1]), 2)
        self.assertEqual(dofErrorArray[0][0], 0.00616)
        self.assertEqual(dofErrorArray[0][1], 0.055)
        self.assertEqual(dofErrorArray[1][0], 0.00614)
        self.assertEqual(dofErrorArray[1][1], 0.054)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(StgCVGTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
