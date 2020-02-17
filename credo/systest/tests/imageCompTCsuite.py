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
import unittest

from credo.systest.imageCompTC import *
from credo.modelresult import ModelResult

class ImageCompTCTestCase(unittest.TestCase):
    def setUp(self):
        self.imageRefPath = os.path.join('input','testImages')
        self.resultsPath1 = os.path.join('input','resultsDirs','res1')
        self.resultsPath2 = os.path.join('input','resultsDirs','res2')
        # Set up a skeleton model run.
        self.imageCompTest = ImageCompTC("window.00001.png", (0.1, 0.1),
            refPath=self.imageRefPath)
        self.resultsSet1 = ModelResult('testModel1', self.resultsPath1)
        self.resultsSet2 = ModelResult('testModel2', self.resultsPath2)

    def tearDown(self):
        pass

    def test_attachOps(self):
        # test the model can have appropriate ops attached.
        # In the case of this testComp, nothing to be done.
        pass

    def test_check(self):
        checkRes = self.imageCompTest.check(self.resultsSet1)
        self.assertTrue(checkRes)
        checkRes = self.imageCompTest.check(self.resultsSet2)
        self.assertTrue(checkRes)
        self.imageCompTest.tol = (1e-10, 1e-10)
        checkRes = self.imageCompTest.check(self.resultsSet2)
        self.assertFalse(checkRes)

    def test_writeXMLSpec(self):
        testNode = etree.Element('testSpec')
        self.imageCompTest._writeXMLCustomSpec(testNode)
        self.assertEqual(testNode.find('imageFilename').text,
            self.imageCompTest.imageFilename)
        tolNode = testNode.find('tolerances')
        self.assertTrue(tolNode != None)
        for ii, tolCompNode in enumerate(tolNode.getchildren()):
            self.assertEqual(int(tolCompNode.attrib['comp']), ii)
            self.assertAlmostEqual(float(tolCompNode.attrib['value']),
                self.imageCompTest.tol[ii])
        self.assertEqual(testNode.find('refPath').text,
            str(self.imageCompTest.refPath))
        self.assertEqual(testNode.find('genPath'), None)

    def test_writeXMLResult(self):
        testNode = etree.Element('testResult')
        self.imageCompTest.tol = (1e-10, 1e-10)
        self.imageCompTest.imageErrors = (1.e-11, 0.03)
        self.imageCompTest.imageResults = [True, False]
        self.imageCompTest._writeXMLCustomResult(testNode, None)
        errorsNode = testNode.find('imgErrors')
        self.assertTrue(errorsNode != None)
        for ii, eNode in enumerate(errorsNode.getchildren()):
            self.assertEqual(int(eNode.attrib['num']), ii)
            self.assertAlmostEqual(float(eNode.attrib['error']),
                self.imageCompTest.imageErrors[ii])
            self.assertEqual(eNode.attrib['withinTol'],
                str(self.imageCompTest.imageErrors[ii] <= \
                    self.imageCompTest.tol[ii]))

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ImageCompTCTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
