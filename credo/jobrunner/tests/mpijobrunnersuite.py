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

from credo.modelrun import ModelRun
from credo.modelresult import ModelResult
from credo.modelsuite import ModelSuite
from credo.jobrunner.mpijobrunner import MPIJobRunner, MPIJobMetaInfo

class MPIJobRunnerTestCase(unittest.TestCase):
    def setUp(self):
        self.jobRunner = MPIJobRunner()

    def tearDown(self):
        pass

    def test_submitRun(self):
        self.fail()
        jobMetaInfo = self.jobRunner.submitRun(self, modelRun,
            prefixStr=None, extraCmdLineOpts=None, dryRun=False,
            maxRunTime=None)

    def test_blockResult(self):
        self.fail()
        # TODO: set up a fake MPI jobHandle
        result = self.jobRunner.blockResult(self, modelRun, jobMetaInfo)

    def test_attachPlatformInfo(self):
        jobMI = MPIJobMetaInfo()
        self.jobRunner.attachPlatformInfo(jobMI)
        #TODO: check MPI-specific info
        pass

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MPIJobRunnerTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
