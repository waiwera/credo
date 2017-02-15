from xml.etree import ElementTree as etree
from .api import SingleRunTestComponent, CREDO_PASS, CREDO_FAIL

import numpy

# TODO: do a literature research how to compare two set of values scientificly
def calc_errors(data1, data2, abs_err_tol=1.0e-9):
    """ Calculates difference array between two numpy 1-d arrays.  For values of
    data1 with absolute value greater than abs_err_tol, this is the relative
    difference for each element (|(t1-t2)/t1|). Otherwise, this is the absolute
    difference (|t1-t2|).
    """
    diff = data1 - data2
    # ignore divide by zero error, replace values with small data1 after
    # see http://stackoverflow.com/a/35696047/2368167
    with numpy.errstate(divide='ignore', invalid='ignore'):
        rdiff = numpy.abs(diff / data1)
    # replace where value < abs_err_tol with absolute error
    iz = numpy.where(numpy.abs(data1) <= abs_err_tol)
    rdiff[iz] = numpy.abs(diff[iz])
    # if there is any more -inf inf NaN, use absolute error
    iz = numpy.where(~numpy.isfinite(rdiff))
    rdiff[iz] = numpy.abs(diff[iz])
    return rdiff

def non_dimensionalise(x1, x2, abs_err_tol=1.0, logscale=False):
    """ Given two lists of numeric values, scales elements of both lists to be
    between 0.0 and 1.0.  If the range of values is smaller than abs_err_tol,
    typically 1.0, the data sets will be shifted down to 0.0, but scale remains.
    """
    xmin = min(min(x1), min(x2))
    xmax = max(max(x1), max(x2))
    if logscale:
        from math import log10
        xmin0 = xmin
        def log_transform(x): return log10(x - xmin0 + 1.)
        x1 = [log_transform(x) for x in x1]
        x2 = [log_transform(x) for x in x2]
        xmin = log_transform(xmin)
        xmax = log_transform(xmax)
    xd = xmax - xmin
    if xd < abs_err_tol:
        x1 = [x - xmin for x in x1]
        x2 = [x - xmin for x in x2]
        xmin, xmax, xd = 0.0, 1.0, 1.0
    xx1 = [(x - xmin)/xd for x in x1]
    xx2 = [(x - xmin)/xd for x in x2]
    return xx1, xx2

def calc_dist_errors(ptx, pty, linex, liney, abs_err_tol=1.0,
                     logx=False, logy=False):
    """ Calculates non-dimensionalised distance (errors) of points to a polyline
    (curve).

    The x-y space is non-dimensionalised before the calculation so the errors
    are normalised errors.  The second set of x/y is the polyline.  Errors are
    calculated from each of the points in the first x/y set.  Generally the
    polyline (second set) should have more points.
    """
    from shapely.geometry import Point, LineString
    # non-dimensionalise both data sets
    ptxx, linexx = non_dimensionalise(ptx, linex, abs_err_tol, logx)
    ptyy, lineyy = non_dimensionalise(pty, liney, abs_err_tol, logy)
    line = LineString([(x,y) for x,y in zip(linexx, lineyy)])
    return [Point(x,y).distance(line) for x,y in zip(ptxx, ptyy)]

