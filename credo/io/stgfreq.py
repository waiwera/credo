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

'''A Module for convenient access to StGermain FrequentOutput files.

Primary construct is the FreqOutput class, which once constructed has numerous
methods to access data from a FrequentOutput file.
'''
from __future__ import division
from __future__ import print_function
from builtins import object
from past.utils import old_div

import os
import operator

STG_DEF_FREQ_FILENAME='FrequentOutput.dat'
FREQ_HEADER_LINESTART='#'

class FreqOutput(object):
    '''A simple class to store information about a frequent output file,
    and make it accessible. Once passed a filename of a FrequentOutput file
    in it's constructor, has methods to get information and values from
    that named file.

    The FrequentOutput file can be either "cached" into memory using
    the :meth:`populateFromFile()` function so subsequent access
    is quick, or else
    calling an access function directly such as
    :meth:`getRecordDictAtStep()` will
    automatically populate the data cache for you behind the scenes.

    Key attributes:

    .. attribute:: populated

       Bool, states whether the class's data structures have been populated
       from file, shouldn't be modified externally.

    .. attribute:: headerColMap

       dict, mapping header names in the FrequentOutput to the column number
       they occupy in the file.

    '''

    def __init__(self, path, filename=STG_DEF_FREQ_FILENAME):
        self.path = path
        self.filename = filename
        fullFilename = os.path.join(path, filename)
        if not os.path.exists(fullFilename):
            raise ValueError("Error, the path and filename passed in, '%s' "
                " and '%s', does not point to a valid freq output file."
                % (path, filename))
        self.populated = False
        self.headers = None
        self.headerColMap = {}
        self.records = None
        self.tStepMap = {}
        self._finalTimeStep = None
        try:
            self.file = open(fullFilename, "r")
        except IOError:
            # TODO: create a new exception class for this?
            raise IOError("Freq output file '%s' unable to be opened."
                " Possibly the relevant ModelRun didn't have one enabled."
                % (fullFilename))

    def populateFromFile(self):
        """This function will read all essential data from the FrequentOutput
        file associated with the class into data structures in memory, for fast
        subsequent access. Saves the fact that this has occurred so it doesn't
        neeed to be repeated in future."""
        self.getHeaders()
        self.getAllRecords()
        self.getTimestepMap()
        self.populated = True

    def getHeaders(self):
        """Read the headers from the associated FrequentOutput file, populate
        attr:`headerColMap`, and return the names of the headers
        as a list."""
        if not self.populated:
            self.file.seek(0)
            firstLine = self.file.readline()
            assert(firstLine[0]) == FREQ_HEADER_LINESTART
            firstLine = firstLine[1:]
            headers = firstLine.split()
            self.headers = headers
            for hI, header in enumerate(headers):
                self.headerColMap[header] = hI
        return self.headers

    def getTimestepMap(self):
        """Calculate a map of timestep number of model, to record number in the
        FrequentOutput file - stores this, and returns a reference to it.

        This is important especially if the FrequentOutput has been sampled from
        the model at a timstep frequency less than 1."""

        if not self.populated:
            self.file.seek(0)
            # First line should be headers, skip
            firstLine = self.file.readline()
            assert(firstLine[0]) == FREQ_HEADER_LINESTART
            # need to do this rather than just enumerate because
            # of possible duplicate header lines
            recordNum = 0
            for lineNum, line in enumerate(self.file):
                # See comment above in getAllRecords
                if line[0] == FREQ_HEADER_LINESTART:
                    continue
                tstep = int(line.split()[0])
                self.tStepMap[tstep] = recordNum
                recordNum+=1
        return self.tStepMap

    def getAllRecords(self):
        """Get all records of timestep information from the associated
        FrequentOutput file.

        Records are stored in an array, where each entry is of the form
        of a list of floats of the records at that timestep. Thus likely
        needs to be used in conjunction with other functions to access the
        data itself by header name, ie the self.headerColMap.

        Saves this as self.records, and returns a reference to it.
        (Also populates the self._finalTimeStep attribute.)"""
        if not self.populated:
            self.file.seek(0)
            self.headers = self.getHeaders()
            tStepCol = self.headerColMap['Timestep']
            self.records = []
            for line in self.file:
                if line[0] == FREQ_HEADER_LINESTART:
                    # Currently, on restart runs it will re-add a header to
                    # Freq out, so ignore this
                    continue
                recordValues = line.split()
                # We are assuming all freq output values are floats.
                # Might be better
                # to actually record the data type in the headers somehow?
                recordValueNums = [float(val) for val in recordValues]
                # For now, manually convert tstep specially to int.
                recordValueNums[0] = int(recordValueNums[tStepCol])
                self.records.append(recordValueNums)
        self._finalTimeStep = (self.records[-1])[tStepCol]
        return self.records

    def getRecordDictAtStep(self, tstep):
        """For a given timestep tstep, looks up the records for that timestep
        and returns a dictionary of "headername":recordVal mappings, where
        headername is the name of each header in the FrequentOutput file, and
        recordVal is the value of that property at the requested timestep."""

        if not self.populated: self.populateFromFile()
        record = self.getRecordAtStep(tstep)
        recordDict = {}
        for header, col in list(self.headerColMap.items()):
            recordDict[header] = record[col]
        return recordDict

    def getRecordDictAtFinalStep(self):
        """Utility wrapper function to get a dictionary of records in
        the FreqOutput at the final timestep - see :attr:`.getRecordDictAtStep`
        ."""
        if not self.populated: self.populateFromFile()
        return self.getRecordDictAtStep(self._finalTimeStep)

    def finalStep(self):
        """Returns the highest timestep number that has information recorded for
        it in the associated FrequentOutput file."""
        if not self.populated: self.populateFromFile()
        return self._finalTimeStep

    def getValueAtStep(self, headerName, tstep):
        """Gets the values of a property given by 'headerName', at a specified
        timestep 'tstep'."""

        if not self.populated:
            # We will take the approach that you should always populate the
            # info for fast access. If memory were really a concern, could use
            # algorithms and/or read file line-by-line until (if) correct
            # timestep's data found.
            self.populateFromFile()
        colNum = self.getColNum(headerName)
        record = self.getRecordAtStep(tstep)
        value = record[colNum]
        return value

    def getRecordNum(self, tstep):
        """Gets the record number in the FrequentOutput file of a given
        timestep. E.g. in a FrequentOutput file where values were saved
        every 5 timesteps, then the 15th timestep will map to the 3rd record."""
        if not self.populated: self.populateFromFile()
        try:
            recordNum = self.tStepMap[tstep]
        except KeyError:
            tSteps = list(self.tStepMap.keys())
            raise ValueError("Error, timestep at which to get value, %d,"
                " doesn't exist in this Frequent output file (valid range is"
                " (%d-%d)." % (tstep, min(tSteps), max(tSteps)))
        return recordNum

    def getRecordAtStep(self, tstep):
        """Gets the record (in raw form, see getAllRecords) at a given
        timestep, and returns."""
        if not self.populated: self.populateFromFile()
        assert self.records
        recordNum = self.getRecordNum(tstep)
        record = self.records[recordNum]
        return record

    def getColNum(self, headerName):
        """Get the column number in the record data structure/FrequentOutput
        file itself - associated with a particular header name."""
        try:
            colNum = self.headerColMap[headerName]
        except KeyError:
            raise ValueError("Error, header to get value of, '%s', doesn't"
                " exist in this Frequent output file. Valid headers are"
                " %s" % (headerName, list(self.headerColMap.keys())))
        return colNum

    def getValuesArray(self, headerName, range="all"):
        """Returns an array of all values over time for the property defined by
        "headerName" in the associated FrequentOutput file.

        .. note::

           the "range" parameter is not yet operational and should be
           ignored for now.
        """
        if not self.populated: self.populateFromFile()
        # TODO: Check range input is ok. I need to find out the right way to
        # handling unusual values for these
        recordsSet = self.records
        colNum = self.getColNum(headerName)
        valArray = []
        for record in recordsSet:
            valArray.append(record[colNum])
        return valArray

    def getTimeStepsArray(self, range="all"):
        """Returns an array of all timestep numbers
        that have records saved in the associated FrequentOutput file.

        .. note::

           the "range" parameter is not yet operational and should be
           ignored for now.
        """
        if not self.populated: self.populateFromFile()
        # TODO: Check range input is ok. I need to find out the right way to
        # handling unusual values for these
        colNum = self.getColNum('Timestep')
        tSteps = [record[colNum] for record in self.records]
        return tSteps

    def getMin(self, headerName):
        '''get the Minimum of the records for a given header, including
        the timestep at which that minimum occured.'''
        return self.getReductionOp(headerName, minOp)

    def getMax(self, headerName):
        '''get the Maximum of the records for a given header, including
        the timestep at which that minimum occured.'''
        return self.getReductionOp(headerName, maxOp)

    def getMean(self, headerName):
        '''gets the Mean of the records for a given header.

        .. note::

           this is provided for convenience. If user wants to do more complex
           statistical operations, use the getValuesArray, then process this
           directly using stats functions/libraries.'''
        if not self.populated: self.populateFromFile()
        valArray = self.getValuesArray(headerName)
        return old_div(sum(valArray, 0.0), len(valArray))

    def getClosest(self, headerName, targVal):
        """Gets the closest value and timestep to the given value."""
        return self.getReductionOp(headerName, closestToVal, targVal=targVal)

    def printAllMinMax(self):
        '''Print the maximum and minimum values of all fields in the frequent
        output.'''
        if not self.populated: self.populateFromFile()
        print("Maximum and minimum values for quantities in Frequent Output:")
        for header in self.headers:
            if header == 'Timestep': continue
            min, minStep = self.getMin(header)
            max, maxStep = self.getMax(header)
            print("\t%s: min %f (at step %d), max %f (at step %d)"\
                % (header, min, minStep, max, maxStep))

    def getReductionOp(self, headerName, reduceFunc, **kwargs):
        '''Utility function for doing comparison operations on the records
        list, e.g. the max or minimum - where reduceFunc can operate on the
        whole records list at once, and support the "key" syntax to pick
        correct field out of tuples for comparison.

        .. note:: This has been written to allow both standard Python
           'reduction ops' like `max()` and `min()`, and also more complex
           operators defined in this module, or by the user.
        '''
        if not self.populated: self.populateFromFile()
        if len(self.records) == 0: return None, None
        colNum = self.getColNum(headerName)
        tStepColNum = self.getColNum('Timestep')
        # Note passing in a couple of specific keywords first - see docstring
        retRecord = reduceFunc(self.records,
            key=operator.itemgetter(colNum), stgFreq=self, **kwargs)
        return retRecord[colNum], retRecord[tStepColNum]

    def getComparisonOp(self, headerName, cmpFunc):
        '''Utility function for doing comparison operations on the records
        list, e.g. the max or minimum - where cmpFunc is a single operator'''
        if not self.populated: self.populateFromFile()
        if len(self.records) == 0: return None, None
        colNum = self.getColNum(headerName)
        tStepColNum = self.getColNum('Timestep')
        firstRec = self.records[0]
        retVal, retStep = firstRec[colNum], firstRec[tStepColNum]
        for record in self.records:
            if cmpFunc(record[colNum], retVal):
                retVal, retStep = record[colNum], record[tStepColNum]
        return retVal, retStep

    def plotOverTime(self, headerName, depName='Timestep', show=False, save=True, path="."):
        """Plot the value of property given by 'headerName', against parameter
        'depName', which defaults to 'Timestep'.

        .. note::

            Use of this function requires the Python library matplotlib to be
            installed.

        The argument "show" enables whether the graph is to be immediately shown
        interactively, and "save" if it should be saved. If "save" is true, the
        "path" parameter determines the path the resulting plot file will
        be saved under.
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
        except ImportError:
            print("Error, to use CREDO built-in plot functions, please "\
                " install the matplotlib python library.")
            return

        if not self.populated: self.populateFromFile()
        valuesArray = self.getValuesArray(headerName)
        depArray = self.getValuesArray(depName)

        plot = plt.clf()   # Start by clearing any pre-existing figure
        plt.plot(depArray, valuesArray)
        plt.xlabel(depName)
        plt.ylabel(headerName)
        plt.title("Output parameter '%s' against %s"\
            % (headerName, depName))

        if save:
            filename = os.path.join(path, headerName+"-timeSeries.png")
            if not os.path.exists(path):
                os.makedirs(path)
            plt.savefig(filename, format="png")
        if show: plt.show()
        return plt

def maxOp(inList, key, stgFreq):
    return max(inList, key=key)

def minOp(inList, key, stgFreq):
    return min(inList, key=key)

def firstOp(inList, key, stgFreq):
    """A utility function designed to pass to
    attr:`~.FreqOutput.getReductionOp` for getting the first value from a
    frequent output list."""
    return inList[0]

def lastOp(inList, key, stgFreq):
    """A utility function designed to pass to
    attr:`~.FreqOutput.getReductionOp` for getting the last value from a
    frequent output list."""
    return inList[-1]

def closestToStep(inList, key, stgFreq, targStep):
    """Utilitiy function for use with attr:`~.FreqOutput.getReductionOp`:
    Gets the value at a given timestep.

    :keyword target: the target timestep."""
    assert stgFreq != None
    return closestToVal(inList, key, stgFreq, targVal=targStep,
        targObsName='Timestep')

def closestToSimTime(inList, key, stgFreq, targTime):
    """Utilitiy function for use with attr:`~.FreqOutput.getReductionOp`:
    Gets the value at a given timestep.

    :keyword target: the target simulation time."""
    assert stgFreq != None
    return closestToVal(inList, key, stgFreq, targVal=targTime,
        targObsName='Time')

def closestToVal(inList, key, stgFreq, targVal, targObsName=None):
    """Utilitiy function for use with attr:`~.FreqOutput.getReductionOp`:
    Gets the entry where the value of chosen observable (eg VRMS) is closest
    to a target value.

    :keyword targVal: the target observable value.
    :keyword targObsName: the target header to check value at. If `None`,
       then use the same as for the observable we'll return.
    """
    if targObsName != None:
        colNum = stgFreq.getColNum(targObsName)
        key=operator.itemgetter(colNum)

    closestVal = key(inList[0])
    closestRec = inList[0]
    diff = abs(closestVal - targVal)
    if len(inList) == 1: return closestVal
    for listEntry in inList[1:]:
        eVal = key(listEntry)
        newDiff = abs(eVal - targVal)
        if newDiff < diff:
            diff = newDiff
            closestVal = eVal
            closestRec = listEntry
    return closestRec
