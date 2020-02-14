from future import standard_library
standard_library.install_aliases()
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
import pickle as pickle
import shutil
import tempfile
import unittest

from credo.analysis.fields import FieldComparisonOp, FieldComparisonList
from credo.analysis.fields import FieldComparisonResult
from credo.modelresult import ModelResult

class AnalysisFieldsTestCase(unittest.TestCase):

    def setUp(self):
        self.basedir = os.path.realpath(tempfile.mkdtemp())
        #os.makedirs(os.path.join(self.basedir,self.results_dir,'StGermain'))
            #self.results_xml = open(os.path.join(self.basedir, self.results_dir, 'StGermain', 'TEST-FooSuite.xml'), 'w')

    def tearDown(self):
        shutil.rmtree(self.basedir)

    def test_getResult(self):
        mRes = ModelResult("test", './output/')
        fComp = FieldComparisonOp('TemperatureField')
        fRes = fComp.getResult(mRes)
        self.assertEqual(fRes.fieldName, fComp.name)
        self.assertEqual(fRes.dofErrors[0], 0.00612235812)

    def test_getAllResults(self):
        mRes = ModelResult("test", './output')
        fieldComps = FieldComparisonList()
        fComp = FieldComparisonOp('TemperatureField')
        fieldComps.add(fComp)
        fResults = fieldComps.getAllResults(mRes)
        self.assertEqual(len(fResults), 1)
        self.assertEqual(fResults[0].fieldName, fComp.name)
        self.assertEqual(fResults[0].dofErrors[0], 0.00612235812)

    def test_WithinTol(self):
        fRes = FieldComparisonResult('TemperatureField', [0.1,0.2])
        self.assertTrue(fRes.withinTol(0.3))
        fRes = FieldComparisonResult('TemperatureField', [0.4,0.2])
        self.assertFalse(fRes.withinTol(0.3))

    def test_addFieldComparisonOp(self):
        fieldCompares = FieldComparisonList()
        self.assertEqual(fieldCompares.fields, {})
        self.assertEqual(fieldCompares.fields, {})
        tempFT = FieldComparisonOp('TemperatureField')
        fieldCompares.add(tempFT)
        velFT = FieldComparisonOp('VelocityField')
        fieldCompares.add(velFT)
        self.assertEqual(fieldCompares.fields, {'TemperatureField':tempFT,\
            'VelocityField':velFT})

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AnalysisFieldsTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

