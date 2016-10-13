from xml.etree import ElementTree as etree
from .api import SingleRunTestComponent, CREDO_PASS, CREDO_FAIL
from .fieldWithinTolTC import calc_errors
import numpy

# TODO: this one is so similar to FieldWithinTolTC, should factor out a common
# base, dealing with all fields related things.  Only thing different is
# .testCellIndex, .times and ._checkFieldWithinTol()

class HistoryWithinTolTC(SingleRunTestComponent):
    """Checks whether, for a particular set of fields and a specified cell
    index, the error between history of each field and an (analytic or
    reference) solution is below a specificed tolerance.

    Other than those that are directly saved as attributes documented below,
    the constructor arguments of interest are:

    * expected: An expected solution in the form of a ModelResult
      (ReferenceResult, HighResReferenceResult) or a function (analytic
      solution).
    * testCellIndex: Integer, the index of the model output that the
      comparison will occur at.
    * times: A list of floats, times that the ModelResult will be interpolated
      onto.  If this is unspecified (None), it will use reference ModelResult's
      .getTimes(). If expected is a analytic function, this will be set to the
      model run's output times.

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
            testCellIndex=0,
            times=None
            ):
        SingleRunTestComponent.__init__(self, "historyWithinTol")
        self.fieldsToTest = fieldsToTest
        self.defFieldTol = defFieldTol
        self.fieldTols = fieldTols
        self.times = times
        # TODO: [Refactor] complete check with ModelResult and func
        if expected is None:
            raise ValueError("expected solution must be ModelResult or func.")
        if callable(expected):
            self.compareSource = 'analytic'
        else:
            # TODO: [Refactor] add support for HighResReferenceResult
            self.compareSource = 'reference'
        self.expected = expected
        self.testCellIndex = testCellIndex
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
            fieldResult, timesError = self._checkFieldWithinTol(field, mResult)
            self.fieldResults[field] = fieldResult
            self.fieldErrors[field] = timesError
            fieldTol = self._getTolForField(field)
            if not fieldResult:
                statusMsg += "Field comp '%s' error(s) of %s not within"\
                    " tol %g of %s solution\n"\
                    % (field, timesError, fieldTol, self.compareSource)
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
        the expected.  Returns fieldResult (a True/False) and timesError (a list
        of float).

        If using reference model as comparison source, expected should be
        ReferenceResult/HighResReferenceResult, which behaves like a normal
        ModelResult, .getFieldHistoryAtCell() is used here.

        If expected is an analytic function (callable), it will call
        ModelResult.getPositions() to find where the cell index is, and
        ModelResult.getTImes() for a series of times and get expected values
        from func using the positions and time (a position tuple and a time
        float).  It is user's responsibility to ensure the analytic function
        accepts the positions returned by (ModelResult.getPositions()[I], time).
        """
        import numpy as np
        def withinTol(tol, timesError):
            """Checks that the difference between the fields is within a given
            tolerance, at the final timestep."""
            for timeError in timesError:
                if timeError > tol: return False
            return True

        fieldTol = self._getTolForField(field)
        result = mResult.getFieldHistoryAtCell(field, self.testCellIndex)
        result_times = mResult.getTimes()

        if callable(self.expected):
            # analytic, calls func with position
            if self.times is None:
                self.times = result_times
            pos = mResult.getPositions()[self.testCellIndex]
            expected = np.array([self.expected(pos, t) for t in self.times])
            timesError = calc_errors(expected, result)
        else:
            expected = self.expected.getFieldHistoryAtCell(field, self.testCellIndex)
            expected_times = self.expected.getTimes()
            if self.times is None:
                self.times = self.expected.getTimes()
                interp_expected = expected
            else:
                interp_expected = numpy.interp(self.times, expected_times, expected)
            result = numpy.interp(self.times, result_times, result)
            timesError = calc_errors(interp_expected, result)

        fieldResult = withinTol(fieldTol, timesError)
        return fieldResult, timesError

    def _writeXMLCustomSpec(self, specNode):
        etree.SubElement(specNode, 'testCellIndex',
            value=str(self.testCellIndex))
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
            fieldNode.attrib['allTimesWithinTol'] = str(fieldRes)
            desNode = etree.SubElement(fieldNode, "timesError")
            for dofI, timeError in enumerate(self.fieldErrors[fName]):
                deNode = etree.SubElement(desNode, "timeError")
                deNode.attrib["num"] = str(dofI)
                deNode.attrib["error"] = "%6e" % timeError
                deNode.attrib["withinTol"] = str(timeError <= fieldTol)
