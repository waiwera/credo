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

"""Package for manipulation of a set of :class:`.SystemTest` s.
Interacts closely with :package:`.SysTestRunner`."""

import os
import inspect
import credo.utils
import credo.io.stgpath as stgpath
from . import api as testapi

class SysTestSuite:
    """Class that aggregates  a set of :class:`~credo.systest.api.SysTest`.

    For examples of how to use, see the CREDO documentation, especially
    :ref:`credo-examples-run-systest-direct`.

    .. attribute:: projectName

       Name of the "Project" the test suite is attached to, e.g. "Underworld"
       or "StgFEM".

    .. attribute:: suiteName

       A short descriptive name of the test suite. NB: doesn't have to be
       unique, e.g. you may want to create different suites with the same\
       suite names, but different project names.

    .. attribute:: sysTests

       List of system tests that should be run and reported upon. Generally
       shouldn't be accessed directly, recommend using :meth:`.addStdTest`
       to add to this list, and other methods to run and report on it.

    .. attribute:: subSuites

       List of subSuites (defaults to none) associated with this suite.
       Associating sub-suites allows a nested hierarchy of system tests.

    .. attribute:: nproc

       The default number of processors to use for tests associated with this
       suite (can be over-ridden per test case though).
    """

    def __init__(self, projectName, suiteName, sysTests=None,
            subSuites=None, nproc=1):
        self.projectName = projectName
        self.suiteName = suiteName
        if sysTests == None:
            self.sysTests = []
        else:
            if not isinstance(sysTests, list):
                raise TypeError("Error, if the sysTests keyword is"
                    " provided it must be a list of SysTest.")
            self.sysTests = sysTests
        if subSuites == None:
            self.subSuites = []
        else:
            if not isinstance(subSuites, list):
                raise TypeError("Error, if the subSuites keyword is"
                    " provided it must be a list of SysTestSuites.")
            self.subSuites = subSuites
        self.nproc = nproc

    def addStdTest(self, testClass, inputFiles, **testOpts):
        """Instantiate and add a "standard" system test type to the list
        of System tests to be run. (The "standard" refers to the user needing
        to have access to the module containing the system test type to be
        added, usually from a `from credo.systest import *` statement.

        :param testClass: Python class of the System test to be added. This
          needs to be a sub-class of :class:`~credo.systest.api.SysTest`.
        :param inputFiles: model input files to be passed through to the
          System test when instantiated.
        :param `**testOpts`: any other keyword arguments the user wishes to
          passed through to the System test when it's instantiated.
          Can be used to customise a test.
        :returns: a reference to the newly created and added SysTest."""

        if not inspect.isclass(testClass):
            raise TypeError("The testClass argument must be a type that's"\
                " a subclass of the CREDO SysTest type. Arg passed in, '%s',"\
                " of type '%s', is not a Python Class." \
                % (testClass, type(testClass)))
        if not issubclass(testClass, testapi.SingleModelSysTest):
            raise TypeError("The testClass argument must be a type that's"\
                " a subclass of the CREDO SysTest type. Type passed in, '%s',"\
                " not a subclass of SysTest." \
                % (testClass))
        callingPath = credo.utils.getCallingPath(1)
        # If just given a single input file as a string, convert
        #  to a list (containing that single file).
        if isinstance(inputFiles, str):
            inputFiles = [inputFiles]
        absInputFiles = stgpath.convertLocalXMLFilesToAbsPaths(inputFiles,
            callingPath)
        stgpath.checkAllXMLInputFilesExist(absInputFiles)
        if 'nproc' not in testOpts:
            testOpts['nproc']=self.nproc
        outputPath = testapi.getStdOutputPath(testClass, inputFiles, testOpts)
        newSysTest = testClass(inputFiles, outputPath, basePath=callingPath,
            **testOpts)
        self.sysTests.append(newSysTest)
        return newSysTest

    def addSubSuite(self, subSuite):
        """Adds a single sub-suite to the list of sub-suites."""
        if not isinstance(subSuite, SysTestSuite):
            raise TypeError("subSuite must be an instance of type"\
                " SysTestSuite.")
        self.subSuites.append(subSuite)

    def addSubSuites(self, subSuites):
        """Adds a set of sub-suites to the list of sub-suites."""
        for subSuite in subSuites:
            self.addSubSuite(subSuite)

    def newSubSuite(self, *subSuiteRegArgs, **subSuiteKWArgs):
        """Shortcut to create a new sub-suite, add it to the existing suite,
        and return reference to the newly created sub-suite."""
        subSuite = SysTestSuite(*subSuiteRegArgs, **subSuiteKWArgs)
        self.addSubSuite(subSuite)
        return subSuite

    def setAllTimeouts(self, seconds=0, minutes=0, applyToSubSuites=True):
        """Utility function to set all the timeouts for all system tests
        associated with the suite to a certain value."""
        for sysTest in self.sysTests:
            sysTest.setTimeout(seconds, minutes)

        for subSuite in self.subSuites:
            subSuite.setAllTimeouts(seconds, minutes, applyToSubSuites)
