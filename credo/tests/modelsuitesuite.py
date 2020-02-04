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
import itertools

from credo.modelrun import ModelRun
from credo.modelsuite import ModelSuite, StgXMLVariant, JobParamVariant
import credo.modelsuite as msuite

# Skeleton classes
#class SkelModelRun(ModelRun):

class ModelSuiteTestCase(unittest.TestCase):

    def setUp(self):
        self.basedir = os.path.realpath(tempfile.mkdtemp())
        self.mRun1 = ModelRun("testRun1",["Input1.xml"],"./output/tr1")
        self.yRange = [-16000, -10000, -3000]
        self.zRange = [10000, 11000]
        self.procRange = [1, 2, 4, 8]
        self.stgI1 = StgXMLVariant("minY", self.yRange)
        self.stgI2 = StgXMLVariant("maxZ", self.zRange)
        self.jobI1 = JobParamVariant("nproc", self.procRange)
        self.varDict = {"Y":self.stgI1, "Z":self.stgI2}

    def tearDown(self):
        # TODO: tear down lxml document?
        shutil.rmtree(self.basedir)

    def test_variantGen(self):
        for paramI in range(self.stgI1.valLen()):
            self.stgI1.applyToModel(self.mRun1, paramI)
            self.assertEqual(self.mRun1.paramOverrides['minY'],
                self.yRange[paramI])

        for paramI in range(self.stgI2.valLen()):
            self.stgI2.applyToModel(self.mRun1, paramI)
            self.assertEqual(self.mRun1.paramOverrides['maxZ'],
                self.zRange[paramI])

        for paramI in range(self.jobI1.valLen()):
            self.jobI1.applyToModel(self.mRun1, paramI)
            self.assertEqual(self.mRun1.jobParams['nproc'],
                self.procRange[paramI])

    def test_getVariantParamPathDicts(self):
        indicesIt = msuite.getVariantIndicesIter(self.varDict, itertools.izip)
        varDicts = msuite.getVariantParamPathDicts(self.varDict, indicesIt)
        self.assertEqual(len(varDicts), min(
            map(len, [self.yRange, self.zRange])))
        for ii, varDict in enumerate(varDicts):
            self.assertEqual(varDict['minY'], self.yRange[ii])
            self.assertEqual(varDict['maxZ'], self.zRange[ii])

        indicesIt = msuite.getVariantIndicesIter(self.varDict,
            msuite.product)
        varDicts = msuite.getVariantParamPathDicts(self.varDict, indicesIt)
        self.assertEqual(len(varDicts), (len(self.yRange) * len(self.zRange)))
        # Loop through and check the product has worked.
        for ii in range(len(self.yRange)):
            for jj in range(len(self.zRange)):
                entryI = ii * len(self.zRange) + jj
                varDict = varDicts[entryI]
                self.assertEqual(varDict['minY'], self.yRange[ii])
                self.assertEqual(varDict['maxZ'], self.zRange[jj])

    def test_generateRuns_product(self):
        mSuite = ModelSuite(os.path.join("output","genSuiteTest"),
            templateMRun = self.mRun1)
        #TODO: since currently mVariants implemented as a dict, the order
        # these are added doesn't currently matter.
        mSuite.addVariant("depthVary", self.stgI1)
        mSuite.addVariant("ZVary", self.stgI2)
        mSuite.addVariant("scaleTests", self.jobI1)
        mSuite.generateRuns(msuite.product)
        self.assertEqual(len(mSuite.runs),
            len(self.yRange) * len(self.zRange) * len(self.procRange))
        # These are indices into lists above, created manually for testing
        # TODO: below is an experimentally-determined order - bad!
        expIndices = list(msuite.product(
            range(len(self.procRange)),
            range(len(self.yRange)),
            range(len(self.zRange))
            ))
        for ii, expIndexTuple in enumerate(expIndices):
            pIndex, yIndex, zIndex = expIndexTuple
            self.assertEqual(mSuite.runs[ii].paramOverrides['minY'],
                self.yRange[yIndex])
            self.assertEqual(mSuite.runs[ii].paramOverrides['maxZ'],
                self.zRange[zIndex])
            self.assertEqual(mSuite.runs[ii].jobParams['nproc'],
                self.procRange[pIndex])
            self.assertEqual(mSuite.runs[ii].outputPath,
                os.path.join("output", "genSuiteTest",
                    mSuite.subOutputPathGenFunc(mSuite.runs[ii],
                        mSuite.modelVariants, expIndexTuple, ii)))
        # Now test regenerating produces correct length again
        mSuite.generateRuns()
        self.assertEqual(len(mSuite.runs),
            len(self.yRange) * len(self.zRange) * len(self.procRange))

    def test_generateRuns_izip(self):
        mSuite = ModelSuite(os.path.join("output","genSuiteTest"),
            templateMRun = self.mRun1)
        mSuite.addVariant("depthVary", self.stgI1)
        mSuite.addVariant("ZVary", self.stgI2)
        mSuite.generateRuns(itertools.izip)
        self.assertEqual(len(mSuite.runs),
            min(len(self.yRange), len(self.zRange)))
        # These are indices into lists above, created manually for testing
        expIndices = [(0,0),(1,1)]
        for ii, expIndexTuple in enumerate(expIndices):
            yIndex, zIndex = expIndexTuple
            self.assertEqual(mSuite.runs[ii].paramOverrides['minY'],
                self.yRange[yIndex])
            self.assertEqual(mSuite.runs[ii].paramOverrides['maxZ'],
                self.zRange[zIndex])
            self.assertEqual(mSuite.runs[ii].outputPath,
                os.path.join("output", "genSuiteTest",
                    mSuite.subOutputPathGenFunc(mSuite.runs[ii],
                    mSuite.modelVariants, expIndexTuple, ii)))

    def test_generateRuns_customSubdirs(self):
        mSuite = ModelSuite(os.path.join("output","genSuiteTest"),
            templateMRun = self.mRun1)
        mSuite.addVariant("depthVary", self.stgI1)
        mSuite.addVariant("ZVary", self.stgI2)

        mSuite.subOutputPathGenFunc = msuite.getSubdir_RunIndex
        mSuite.generateRuns(itertools.izip)
        self.assertEqual(len(mSuite.runs),
            min(len(self.yRange), len(self.zRange)))
        for runI in range(len(mSuite.runs)):
            # This should just be a very simple output path based on
            #  run index
            self.assertEqual(mSuite.runs[runI].outputPath,
                os.path.join("output", "genSuiteTest",
                    msuite.getSubdir_RunIndex(None, None, None, runI)))

        mSuite.subOutputPathGenFunc = msuite.getSubdir_TextParamVals
        mSuite.generateRuns(itertools.izip)
        expIndices = [(0,0),(1,1)]
        for runI, expIndexTuple in enumerate(expIndices):
            self.assertEqual(mSuite.runs[runI].outputPath,
                os.path.join("output", "genSuiteTest",
                    msuite.getSubdir_TextParamVals(mSuite.runs[runI],
                    mSuite.modelVariants, expIndexTuple, runI)))

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ModelSuiteTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
