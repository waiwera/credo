from __future__ import division
from builtins import range
from past.utils import old_div
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

from credo.io.stgfreq import FreqOutput
import credo.io.stgfreq as stgfreq

class StgFreqTestCase(unittest.TestCase):
    def setUp(self):
        self.basedir = os.path.realpath(tempfile.mkdtemp())
        self.stgFreq = FreqOutput("./sampleData")
        self.tSteps = [3, 6, 9, 12, 15]
        self.timeVals = [0.0125, 0.0375, 0.0625, 0.0875, 0.1125]
        self.VRMSVals = [3, 3.2, 3.8, 3.4, 2.6]

    def tearDown(self):
        shutil.rmtree(self.basedir)

    def test_getHeaders(self):
        headers = self.stgFreq.getHeaders()
        self.assertEqual(headers, ['Timestep','Time','VRMS'])
        self.assertEqual(self.stgFreq.headerColMap, {'Timestep':0, 'Time':1,
            'VRMS':2})

    def test_getAllRecords(self):
        records = self.stgFreq.getAllRecords()
        for ii in range(0,5):
            self.assertEqual(records[ii][0], self.tSteps[ii])
            self.assertAlmostEqual(records[ii][1], self.timeVals[ii])
            self.assertAlmostEqual(records[ii][2], self.VRMSVals[ii])

    def test_getValueAtStep(self):
        self.stgFreq.populateFromFile()
        tI = 2
        tStep = self.tSteps[tI]
        time4 = self.stgFreq.getValueAtStep("Time", tStep)
        self.assertAlmostEqual(time4, self.timeVals[tI])
        VRMS2 = self.stgFreq.getValueAtStep("VRMS", tStep)
        self.assertAlmostEqual(VRMS2, self.VRMSVals[tI])

    def test_getRecordDictAtStep(self):
        self.stgFreq.populateFromFile()
        tI = 2
        tStep = self.tSteps[tI]
        recordDict = self.stgFreq.getRecordDictAtStep(tStep)
        self.assertEqual(recordDict,
            {'Timestep':tStep,'Time':self.timeVals[tI],
              "VRMS":self.VRMSVals[tI]})

    def test_finalStep(self):
        self.assertEqual(self.tSteps[-1], self.stgFreq.finalStep())

    def test_getValuesArray(self):
        valArray = self.stgFreq.getValuesArray('Time')
        for ii, val in enumerate(valArray):
            self.assertAlmostEqual(val, self.timeVals[ii])

    def test_getTimeStepsArray(self):
        timeStepsArray = self.stgFreq.getTimeStepsArray()
        self.assertEqual(self.tSteps, timeStepsArray)

    def test_getMin(self):
        for headerName, testList in [('Time', self.timeVals),
                ('VRMS', self.VRMSVals)]:
            minVal, minStep = self.stgFreq.getMin(headerName)
            calcMin = min(testList)
            calcIndex = testList.index(calcMin)
            self.assertAlmostEqual(minVal, calcMin)
            self.assertEqual(minStep, self.tSteps[calcIndex])

    def test_getMax(self):
        for headerName, testList in [('Time', self.timeVals),
                ('VRMS', self.VRMSVals)]:
            maxVal, maxStep = self.stgFreq.getMax(headerName)
            #print "max for header '%s' calc to be %f at step %d"\
            #    % (headerName, maxVal, maxStep)
            calcMax = max(testList)
            calcIndex = testList.index(calcMax)
            self.assertAlmostEqual(maxVal, calcMax)
            self.assertEqual(maxStep, self.tSteps[calcIndex])

    def test_getMean(self):
        meanVal = self.stgFreq.getMean('VRMS')
        calcMean = old_div(sum(self.VRMSVals, 0.0), len(self.VRMSVals))
        self.assertAlmostEqual(meanVal, calcMean)

    def test_getReductionOps(self):
        #Test the MinOp
        for headerName, testList in [('Time', self.timeVals),
                ('VRMS', self.VRMSVals)]:
            minVal, minStep = self.stgFreq.getReductionOp(headerName,
                stgfreq.minOp)
            calcMin = min(testList)
            calcIndex = testList.index(calcMin)
            self.assertAlmostEqual(minVal, calcMin)
            self.assertEqual(minStep, self.tSteps[calcIndex])
        #Test the MaxOp
        for headerName, testList in [('Time', self.timeVals),
                ('VRMS', self.VRMSVals)]:
            maxVal, maxStep = self.stgFreq.getReductionOp(headerName,
                stgfreq.maxOp)
            calcMax = max(testList)
            calcIndex = testList.index(calcMax)
            self.assertAlmostEqual(maxVal, calcMax)
            self.assertEqual(maxStep, self.tSteps[calcIndex])
        #Test the last op
        for headerName, testList in [('Time', self.timeVals),
                ('VRMS', self.VRMSVals)]:
            lastVal, lastStep = self.stgFreq.getReductionOp(headerName,
                stgfreq.lastOp)
            calcLast = testList[-1]
            calcIndex = len(testList)-1
            self.assertAlmostEqual(lastVal, calcLast)
            self.assertEqual(lastStep, self.tSteps[calcIndex])
        #Test the first op
        for headerName, testList in [('Time', self.timeVals),
                ('VRMS', self.VRMSVals)]:
            firstVal, firstStep = self.stgFreq.getReductionOp(headerName,
                stgfreq.firstOp)
            calcFirst = testList[0]
            calcIndex = 0
            self.assertAlmostEqual(firstVal, calcFirst)
            self.assertEqual(firstStep, self.tSteps[calcIndex])
        #Test the closestToVal
        for headerName, testList in [('Time', self.timeVals),
                ('VRMS', self.VRMSVals)]:
            for targIndex in range(len(self.tSteps)):
                targVal = testList[targIndex] + 0.000001
                closestVal, closestStep = self.stgFreq.getReductionOp(
                    headerName, stgfreq.closestToVal, targVal=targVal)
                self.assertAlmostEqual(closestVal, testList[targIndex])
                self.assertEqual(closestStep, self.tSteps[targIndex])
         #Test the closestToStep
        for headerName, testList in [('Time', self.timeVals),
                ('VRMS', self.VRMSVals)]:
            for targIndex in range(len(self.tSteps)):
                targStep = self.tSteps[targIndex] + 1
                closestVal, closestStep = self.stgFreq.getReductionOp(
                    headerName, stgfreq.closestToStep, targStep=targStep)
                self.assertAlmostEqual(closestVal, testList[targIndex])
                self.assertEqual(closestStep, self.tSteps[targIndex])
         #Test the closestToSimTime
        for headerName, testList in [('VRMS', self.VRMSVals)]:
            for targIndex in range(len(self.tSteps)):
                targTime = self.timeVals[targIndex] + 0.00002
                closestVal, closestStep = self.stgFreq.getReductionOp(
                    headerName, stgfreq.closestToSimTime, targTime=targTime)
                self.assertAlmostEqual(closestVal, testList[targIndex])
                self.assertEqual(closestStep, self.tSteps[targIndex])

    def test_plotOverTime(self):
        self.stgFreq.plotOverTime("Time", show=False, path="output/Plots")
        self.stgFreq.plotOverTime("VRMS", show=False, path="output/Plots")

    def test_printAllMinMax(self):
        self.stgFreq.printAllMinMax()

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(StgFreqTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