class BaseWithinTolTC(SingleRunTestComponent):
    """Checks whether, for a particular set of fields and a specified cell
    index, the error between history of each field and an (analytic or
    reference) solution is below a specificed tolerance.

    NOTE this is an abstract class that needs to be impleted.

    Other than those that are directly saved as attributes documented below,
    the constructor arguments of interest are:

    * expected: An expected solution in the form of a ModelResult
      (ReferenceResult, HighResReferenceResult) or a function (analytic
      solution).

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

    .. attribute:: absoluteErrorTol

       For values of the expected result with absolute value greater than
       absoluteErrorTol, relative difference will be used (|(t1-t2)/t1|).
       Otherwise, absolute difference (|t1-t2|) will be used.  The default
       value of this tolerance is 1.0.

    """
    def __init__(self, fieldsToTest=None,
            defFieldTol=0.01,
            fieldTols=None,
            expected=None,
            absoluteErrorTol=1.0
            ):
        SingleRunTestComponent.__init__(self, self.__class__.__name__)
        self.fieldsToTest = fieldsToTest
        self.defFieldTol = defFieldTol
        self.fieldTols = fieldTols
        self.absoluteErrorTol = absoluteErrorTol
        self.expected = expected
        if expected is None:
            raise ValueError("expected solution must be ModelResult or func.")
        if callable(expected):
            self.compareSource = 'analytic'
        else:
            # TODO: [Refactor] add support for HighResReferenceResult
            self.compareSource = 'reference'
        self.fieldResults = {}
        self.fieldErrors = {}

    def preRunOps(self, modelRun):
        """ Implement pre-processing required for ModelRun object """
        pass

    def postRunOps(self, modelRun):
        """ Implement post-processing required for ModelRun object, before
        .check() """
        # TODO: add this into base class
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
            fieldResult, errors = self._checkFieldWithinTol(field, mResult)
            self.fieldResults[field] = fieldResult
            self.fieldErrors[field] = errors
            fieldTol = self._getTolForField(field)
            if not fieldResult:
                failed = [(i,e) for i,e in enumerate(errors) if e > fieldTol]
                failed_indices, failed_errors = zip(*failed)
                max_error = max(failed_errors)
                statusMsg += "Field comp '%s' has failed error(s) of %s at"\
                    " indices %s not within tol %g of %s solution\n"\
                    % (field, list(failed_errors), list(failed_indices), fieldTol, self.compareSource)
                # statusMsg += "Field comp '%s' error(s) of %s not within"\
                #     " tol %g of %s solution\n"\
                #     % (field, errors, fieldTol, self.compareSource)
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
        the expected.  Returns fieldResult (a True/False) and errors (a list
        of float).
        """
        msg = "._checkFieldWithinTol() not implemented in %s" % self.__class__.__name__
        raise NotImplementedError(msg)

    def _writeXMLCustomSpec(self, specNode):
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
            fieldNode.attrib['allErrorsWithinTol'] = str(fieldRes)
            desNode = etree.SubElement(fieldNode, "errors")
            for idx, error in enumerate(self.fieldErrors[fName]):
                deNode = etree.SubElement(desNode, "error")
                deNode.attrib["index"] = str(idx)
                deNode.attrib["error"] = "%6e" % error
                deNode.attrib["withinTol"] = str(error <= fieldTol)

    # TODO: make this obsolete
    def attachOps(self, modelRun):
        # TODO: [Refactor] interface to remove or changed to pre-run blah.
        """Implements base class
        :meth:`credo.systest.api.SingleRunTestComponent.attachOps`."""
        self.preRunOps(modelRun)

class HistoryWithinTolTC(BaseWithinTolTC):
    """
    Additional arguments compared to the base class:

    * testCellIndex: Integer, the index of the model output that the
      comparison will occur at.

    * times: A list of floats, times that the ModelResult will be interpolated
      onto.  If this is unspecified (None), it will use reference ModelResult's
      .getTimes(). If expected is a analytic function, this will be set to the
      model run's output times.  NOTE, this should not be specified in general,
      the attribute will contain the times error was calculated when test
      finished, which is useful for plotting.

    * orthogonalError: if set to True, error will be non-dimensionalised
      distance (from expected data points) to curve (polyline from model
      result).  Otherwise the default error is between the expected data points
      to interpolated model results.  Orthorgonal error is particularly useful
      if the expected model results are digitised points from plots in print.

    """
    def __init__(self,
                 fieldsToTest=None,
                 defFieldTol=0.01,
                 fieldTols=None,
                 expected=None,
                 absoluteErrorTol=1.0,
                 testCellIndex=0,
                 times=None,
                 orthogonalError=False,
                 enforceLogic=True ):
        BaseWithinTolTC.__init__(self,
                                 fieldsToTest=fieldsToTest,
                                 defFieldTol=defFieldTol,
                                 fieldTols=fieldTols,
                                 expected=expected,
                                 absoluteErrorTol=absoluteErrorTol )
        self.testCellIndex = testCellIndex
        self.times = times
        self.orthogonalError = orthogonalError

        # avoid doing stupid comparison (raise exception)
        # - analytical always use result times (NO times allowed)
        # - analytical solution cannot use curve fitting
        # - curve fitting do not use interpolation (No times allowed)
        # - simple error, times use either expected times or specified times
        if enforceLogic:
            if self.times is not None:
                raise Exception("There is no need to specify times in common tests.")
            if callable(self.expected):
                if self.orthogonalError is True:
                    raise Exception("Comparison with analytic solution cannot use orthorgonal erroes.")

    def _checkFieldWithinTol(self, field, mResult):
        """ This is the core of the TC, checks a field from ModelResult against
        the expected.  Returns fieldResult (a True/False) and errors (a list
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
        fieldTol = self._getTolForField(field)
        result = mResult.getFieldHistoryAtCell(field, self.testCellIndex)
        result_times = mResult.getTimes()

        if callable(self.expected):
            # analytic, calls func with position
            if self.times is None:
                self.times = result_times
            pos = mResult.getPositions()[self.testCellIndex]
            expected = numpy.array([self.expected(pos, t) for t in self.times])
            expected_times = self.times
        else:
            expected = self.expected.getFieldHistoryAtCell(field, self.testCellIndex)
            expected_times = self.expected.getTimes()
            if self.times is None:
                self.times = expected_times

        if self.orthogonalError:
            errors = calc_dist_errors(expected_times, expected,
                                      result_times, result,
                                      self.absoluteErrorTol)
        else:
            # expected/result needs to have the same length here (self.times)
            expected = numpy.interp(self.times, expected_times, expected)
            expected_times = self.times
            result = numpy.interp(self.times, result_times, result)
            result_times = self.times
            # TODO: check if interp is actually skipped if times matched
            errors = calc_errors(expected, result, self.absoluteErrorTol)

        fieldResult = all(e <= fieldTol for e in errors)
        return fieldResult, errors

    def _writeXMLCustomSpec(self, specNode):
        etree.SubElement(specNode, 'testCellIndex',
            value=str(self.testCellIndex))
        BaseWithinTolTC._writeXMLCustomSpec(self, specNode)

class FieldWithinTolTC(BaseWithinTolTC):
    """
    Additional arguments compared to the base class:

    * testOutputIndex: Integer, the index of the model output that the
      comparison will occur at.  If -1, means the final result.
    """
    def __init__(self,
                 fieldsToTest=None,
                 defFieldTol=0.01,
                 fieldTols=None,
                 expected=None,
                 absoluteErrorTol=1.0,
                 testOutputIndex=-1 ):
        BaseWithinTolTC.__init__(self,
                                 fieldsToTest=fieldsToTest,
                                 defFieldTol=defFieldTol,
                                 fieldTols=fieldTols,
                                 expected=expected,
                                 absoluteErrorTol=absoluteErrorTol )
        self.testOutputIndex = testOutputIndex

    def _checkFieldWithinTol(self, field, mResult):
        """ This is the core of the TC, checks a field from ModelResult against
        the expected.  Returns fieldResult (a True/False) and errors (a list
        of float).

        If using reference model as comparison source, expected should be
        ReferenceResult/HighResReferenceResult, which behaves like a normal
        ModelResult, .getFieldAtOutputIndex() is used here.

        If expected is an analytic function (callable), it will call
        ModelResult.getPositions() and get expected values from func using the
        positions (a list of tuples).  It is user's responsibility to ensure the
        analytic function accepts the positions returned by
        ModelResult.getPositions().
        """
        fieldTol = self._getTolForField(field)
        result = mResult.getFieldAtOutputIndex(field, self.testOutputIndex)

        if callable(self.expected):
            # analytic, calls func with position
            expected = numpy.array([self.expected(pos) for pos in mResult.getPositions()])
        else:
            # TODO: [Refactor] add support for HighResReferenceResult
            expected = self.expected.getFieldAtOutputIndex(field, self.testOutputIndex)
        errors = calc_errors(expected, result, self.absoluteErrorTol)

        fieldResult = all(e <= fieldTol for e in errors)
        return fieldResult, errors

    def _writeXMLCustomSpec(self, specNode):
        etree.SubElement(specNode, 'testOutputIndex',
            value=str(self.testOutputIndex))
        BaseWithinTolTC._writeXMLCustomSpec(self, specNode)

