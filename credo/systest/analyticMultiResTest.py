from builtins import str
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
import credo.modelrun as mrun
from .api import SingleModelSysTest, CREDO_PASS, CREDO_FAIL
from .fieldCvgWithScaleTC import FieldCvgWithScaleTC

class AnalyticMultiResTest(SingleModelSysTest):
    '''A Multiple Resolution system test.
       This test can be used to convert any existing system test that
       analyses fields, to check that the error between the analytic
       solution fields and the actual results improves at the required
       rate as the model resolution is increased. Uses a
       :class:`~credo.systest.fieldCvgWithScaleTC.FieldCvgWithScaleTC`
       test component to perform the check.

       Optional constructor keywords:

       * resSet: a list of resolutions to use for the test, as tuples.
         E.g. to specify testing at 10x10 res then 20x20, resSet would
         be [(10,10), (20,20)]

       .. attribute:: resSet

          Set of resolutions to use, as described for the resSet keyword
          to the constructor.
       '''

    description = '''Runs an existing test with multiple resolutions.'''
    passMsg = "The solution compared to the analytic result"\
	    " converged as expected with increasing resolution for all fields."
    failMsg = "One of the fields failed to converge as expected."

    def __init__(self, inputFiles, outputPathBase, resSet,
            basePath=None, nproc=1, timeout=None,
            paramOverrides=None, solverOpts=None, nameSuffix=None):
        SingleModelSysTest.__init__(self, "AnalyticMultiResConvergence",
            inputFiles, outputPathBase,
            basePath, nproc, timeout,
            paramOverrides, solverOpts, nameSuffix)
        self.resSet = resSet
        self.cvgChecker = FieldCvgWithScaleTC()

    def genSuite(self):
        """See base class :meth:`~credo.systest.api.SysTest.genSuite`.

        The generated suite will contain model runs all with the same model
        XML files, but with increasing resolution as specified by the
        :attr:`.resSet` attribute.
        """
        for res in self.resSet:
            resStr = mrun.strRes(res)
            modelName = self.testName+'-'+resStr
            mRun = self._createDefaultModelRun(modelName,
                os.path.join(self.outputPathBase, resStr))
            customOpts = mrun.generateResOpts(res)
            self.mSuite.addRun(mRun, "Run the model at res %s" % (resStr), customOpts)

    def configureTestComps(self):
        self.setupEmptyTestCompsList()
        self.multiRunTestComps['fieldConvChecker'] = self.cvgChecker

    def checkModelResultsValid(self, resultsSet):
        """See base class :meth:`~credo.systest.api.SysTest.checkModelResultsValid`."""
        # TODO check it's a result instance
        # check number of results is correct
        for mResult in resultsSet:
            # Check fieldresults exists, and is right length
            # Check each fieldResult contains correct fields
            pass

    def _writeXMLCustomSpec(self, specNode):
        resSetNode = etree.SubElement(specNode, "resSet")
        for res in self.resSet:
            resNode = etree.SubElement(resSetNode, "res")
            resNode.attrib['x'] = str(res[0])
            resNode.attrib['y'] = str(res[1])
            if len(res) == 3:
                resNode.attrib['z'] = str(res[2])
        #TODO: if we allow user to choose/override convergence checking
        # algorithm
        #cvgFuncNode = etree.SubElement(specNode, "cvgFunc")
        #cvgFuncNode.attrib['name']
        #cvgFuncNode.attrib['module'] = inspect.getmodule(cvgFunc)


