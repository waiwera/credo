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


import credo.utils
from credo.systest.api import SysTest, SingleModelSysTest, \
    CREDO_PASS, CREDO_FAIL
from credo.modelsuite import ModelSuite

class SkeletonSysTest(SysTest):
    """A Skeleton system test class, used for testing."""

    description = "Skeleton system test."

    def __init__(self, testName, outputPathBase, statusToReturn,
            basePath=None, nproc=1, timeout=None):
        if basePath is None:
            # Since expect this class to be used directly,
            #  get calling path 1 levels up
            basePath = credo.utils.getCallingPath(1)
        SysTest.__init__(self, "SkeletonSysTest", testName,
            basePath, outputPathBase, nproc, timeout)
        self.statusToReturn = statusToReturn

    def genSuite(self):
        # an empty suite
        pass

    def setupEmptyTestCompsList(self):
        # have to over-ride this to prevent errors with our empty suite
        pass

    def configureTestComps(self):
        pass

    def attachAllTestCompOps(self):
        pass

    def checkModelResultsValid(self, resultsSet):
        pass

    def runTest(self, jobRunner, postProcFromExisting=False):
        testStatus = self.getStatus(None)
        testStatus.setRecordFile("Foo.xml")
        return testStatus, None

    def getStatus(self, resultsSet):
        self.testStatus = self.statusToReturn
        return self.testStatus

    def _writeXMLCustomSpec(self, specNode):
        pass


class SkeletonSingleModelSysTest(SingleModelSysTest):
    """A Skeleton system test class, used for testing."""

    description = "Skeleton system test."

    def __init__(self, inputFiles, outputPathBase, statusToReturn,
            basePath=None, nproc=1, timeout=None,
            paramOverrides=None, solverOpts=None, nameSuffix=None):
        SingleModelSysTest.__init__(self, "SkeletonSingleModelSysTest",
            inputFiles, outputPathBase,
            basePath, nproc, timeout,
            paramOverrides, solverOpts, nameSuffix)

        self.statusToReturn = statusToReturn

    def genSuite(self):
        # an empty suite
        self.mSuite = ModelSuite(outputPathBase=self.outputPathBase)
        return self.mSuite

    def checkModelResultsValid(self, resultsSet):
        pass

    def getStatus(self, resultsSet):
        self.testStatus = self.statusToReturn
        return self.testStatus

    def _writeXMLCustomSpec(self, specNode):
        pass
