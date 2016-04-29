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
from xml.etree import ElementTree as etree

from credo.modelsuite import ModelSuite
from .api import SysTest, TestComponent, CREDO_PASS, CREDO_FAIL
import credo.utils

class SciBenchmarkTest(SysTest):
    '''A Science benchmark test.
        This is an open-ended system test, designed for the user to add multiple
        :class:`~.api.TestComponent` s to,
        which test the conditions of the benchmark.
        Contains extra capabilities to report more fully on the test result
        than a standard system test.

        See the examples section of the CREDO documentation,
        :ref:`credo-examples-scibenchmarking`, for examples of sci benchmarking
        in practice.'''

    description = '''Runs a user-defined science benchmark.'''
    passMsg = "All aspects of the benchmark passed."
    failMsg = "At least one aspect of the benchmark failed."

    def __init__(self, testName, outputPathBase=None,
            basePath=None, nproc=1, timeout=None):
        if basePath is None:
            # Since expect this class to be used directly,
            #  get calling path 1 levels up
            basePath = credo.utils.getCallingPath(1)
        if outputPathBase == None:
            outputPathBase = os.path.join("output", testName)
        SysTest.__init__(self, "SciBenchmark", testName, basePath,
            outputPathBase, nproc, timeout)
        # In the case of SciBenchmarks, we will auto-create the
        # ModelSuite here, since it's up to the user to configure
        # this rather than being done automatically in getSuite().
        self.mSuite = ModelSuite(outputPathBase=self.outputPathBase)

    def setupTest(self):
        """Overriding default SysTest.setupTest() method, as for
        SciBenchmarks we want to allow the user to manage test setup
        explicitly in their benchmark script. Thus assume suite
        runs and test components have been setup correctly already."""
        # Re-force this just in case
        self.mSuite.outputPathBase = self.outputPathBase
        # Check all output paths are subdirs of outputPathBase, if not correct
        for mRun in self.mSuite.runs:
            commonPrefix = os.path.commonprefix(
                [self.outputPathBase, mRun.outputPath])
            if commonPrefix != self.outputPathBase:
                mRun.outputPath = os.path.join(self.outputPathBase, mRun.name)

    def addTestComp(self, runI, testCompName, testComp):
        """Add a testComponent (:class:`~.api.TestComponent`)
        with name testCompName to the list of test
        components to be applied as part of determining if the benchmark
        has passed. Does basic error-checking."""
        if not isinstance(testComp, TestComponent):
            raise TypeError("Test component passed in to be added to"\
                " benchmark, '%s', not an instance of a TestComponent."\
                % (testComp))
        if not len(self.testComps) == len(self.mSuite.runs):
            raise AttributeError("Error, the array of testComps hasn't yet "\
                "been properly set up to match the modelSuite's number of "\
                "runs (%d). Have you run both %s and %s already?"\
                % (len(self.mSuite.runs), "self.mSuite.genSuite()", \
                    "self.setupEmptyTestCompsList()"))
        try:
            self.testComps[runI][testCompName] = testComp
        except IndexError:
            raise ValueError("Error, 'run' passed in must be < the number"\
                " of runs in this system test's ModelSuite, currently %d"\
                % (len(self.testComps)))

    def configureSuite(self):
        raise NotImplementedError("Should not be called on SciBenchmark"\
            " class, user should configure suite manually by operating on"\
            " benchmarks .mSuite attribute directly.")

    def configureTestComps(self):
        raise NotImplementedError("Should not be called on SciBenchmark"\
            " class, user should configure manually by calling addTestComps()")

    def _writeXMLCustomSpec(self, specNode):
        # TODO: write info about the modelRuns making up the suite ...
        #  or should this be a standard feature of all Sys tests writeups?
        # TODO: write stuff like paper references here?
        # TODO: does this need to be converted to an FP to allow
         # user to more easily over-ride? Or is that done via
         #  custom test components?
        pass
