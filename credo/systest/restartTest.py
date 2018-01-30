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
from credo.modelrun import SimParams
from .api import SingleModelSysTest, CREDO_PASS, CREDO_FAIL
from .singleRunWithinTolTC import FieldWithinTolTC

class RestartTest(SingleModelSysTest):
    '''A Restart System test.
       This case simply runs a given model for set number of steps,
       then restarts half-way through, and checks the same result is
       obtained. (Thus it's largely a regression test to ensure
       checkpoint-restarting works for various types of models).
       Uses a :class:`~credo.systest.fieldWithinTolTC.FieldWithinTolTC`
       test component to perform the check.

       Optional constructor keywords:

       * fullRunSteps: number of steps to do the initial "full" run for.
         Must be a multiple of 2, so it can be restarted half-way through.
       * fieldsToTest: Which fields in the model should be compared with the
         reference solution.
       * defFieldTol: The default tolerance to be applied when comparing fields of
         interest between the restarted, and original solution.
         See also the FieldWithinTolTC's
         :attr:`~credo.systest.fieldWithinTolTC.FieldWithinTolTC.defFieldTol`.
       * fieldTols: a dictionary of tolerances to use when testing particular
         fields, rather than the default tolerance defined by
         the defFieldTol argument.

       .. attribute:: fTestName

          Standard name to use for this test's field comparison TestComponent
          in the :attr:`~credo.systest.api.SysTest.testComponents` list.
        '''

    fTestName = 'Restart compared with original'
    description = '''Runs a Model for a set number of timesteps,
        then restarts half-way, checking the standard fields are the
        same at the end for both the original and restart run.'''
    passMsg = "All fields on restart were within required"\
                " tolerance of full run at end."
    failMsg = "At least one field wasn't within tolerance"\
                " on restart run of original run."
    _initialSD = "initial"
    _restartSD = "restart"

    def __init__(self, inputFiles, outputPathBase,
            basePath=None, nproc=1, timeout=None,
            paramOverrides=None, solverOpts=None, nameSuffix=None,
            fieldsToTest = ['VelocityField','PressureField'], fullRunSteps=20,
            defFieldTol=1e-5, fieldTols=None):
        SingleModelSysTest.__init__(self, "Restart",
            inputFiles, outputPathBase,
            basePath, nproc, timeout,
            paramOverrides, solverOpts, nameSuffix)
        self.initialOutputPath = os.path.join(outputPathBase, self._initialSD)
        self.restartOutputPath = os.path.join(outputPathBase, self._restartSD)
        self.fieldsToTest = fieldsToTest
        self.fullRunSteps = fullRunSteps
        if self.fullRunSteps % 2 != 0:
            raise ValueError("fullRunSteps parameter must be even so restart"\
                " can occur half-way - but you provided %d." % (fullRunSteps))
        self.fTests = FieldWithinTolTC(
            fieldsToTest=self.fieldsToTest, defFieldTol=defFieldTol,
            fieldTols=fieldTols,
            useReference=True,
            referencePath=self.initialOutputPath,
            testTimestep=self.fullRunSteps)

    def updateOutputPaths(self, newOutputPathBase):
        """See base class
        :meth:`~credo.systest.api.SysTest.updateOutputPaths`."""
        SingleModelSysTest.updateOutputPaths(self, newOutputPathBase)
        self.initialOutputPath = os.path.join(newOutputPathBase,
            self._initialSD)
        self.restartOutputPath = os.path.join(newOutputPathBase,
            self._restartSD)
        #Also need to re-connect the fTest to use new output path.
        self.fTests.fComps.referencePath = self.initialOutputPath

    def genSuite(self):
        """See base class :meth:`~credo.systest.api.SysTest.genSuite`.

        For this test, will create a suite containing 2 model runs:
        one to initally run the requested Model and save the results,
        and a 2nd to restart mid-way through, so that the results can
        be compared at the end."""
        # Initial run
        initRun = self._createDefaultModelRun(self.testName+"-initial",
            self.initialOutputPath)
        initRun.simParams = SimParams(nsteps=self.fullRunSteps,
            cpevery=self.fullRunSteps/2, dumpevery=0)
        initRun.cpFields = self.fieldsToTest
        self.mSuite.addRun(initRun, "Do the initial full run and checkpoint"\
            " solutions.")
        # Restart run
        resRun = self._createDefaultModelRun(self.testName+"-restart",
            self.restartOutputPath)
        resRun.simParams = SimParams(nsteps=self.fullRunSteps/2,
            cpevery=0, dumpevery=0, restartstep=self.fullRunSteps/2)
        resRun.cpReadPath = self.initialOutputPath
        self.resRunI = self.mSuite.addRun(resRun,
            "Do the restart run and check results at end match initial.")

    def configureTestComps(self):
        self.setupEmptyTestCompsList()
        # Only test fields on the restart run
        self.testComps[self.resRunI][self.fTestName] = self.fTests

    def checkModelResultsValid(self, resultsSet):
        """See base class :meth:`~credo.systest.api.SysTest.checkModelResultsValid`."""
        # TODO check it's a result instance
        # check number of results is correct
        for mResult in resultsSet:
            # Check fieldresults exists, and is right length
            # Check each fieldResult contains correct fields
            pass

    def _writeXMLCustomSpec(self, specNode):
        etree.SubElement(specNode, 'fullRunSteps').text = str(self.fullRunSteps)
        # fieldTols
        fieldsToTestNode = etree.SubElement(specNode, 'fieldsToTest')
        for fieldName in self.fieldsToTest:
            fieldsNode = etree.SubElement(fieldsToTestNode, 'field',
                name=fieldName)

