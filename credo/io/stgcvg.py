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

'''A Module for dealing with StGermain "Convergence" files, i.e. records of
comparison between a set of Fields and either reference or Analytic solutions,
produced by the FieldTester Component.

The module is not fully object-oriented, and in the current design allows for
the possibility of a set of cvg files in one path that should all be referenced.
(e.g. the see function :func:`genConvergenceFileIndex`).

It provides a similar, though not identical, interface to the
:mod:`credo.io.stgfreq` module.

The format of CVG files is space-separated, of the form:

* Header lines, which may be repeated throughout the file::

    #Res        FieldName1      FieldName2 ...

* Values lines, which are of the form::

    <len scale> <field value 1> <field value 2>

For example::

  #Res TemperatureField1 TemperatureField2
  1.000000e-01 6.16e-03 5.5e-2
  #Res TemperatureField1 TemperatureField2
  1.000000e-01 6.14e-03 5.4e-2
  #Res TemperatureField1 TemperatureField2
  1.000000e-01 6.12235812e-03 5.3e-2
'''

import os
import glob
import linecache

CVG_EXT='cvg'
CVG_HEADER_LINESTART='#'

class CVGReadError(IOError):
    """An exception for specifying problems reading an Underworld
    convergence file."""
    pass


class CvgFileInfo:
    '''A simple class to store info about what fields map to what
     convergence files. Currently implicit is the name of the Field,
     this is usually handled by storing CvgFileInfos in a dictionary,
     with the keys being Field names.

     .. attribute:: filename

        The filename (as a string) that the cvg info is stored in.

     .. attribute:: dofColMap

        A dictionary mapping for each degree of freedom of a field, the
        column number it is stored in in the cvg file.
     '''

    def __init__(self, filename):
        self.filename=filename
        self.dofColMap={}


def genConvergenceFileIndex(path):
    '''Returns a dictionary relating field names to :class:`CvgFileInfo`
    classes, after reading all .cvg files in the given path.'''

    # get list of all convergence files
    cvgFiles=glob.glob(os.path.join(path, "*."+CVG_EXT))

    cvgFileDict = {}

    # for each file, read first line, and check field name
    for cvgFilename in cvgFiles:
        # Store in a dict structure, so we know file, field
        cvgFile = open(cvgFilename,"r")
        line=cvgFile.readline()
        cols=line.split()
        for colIndex in range(1,len(cols)):
            fieldCol=cols[colIndex]
            # The Field name is written with a number appended, the field
            # Degree of freedom
            assert fieldCol[-1].isdigit()
            # The -1 is because of the way FieldTest adds 1 to these
            fieldName = fieldCol[:-1]
            dofValue = int(fieldCol[-1]) - 1
            if (fieldName not in cvgFileDict):
                newCvgInfo = CvgFileInfo(cvgFilename)
                newCvgInfo.dofColMap[dofValue] = colIndex
                cvgFileDict[fieldName] = newCvgInfo
            else:
                cvgFileDict[fieldName].dofColMap[dofValue] = colIndex

        cvgFile.close()

    return cvgFileDict

# TODO: the files below could perhaps be converted to an O-O representation,
# where operations are performed on a CVG file, and support e.g. slice notation?

def getCheckStepsRange(cvgFile, steps):
    """Checks that "steps" specified is valid for a given cvgFile (Python File),
    and if so converts it into a list of step numbers within the range
    specified. into a tuple of start and end values.
    If steps isn't valid, raises assertion.

    "steps" can be of the format:

    * The string "all", meaning a list from 0 to the last step number will
      be returned;
    * The string "last", meaning that a list containing only the last step
      number in the cvgFile will be returned;
    * A tuple of two step numbers (integers), in which case a list will
      be returned containing a range between the two steps (using Python's
      range() function).
    """
    lineTot = sum(1 for line in cvgFile)
    cvgFile.seek(0)

    # Given every 2nd line is a header
    stepTot = lineTot/2

    if steps == 'all':
        stepRange = range(0,stepTot)
    elif steps == 'last':
        stepRange = [stepTot-1]
    elif type(steps) == tuple:
        if len(steps) != 2 or type(steps[0]) != int or type(steps[1]) != int:
            raise TypeError("If arg 'steps' is a tuple, should be only two"\
                " numbers.")

        start,end = steps

        if start < 0:
            raise ValueError("Error, 'steps' init number less than 0")
        if end > stepTot:
            raise ValueError("Error, 'steps' finish number %d "\
                "greater than number of steps in the given file (%d)" % \
                (end, stepTot))

        stepRange = range(start,end)
    else:
        raise TypeError("arg 'steps' must be either 'all', 'last', or a tuple"\
            " of start and ending numbers")

    return stepRange

