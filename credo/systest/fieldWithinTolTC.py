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

from xml.etree import ElementTree as etree

from .api import SingleRunTestComponent, CREDO_PASS, CREDO_FAIL
import credo.analysis.fields as fields

class FieldWithinTolTC(SingleRunTestComponent):
    """Checks whether, for a particular set of fields, the error
    between each field and an (analytic or reference) solution
    is below a specificed tolerance.

    This relies largely on functionality of:

    * :mod:`credo.analysis.fields` to specify the comparison operations
    * :mod:`credo.io.stgcvg` to analyse the "convergence" files containing
      comparison information produced by these operations.

    Other than those that are directly saved as attributes documented below,
    the constructor arguments of interest are:

    * useReference: determines whether the fields are compared against
      a reference, or analytic solution. See
      :meth:`credo.analysis.fields.FieldComparisonList.useReference`
    * useHighResReference: determines whether the fields are compared against
      a high resolution reference field, or analytic solution. See
      :meth:`credo.analysis.fields.FieldComparisonList.useHighResReference`
    * referencePath: See
      :meth:`credo.analysis.fields.FieldComparisonList.referencePath`
    * testTimestep: See
      :meth:`credo.analysis.fields.FieldComparisonList.testTimestep`

    .. attribute:: fieldsToTest

       A list of strings containing the names of fields that should be tested-
       i.e. those that will be compared with an expected solution. If left
       as `None` in constructor, this means the fieldsToTest list will be
       expected to be defined in the StGermain model XML files themselves.

    .. attribute:: defFieldTol

       The default allowed tolerance for global normalised error when comparing
       Fields with their expected values.

    .. attribute:: fieldTols

       A dictionary, mapping particular field names to particular tolerances
       to use, overriding the default. E.g. {"VelocityField":1e-4} means
       the tolerance used for the VelocityField will be 1e-4.

    .. attribute:: fComps

        A :class:`credo.analysis.fields.FieldComparisonList` used as an
        operator to attach to ModelRuns to be tested, and do the actual
        comparison between fields.

    .. attribute:: fieldResults

       Initially {}, after the test is completed will store a dictionary
       mapping each field name to a Bool saying whether or not it was within
       the required tolerance.

    .. attribute:: fieldErrors

       Initially {}, after the test is completed will store a dictionary
       mapping each field name to a float representing the global normalised
       error in the comparison.
    """

    def __init__(self, fieldsToTest=None,
            defFieldTol=0.01,
            fieldTols=None,
            useReference=False,
            useHighResReference= False,
            referencePath=None,
            testTimestep=0
            ):
        # TODO: [Refactor] simplify, combine Ref/HRRef/Analytic to one
        SingleRunTestComponent.__init__(self, "fieldWithinTol")
        self.fieldsToTest = fieldsToTest
        self.defFieldTol = defFieldTol
        self.fieldTols = fieldTols
        self.fComps = fields.FieldComparisonList()
        self.fComps.useReference = useReference
        self.fComps.useHighResReference = useHighResReference
        if useReference and useHighResReference:
            raise ValueError("Don't define both regular reference and high "\
               "res reference solution mode - choose one or the other.")
        self.fComps.referencePath = referencePath
        self.fComps.testTimestep = testTimestep
        self.fieldResults = {}
        self.fieldErrors = {}

    def attachOps(self, modelRun):
        # TODO: [Refactor] interface to remove or changed to pre-run blah.
        """Implements base class
        :meth:`credo.systest.api.SingleRunTestComponent.attachOps`."""
        if self.fieldsToTest == None:
            self.fComps.readFromStgXML(modelRun.modelInputFiles,
                modelRun.basePath)
        else:
            for fieldName in self.fieldsToTest:
                self.fComps.add(fields.FieldComparisonOp(fieldName))
        modelRun.analysisOps['fieldComparisons'] = self.fComps

    def getTolForField(self, fieldName):
        # TODO: [Refactor] remove
        """Utility func: given fieldName, returns the tolerance to use for
        testing that field (may be given by :attr:`.defFieldTol`, or
        been over-ridden in :attr:`.fieldTols`)."""
        if (self.fieldTols is not None) and fieldName in self.fieldTols:
            fieldTol = self.fieldTols[fieldName]
        else:
            fieldTol = self.defFieldTol
        return fieldTol

    def check(self, mResult):
        """Implements base class
        :meth:`credo.systest.api.SingleRunTestComponent.check`."""
        self.fieldResults = {}
        self.fieldErrors = {}
        statusMsg = ""
        overallResult = True
        for fComp in self.fComps.fields.itervalues():
            fieldTol = self.getTolForField(fComp.name)
            fieldResult, dofErrors = self._checkFieldWithinTol(fComp, mResult)
            self.fieldResults[fComp.name] = fieldResult
            self.fieldErrors[fComp.name] = dofErrors
            if not fieldResult:
                statusMsg += "Field comp '%s' error(s) of %s not within"\
                    " tol %g of %s solution\n"\
                    % (fComp.name, dofErrors, fieldTol,
                    self.fComps.getCmpSrcString())
                overallResult = False
            else:
                statusMsg += "Field comp '%s' error within tol %g of %s"\
                    " solution.\n"\
                    % (fComp.name, fieldTol, self.fComps.getCmpSrcString())

        print statusMsg
        self._setStatus(overallResult, statusMsg)
        return overallResult

    def _checkFieldWithinTol(self, fComp, mResult):
        # TODO: [Refactor] remove, only used by .check()
        fieldTol = self.getTolForField(fComp.name)
        fCompRes = fComp.getResult(mResult)
        fieldResult = fCompRes.withinTol(fieldTol)
        dofErrors = fCompRes.dofErrors
        return fieldResult, dofErrors

    def _writeXMLCustomSpec(self, specNode):
        etree.SubElement(specNode, 'fromXML', value=str(self.fComps.fromXML))
        etree.SubElement(specNode, 'testTimestep',
            value=str(self.fComps.testTimestep))
        etree.SubElement(specNode, 'useReference',
            value=str(self.fComps.useReference))
        etree.SubElement(specNode, 'useHighResReference',
            value=str(self.fComps.useHighResReference))
        if self.fComps.useReference or self.fComps.useHighResReference:
            etree.SubElement(specNode, 'referencePath',
                value=self.fComps.referencePath)
        fListNode = etree.SubElement(specNode, 'fields')
        for fName in self.fComps.fields.keys():
            fNode = etree.SubElement(fListNode, 'field', name=fName,
                tol=str(self.getTolForField(fName)))

    def _writeXMLCustomResult(self, resNode, mResult):
        frNode = etree.SubElement(resNode, 'fieldResultDetails')
        for fName, fComp in self.fComps.fields.iteritems():
            fieldTol = self.getTolForField(fName)
            fieldRes = self.fieldResults[fName]
            fieldNode = etree.SubElement(frNode, "field", name=fName)
            fieldNode.attrib['allDofsWithinTol'] = str(fieldRes)
            desNode = etree.SubElement(fieldNode, "dofErrors")
            for dofI, dofError in enumerate(self.fieldErrors[fName]):
                deNode = etree.SubElement(desNode, "dofError")
                deNode.attrib["num"] = str(dofI)
                deNode.attrib["error"] = "%6e" % dofError
                deNode.attrib["withinTol"] = str(dofError <= fieldTol)
