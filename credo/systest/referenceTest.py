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

"""Provides a :class:`.ReferenceTest` for use in system testing.

.. attribute:: DEF_TEST_FIELDS

   Default fields that will be tested, if not explicitly provided
   as a constructor keyword argument to :class:`~.ReferenceTest` instantiations.
"""

import os
from xml.etree import ElementTree as etree

from credo.modelsuite import ModelSuite
from credo.modelrun import SimParams
import credo.jobrunner
from .api import SingleModelSysTest, CREDO_PASS, CREDO_FAIL, getStdTestNameBasic
from .fieldWithinTolTC import FieldWithinTolTC

DEF_TEST_FIELDS = ['VelocityField','PressureField']

class ReferenceTest(SingleModelSysTest):
    '''A Reference System test.
    This case simply runs a given model for a set number of steps,
    then checks the resultant solution matches within a tolerance
    of a previously-generated reference solution. Uses a
    :class:`~credo.systest.fieldWithinTolTC.FieldWithinTolTC`
    test component to perform the check.

    Optional constructor keywords:

    * runSteps: number of steps the reference solution should run for.
    * fieldsToTest: Which fields in the model should be compared with the
      reference solution, as a list. If not provided, will default to
      :attr:`.DEF_TEST_FIELDS`.
    * defFieldTol: The default tolerance to be applied when comparing
      fields of interest to the reference solution.
      See also the FieldWithinTolTC's
      :attr:`~credo.systest.fieldWithinTolTC.FieldWithinTolTC.defFieldTol`.
    * fieldTols: a dictionary of tolerances to use when testing particular
      fields, rather than the default tolerance as set in the defFieldTol
      argument.
       
    .. attribute:: fTestName

       Standard name to use for this test's field comparison TestComponent
       in the :attr:`~credo.systest.api.SysTest.testComponents` list.
    '''

    fTestName = 'Reference Solution compare'
    description = '''Runs a Model for a set number of timesteps,
        then checks the specified fields match a previously-generated
        reference solution.'''
    passMsg = "All fields were within required tolerance of reference"\
        " soln at end of run."
    failMsg = "A Field was not within tolerance of reference soln."

    def __init__(self, inputFiles, outputPathBase,
            basePath=None, nproc=1, timeout=None,
            paramOverrides=None, solverOpts=None, nameSuffix=None, 
            fieldsToTest = None, runSteps=20, defFieldTol=1e-2, fieldTols=None,
            expPathPrefix="expected"):
        SingleModelSysTest.__init__(self, "Reference",
            inputFiles, outputPathBase,
            basePath, nproc, timeout,
            paramOverrides, solverOpts, nameSuffix)
        testNameBasic = getStdTestNameBasic(self.testType+"Test",
            self.inputFiles)
        self.expectedSolnPath = os.path.join(expPathPrefix, testNameBasic)
        if fieldsToTest == None:
            # Set default fields to test.
            self.fieldsToTest = DEF_TEST_FIELDS
        else:    
            self.fieldsToTest = fieldsToTest
        self.runSteps = runSteps
        self.fTests = FieldWithinTolTC(fieldsToTest=self.fieldsToTest,
            defFieldTol=defFieldTol,
            fieldTols=fieldTols,
            useReference=True,
            referencePath=self.expectedSolnPath,
            testTimestep=self.runSteps)

    def regenerateFixture(self, jobRunner):
        '''Do a run to create the reference solution to use.
        
        .. note:: by default, this will save checkpoint for the entire step,
           not just fields to be checkpointed against.'''

        print "Running the model to create a reference solution after %d"\
            " steps, and saving in dir '%s'" % \
            (self.runSteps, self.expectedSolnPath)
        mRun = self._createDefaultModelRun(self.testName+"-createReference",
            self.expectedSolnPath)
        mRun.simParams = SimParams(nsteps=self.runSteps, cpevery=self.runSteps,
            dumpevery=0)
        mRun.cpFields = self.fieldsToTest
        mRun.writeInfoXML()
        result = jobRunner.runModel(mRun)
        # It's conceivable this could be useful, if we store results about
        # e.g. solver solution times etc.
        result.writeRecordXML()

    # TODO: a pre-check phase - check the reference dir exists?

    def genSuite(self):
        """See base class :meth:`~credo.systest.api.SysTest.genSuite`.
        For this test, just a single model run is needed, to run
        the model and compare against the reference solution."""
        mRun = self._createDefaultModelRun(self.testName,
            os.path.join(self.outputPathBase, "testRun"))
        mRun.simParams = SimParams(nsteps=self.runSteps,
            cpevery=0, dumpevery=0)
        self.mSuite.addRun(mRun, "Run the model, and check results against "\
            "previously generated reference solution.")

    def configureTestComps(self):
        assert len(self.mSuite.runs) == 1
        self.setupEmptyTestCompsList()
        self.testComps[0][self.fTestName] = self.fTests

    def checkModelResultsValid(self, resultsSet):
        """See base class 
        :meth:`~credo.systest.api.SysTest.checkModelResultsValid`."""
        # TODO check it's a result instance
        # check number of results is correct
        for mResult in resultsSet:
            # Check fieldresults exists, and is right length
            # Check each fieldResult contains correct fields
            pass

    def _writeXMLCustomSpec(self, specNode):
        etree.SubElement(specNode, 'runSteps').text = str(self.runSteps)
        # fieldTols
        fieldsToTestNode = etree.SubElement(specNode, 'fieldsToTest')
        for fieldName in self.fieldsToTest:
            fieldsNode = etree.SubElement(fieldsToTestNode, 'field',
                name=fieldName)    
