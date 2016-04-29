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

from credo.modelrun import JobParams
from credo.modelresult import ModelResult
from credo.jobrunner.pbsjobrunner import PBSJobRunner
from skeleton import SkeletonModelRun, SkeletonModelResult, SkeletonModelSuite

class PBSJobRunnerTestCase(unittest.TestCase):
    def setUp(self):
        self.jobRunner = PBSJobRunner()

    def tearDown(self):
        pass

    def test_writePBSFile_basic(self):
        modelRun = SkeletonModelRun("skelMRun1", "output/test1")
        modelRun.jobParams = JobParams(nproc=2, maxRunTime=1000,
            pollInterval=10)
        runCommand = "mpiexec ./someApp Input.xml"
        self.jobRunner._writePBSFile(modelRun, runCommand)

    def test_writePBSFile_opts(self):
        """This time test writing with several PBS-specific options."""
        modelRun = SkeletonModelRun("skelMRun2", "output/test1")
        modelRun.jobParams = JobParams(nproc=2, maxRunTime=1000,
            pollInterval=10,
            PBS={'queue':"sque",
                'jobNameLine':"#PBS -N CoolJob",
                'nodeLine':"#PBS -l nodes=4:3",
                'sourcefiles':['/usr/srcfile.sh'],
                'modules':['hdf5','underworld','petsc']})
        runCommand = "mpiexec ./someApp Input.xml"
        self.jobRunner._writePBSFile(modelRun, runCommand)

    def test_blockResult(self):
        self.fail()
        # TODO: set up a fake PBS jobHandle
        result = self.jobRunner.blockResult(self, modelRun, jobMetaInfo)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PBSJobRunnerTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
