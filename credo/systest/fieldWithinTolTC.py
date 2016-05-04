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

class FieldWithinTolTC(SingleRunTestComponent):
    """Checks whether, for a particular set of fields, the error
    between each field and an (analytic or reference) solution
    is below a specificed tolerance.

    Other than those that are directly saved as attributes documented below,
    the constructor arguments of interest are:

    * expected: An expected solution in the form of a ModelResult
      (ReferenceResult, HighResReferenceResult) or a function (analytic
      solution).
    * testTimestep: Integer, the timestep of the model that the comparison will
      occur at.  If -1, means the final timestep.

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
            expected=None,
            testTimestep=-1
            ):
        SingleRunTestComponent.__init__(self, "fieldWithinTol")
        self.fieldsToTest = fieldsToTest
        self.defFieldTol = defFieldTol
        self.fieldTols = fieldTols
        # TODO: [Refactor] complete check with ModelResult and func
        if expected is None:
            raise ValueError("expected solution must be ModelResult or func.")
        if callable(expected):
            self.compareSource = 'analytic'
        else:
            # TODO: [Refactor] add support for HighResReferenceResult
            self.compareSource = 'reference'
        self.expected = expected
        self.testTimestep = testTimestep
        self.fieldResults = {}
        self.fieldErrors = {}

    def attachOps(self, modelRun):
        # TODO: [Refactor] interface to remove or changed to pre-run blah.
        """Implements base class
        :meth:`credo.systest.api.SingleRunTestComponent.attachOps`."""
        pass

    def _getTolForField(self, fieldName):
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
        for field in self.fieldsToTest:
            fieldResult, dofErrors = self._checkFieldWithinTol(field, mResult)
            self.fieldResults[field] = fieldResult
            self.fieldErrors[field] = dofErrors
            fieldTol = self._getTolForField(field)
            if not fieldResult:
                statusMsg += "Field comp '%s' error(s) of %s not within"\
                    " tol %g of %s solution\n"\
                    % (field, dofErrors, fieldTol, self.compareSource)
                overallResult = False
            else:
                statusMsg += "Field comp '%s' error within tol %g of %s"\
                    " solution.\n"\
                    % (field, fieldTol, self.compareSource)

        print statusMsg
        self._setStatus(overallResult, statusMsg)
        return overallResult

    def _checkFieldWithinTol(self, field, mResult):
        """ This is the core of the TC, checks a field from ModelResult against
        the expected.  Returns fieldResult (a True/False) and dofErrors (a list
        of float).

        If using reference model as comparison source, expected should be
        ReferenceResult/HighResReferenceResult, which behaves like a normal
        ModelResult, .getFieldAtStep() is used here.

        If expected is an analytic function (callable), it will call
        ModelResult.getPositions() and get expected values from func using the
        positions (a list of tuples).  It is user's responsibility to ensure the
        analytic function accepts the positions returned by
        ModelResult.getPositions().
        """
        import numpy as np
        def withinTol(tol, dofErrors):
            """Checks that the difference between the fields is within a given
            tolerance, at the final timestep."""
            for dofError in dofErrors:
                if dofError > tol: return False
            return True
        fieldTol = self._getTolForField(field)
        result = mResult.getFieldAtStep(field, self.testTimestep)
        if callable(self.expected):
            # analytic, calls func with position
            expected = np.array([self.expected(pos) for pos in mResult.getPositions()])
        else:
            # TODO: [Refactor] add support for HighResReferenceResult
            expected = self.expected.getFieldAtStep(field, self.testTimestep)
        dofErrors = calc_errors(expected, result)
        fieldResult = withinTol(fieldTol, dofErrors)
        return fieldResult, dofErrors

    def _writeXMLCustomSpec(self, specNode):
        etree.SubElement(specNode, 'testTimestep',
            value=str(self.testTimestep))
        etree.SubElement(specNode, 'compareSource',
            value=str(self.compareSource))
        fListNode = etree.SubElement(specNode, 'fields')
        for fName in self.fieldsToTest:
            fNode = etree.SubElement(fListNode, 'field', name=fName,
                tol=str(self._getTolForField(fName)))

    def _writeXMLCustomResult(self, resNode, mResult):
        frNode = etree.SubElement(resNode, 'fieldResultDetails')
        for fName in self.fieldsToTest:
            fieldTol = self._getTolForField(fName)
            fieldRes = self.fieldResults[fName]
            fieldNode = etree.SubElement(frNode, "field", name=fName)
            fieldNode.attrib['allDofsWithinTol'] = str(fieldRes)
            desNode = etree.SubElement(fieldNode, "dofErrors")
            for dofI, dofError in enumerate(self.fieldErrors[fName]):
                deNode = etree.SubElement(desNode, "dofError")
                deNode.attrib["num"] = str(dofI)
                deNode.attrib["error"] = "%6e" % dofError
                deNode.attrib["withinTol"] = str(dofError <= fieldTol)

# This is the same as used in AUT2's testing at the moment, but maybe there is a
# better way.
#
# TODO: do a literature research how to compare two set of values scientificly
def calc_errors(data1, data2, zero_tolerance=1.e-9):
    """ Calculates difference array between two listing tables.  For values
    of data1 with absolute value greater than zero_tolerance, this is the
    relative difference for each element (|(t1-t2)/t1|). Otherwise, this is
    the absolute difference (|t1-t2|).
    """
    import numpy as np
    diff = data1 - data2
    rdiff = np.abs(diff / data1)
    iz = np.where(np.abs(data1) <= zero_tolerance)
    rdiff[iz] = np.abs(diff[iz])
    return rdiff

