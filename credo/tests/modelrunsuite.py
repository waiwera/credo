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

from credo import modelrun as mrun
from credo import modelresult as mres

class ModelRunTestCase(unittest.TestCase):

    def setUp(self):
        #self.basedir = os.path.realpath(tempfile.mkdtemp())
        self.basedir = 'modelRunWorking'
        if not os.path.exists(self.basedir):
            os.makedirs(self.basedir)
        self.inputFiles = [os.path.join('input', 'testModel.xml')]
        self.outputPath = os.path.join('output', 'testModel')

    def tearDown(self):
        shutil.rmtree(self.basedir)

    def test_checkValidRunConfig(self):
        #TODO
        self.fail()

    def test_checkPreRunPreparation(self):
        #TODO
        self.fail()

    def test_getModelRunAppExeCommand(self):
        #TODO
        self.fail()

    def test_getModelRunCommand(self):
        #TODO
        self.fail()

    def test_postRunCleanup(self):
        #TODO
        self.fail()

    def test_checkSolverOptsFile(self):
        #TODO
        self.fail()

    def test_writeInfoXML(self):
        nproc = 2
        modelRun = mrun.ModelRun('TestModel', self.inputFiles,
            self.outputPath, nproc=nproc, basePath=self.basedir)
        modelRun.simParams = mrun.SimParams(nsteps=5, cpevery=10)
        modelRun.writeInfoXML(prettyPrint=True)

    def test_analysisXMLGen(self):
        #TODO
        self.fail()

    def test_genFlattenedXML(self):
        modelRun = mrun.ModelRun('TestModel', self.inputFiles,
            self.outputPath, basePath=self.basedir)
        modelRun.simParams = mrun.SimParams(nsteps=5, cpevery=10)
        modelRun.paramOverrides['allowUnbalancing'] = False
        modelRun.paramOverrides['defaultDiffusivity'] = 1.0e-5
        flatFilename=os.path.join("output", "testFlat.xml")
        modelRun.genFlattenedXML(flatFilename=flatFilename)
        os.unlink(modelRun.analysisXML)
        self.assertTrue(os.path.exists(flatFilename))
        # TODO: Some extra tests would be good here of the newly created
        # flattened file


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ModelRunTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