def _getLineValues(cvgFilename, stepNum):
    """Get all the values in the given step number in the filename given by
    cvgFilename. Returned as a list."""
    # Given every 2nd line is a header, need to handle these
    lineNum = stepNum*2+1
    # The linecache.getline function indexes file lines from 1, hence
    # adjustment below
    line = linecache.getline(cvgFilename, lineNum+1)
    if line == "":
        raise IOError("Couldn't read step %d (line %d) from '%s'" %
            (stepNum, lineNum, cvgFilename))
    elif line[0] == CVG_HEADER_LINESTART:
        # Should have avoided header lines
        raise IOError("Trying to read step %d (line %d) from '%s'"
            " unexpectedly indexed to a header line" %
            (stepNum, lineNum, cvgFilename))
    colValsStr = line.split()
    colVals = map(float, colValsStr)
    return colVals

def getDofErrorsForStep(cvgFileInfo, stepNum):
    """For the given :class:`CvgFileInfo` and step number, returns
    a list indexed by dof number of the error of each dof in that step.
    """

    colVals = _getLineValues(cvgFileInfo.filename, stepNum)

    dofErrorsForStep = []
    for dof, colIndex in cvgFileInfo.dofColMap.iteritems():
        try:
            dofError = colVals[colIndex]
        except IndexError:
            raise CVGReadError("Error, couldn't read expected error in"
                " column %d"\
                " from CVG file '%s'. Perhaps the model run had a parallel"\
                " I/O problem (see CREDO FAQ online for advice)." \
                % (colIndex, cvgFileInfo.filename))
        else:
            dofErrorsForStep.append(dofError)

    return dofErrorsForStep


def getRes(cvgFilename, steps='all'):
    """For a given cvg Filename, return the 'resolutions' (length scale)
    for the given set of steps, where "steps" is of the form documented
    in :func:`getCheckStepsRange`."""

    cvgFile = open(cvgFilename,"r")
    stepRange = getCheckStepsRange(cvgFile, steps)

    resResult = []

    if len(stepRange) == 1:
        resResult = _getLineValues(cvgFilename, stepRange[0])[0]
    else:
        for stepNum in stepRange:
            res = _getLineValues(cvgFilename, stepNum)[0]
            resResult.append(res)

    cvgFile.close()
    return resResult


# Question: should we use Numeric for this? - as performance for very large
#  CVG files could be a bit ordinary
def getDofErrors_ByDof(cvgFileInfo, steps='all'):
    """For a given cvgFileInfo, get the errors in the specified dof from
    the specified file, indexed primarily by Dof.
    The 'steps' arg can be either 'all' (for all timesteps), 'last',
    or a tuple specifying range (see :func:`getCheckStepsRange` for more).
    If only one step result is asked for, the dofs are returned as a
    simple 1D array, otherwise they're returned as a list."""

    cvgFile = open(cvgFileInfo.filename,"r")

    stepRange = getCheckStepsRange(cvgFile, steps)

    dofErrors = []
    numDofs = len(cvgFileInfo.dofColMap)
    for ii in range(numDofs): dofErrors.append([])

    if len(stepRange) == 1:
        dofErrors = getDofErrorsForStep(cvgFileInfo, stepRange[0])
    else:
        for stepNum in stepRange:
            dofErrorsStep = getDofErrorsForStep(cvgFileInfo, stepNum)
            for dofI in range(numDofs):
                dofErrors[dofI].append(dofErrorsStep[dofI])

    cvgFile.close()
    return dofErrors


def getDofErrors_ByStep(cvgFileInfo, steps='all'):
    """For a given :class:`CvgFileInfo`, return the errors in the
    cvgFileInfo's specified file - for the timestep range specified by
    `steps`, indexed primarily by Timestep.
    The `steps` arg can be either 'all' (for all timesteps), 'last',
    or a tuple specifying range (see :func:`getCheckStepsRange` for more).
    If only one step result is asked for, the dofs are returned as a
    simple 1D array."""

    cvgFile = open(cvgFileInfo.filename,"r")

    stepRange = getCheckStepsRange(cvgFile, steps)

    dofErrors = []
    numDofs = len(cvgFileInfo.dofColMap)

    if len(stepRange) == 1:
        dofErrors = getDofErrorsForStep(cvgFileInfo, stepRange[0])
    else:
        for stepNum in stepRange:
            dofErrorsStep = getDofErrorsForStep(cvgFileInfo, stepNum)
            dofErrors.append(dofErrorsStep)

    cvgFile.close()
    return dofErrors
