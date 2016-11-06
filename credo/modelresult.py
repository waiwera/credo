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

"""This module allows recording and post-processing of the results of running
a StGermain-based application.

The primary interface is via the :class:`~credo.modelrun.ModelRun` class.

.. seealso:: :mod:`credo.modelrun`."""

import os
import glob
from xml.etree import ElementTree as etree
import numpy as np

from credo.io import stgfreq
from credo.io.stgxml import writeXMLDoc
from credo.analysis import fields

class ModelResult(object):
    """ A (mostly abstract) base class that defines the common interface of
    various model results from different simulators.  The primary users of these
    interface is TestComponents, where a set of shared field values extraction
    mehtods allows TCs to be reused (for different simulators).

    I think I will start with a few new methods:
        .getFieldAtOutputIndex(field, outputIndex)
        .getPositions()

    Attribute .ordering_map is used to convert internal storage's element order to
    external order, which is used to make TestComponent able to compare
    different model results from different simulators (some of which may have
    dummy boundary elements).  .ordering_map should be a list of integers, indices
    point to internal element/block order, size and order matches other
    simulators it compared to.

    Attribute .fieldname_map is used to convert field names from the internal
    storage to external field names shared by different simulator.
    .fieldname_map should be a dictionary with keys of names used in TC, and
    values of names within the internal storage.  If not specified, default will
    be empty dictionary.  NOTE that only field names need *translation* need to
    be specified in the dictionary.  i.e. field name not in the keys will be
    left untouched.

    TODO: .ordering_map and .fieldname_map are both handled by subclass at the
    moment, should it be part of the ModelRun superclass?

    TODO: ??? Should I let the the ModelResult to handle the calculation of
    analytic solution?  That would allow the implementation of say volumetric
    averaging of analytic solution so it's comparable to FV element results.
    """
    def __init__(self, modelName, outputPath, ordering_map=None,
                 fieldname_map={}):
        super(ModelResult, self).__init__()

        self.modelName = modelName
        self.outputPath = outputPath # needed by jobrunner
        self.jobMetaInfo = None  # needed by jobrunner

        self.ordering_map = ordering_map
        self.fieldname_map = fieldname_map
        if self.fieldname_map is None:
            self.fieldname_map = {}

    def getFieldAtOutputIndex(self, field, outputIndex):
        try:
            field = self.fieldname_map[field]
        except KeyError:
            pass
        if callable(field):
            return field(self, outputIndex)
        else:
            return self._getFieldAtOutputIndex_(field, outputIndex)

    def _getFieldAtOutputIndex_(self, field, outputIndex):
        """ Returns a list of values of field variable, of all model's elements,
        in order.  If outputIndex is -1, it will be the last time step.  The
        returned values are preferably in the form of NumPy array.

        Sub-classes should implement _getFieldAtOutputIndex() instead of this.
        This is done to support element mapping, to make different simulators
        compatible (some with dummy element for boundary conditions to be mapped
        out).
        """
        # if self.fieldname_map is not None:
        #     field = self.fieldname_map[field]
        if self.ordering_map is None:
            return self._getFieldAtOutputIndex(field, outputIndex)
        else:
            orig = self._getFieldAtOutputIndex(field, outputIndex)
            if type(orig) == np.ndarray:
                return orig[self.ordering_map]
            else:
                return np.array([orig[i] for i in self.ordering_map])

    def _getFieldAtOutputIndex(self, field, outputIndex):
        """ Returns a list of values of field variable, of all model's elements,
        in order.  If outputIndex is -1, it will be the last time step.  The
        returned values are preferably in the form of NumPy array.
        """
        raise NotImplementedError("._getFieldAtOutputIndex()")

    def getFieldHistoryAtCell(self, field, cellIndex):
        try:
            field = self.fieldname_map[field]
        except KeyError:
            pass
        if callable(field):
            return field(self, cellIndex)
        else:
            return self._getFieldHistoryAtCell_(field, cellIndex)

    def _getFieldHistoryAtCell_(self, field, cellIndex):
        """ Returns history value of specified field at one of the model's
        element/cell.  Note the cellIndex will be mapped if self.ordering_map is
        specified at the construction of the model result.

        Sub-classes should implement _getFieldHistoryAtCell() instead of this.
        This is done to support element mapping, to make different simulators
        compatible (some with dummy element for boundary conditions to be mapped
        out).
        """
        # if self.fieldname_map is not None:
        #     field = self.fieldname_map[field]
        if self.ordering_map is None:
            return self._getFieldHistoryAtCell(field, cellIndex)
        else:
            orig = self._getFieldHistoryAtCell(field, self.ordering_map[cellIndex])
            if type(orig) == np.ndarray:
                return orig
            else:
                return np.array(orig)

    def _getFieldHistoryAtCell(self, field, cellIndex):
        """ Returns history value of specified field at one of the model's
        element/cell.  The returned values are preferred to be in the form of
        NumPy array.
        """
        raise NotImplementedError("._getFieldHistoryAtCell()")

    def getPositions(self):
        """ Returns a list of positions of all model's elements in order.

        Note the CREDO framework does not care what's in each of position
        object, as long as it's accepted by the analytic function created by the
        users.

        Sub-classes should implement _getFieldAtOutputIndex() instead of this.
        This is done to support element mapping, to make different simulators
        compatible (some with dummy element for boundary conditions to be mapped
        out).
        """
        if self.ordering_map is None:
            return self._getPositions()
        else:
            orig = self._getPositions()
            return [orig[i] for i in self.ordering_map]

    def _getPositions(self):
        """ Returns a list of positions of all model's elements in order.

        Note the CREDO framework does not care what's in each of position
        object, as long as it's accepted by the analytic function created by the
        users.
        """
        raise NotImplementedError("._getPositions()")

    def getTimes(self):
        """ Returns a numpy array of model result's output times.
        """
        times = self._getTimes()
        if type(times) == np.ndarray:
            return times
        else:
            return np.array(times)

    def _getTimes(self):
        """ Returns a numpy array of model result's output times.
        """
        raise NotImplementedError("._getTimes()")

    def writeRecordXML(self, outputDir="", filename="", prettyPrint=True):
        """Write an XML record of a :class:`.ModelResult`."""
        if filename == "":
            filename = 'ModelResult-' + self.modelName + '.xml'
        if outputDir == "":
            outputDir = self.outputPath

        # Write extra model results, e.g.
        # create model file
        # TODO: [Refactor] modified this from 'StgModelResult', check if okay
        mrNode = etree.Element(self.__class__.__name__)
        xmlDoc = etree.ElementTree(mrNode)
        etree.SubElement(mrNode, 'modelName').text = self.modelName
        etree.SubElement(mrNode, 'outputPath').text = self.outputPath
        if self.jobMetaInfo is not None:
            self.jobMetaInfo.writeInfoXML(mrNode)
        # if (self.fieldResults):
        #     fieldResultsNode = etree.SubElement(mrNode,
        #         fields.FieldComparisonResult.XML_INFO_LIST_TAG)
        #     for fieldResult in self.fieldResults:
        #         fieldResult.writeInfoXML(fieldResultsNode)

        # Write the files
        if not os.path.exists(outputDir): os.makedirs(outputDir)
        fullPath = os.path.join(outputDir, filename)
        outFile = open(fullPath, 'w')
        writeXMLDoc(xmlDoc, outFile, prettyPrint)
        outFile.close()
        return fullPath



class UnderworldModelResult(ModelResult):
    """A class to keep records about the results of a StgDomain/Underworld
     model run. These are normally produced as a result of running a
     :class:`~credo.modelrun.ModelRun`.

     .. note:: In future, we intend to add the ability to create a ModelResult
        class by reading in an XML file specifying output directory, etc.

     .. attribute:: modelName

        Name of the Model that was run.

     .. attribute:: outputPath

        Path to the output results the ModelRun produced.

     .. attribute:: jobMetaInfo

        A :class:`jobrunner.api.JobMetaInfo`, recording information about the
        run such as time taken, Memory usage etc (generally attached by a
        :class:`credo.jobrunner.api.JobRunner` soon after the
        ModelResult created).

     .. attribute:: fieldResults
     # TODO:[ Refactor] remove, StGermain specific

        A list of FieldComparisonResult objects.

        .. note:: is a legacy of early design of CREDO to allow construction of
           XML files from pre-existing sys test scripts, may be removed soon.

     .. attribute:: freqOutput
     # TODO:[ Refactor] *maybe* remove, StGermain specific, but could be similar
     # for time stepping etc.

        Initially `None`, if :meth:`.readFrequentOutput` is called, this will
        be populated with a reference to a :class:`credo.io.stgfreq.FreqOutput`
        class, to allow post-processing of info in the Frequent Output file
        saved as part of the model run.

     """

    XML_INFO_TAG = 'StgModelResult'

    def __init__(self, modelName, outputPath):
        self.modelName = modelName
        self.outputPath = outputPath
        self.jobMetaInfo = None
        self.fieldResults = []
        self.freqOutput = None

    def readFrequentOutput(self):
        """Opens and reads in info from the Frequent Output file produced
        as part of the run, and saves to the attribute :attr:`.freqOutput`.

        .. seealso: :class:`credo.io.stgfreq.FreqOutput` for info on how to
           use this attribute once created."""
        self.freqOutput = stgfreq.FreqOutput(self.outputPath)

    # TODO: is this function still appropriate?
    def recordFieldResult(self, fieldName, tol, errors):
        '''Records the info required for a FieldResult in the array of
         stored FieldResults kept by the ModelResult. Returns a reference
         to the just-added FieldResult.'''
        fieldResult = fields.FieldComparisonResult(fieldName, errors)
        self.fieldResults.append(fieldResult)
        return fieldResult

    def defaultRecordFilename(self):
        """Get the default filename to use, based on the model name of a
        particular model."""
        return 'ModelResult-' + self.modelName + '.xml'

    def writeRecordXML(self, outputDir="", filename="", prettyPrint=True):
        """Write an XML record of a :class:`.ModelResult`."""
        if filename == "":
            filename = self.defaultRecordFilename()
        if outputDir == "":
            outputDir = self.outputPath

        # Write extra model results, e.g.
        # create model file
        mrNode = etree.Element(self.XML_INFO_TAG)
        xmlDoc = etree.ElementTree(mrNode)
        etree.SubElement(mrNode, 'modelName').text = self.modelName
        etree.SubElement(mrNode, 'outputPath').text = self.outputPath
        if self.jobMetaInfo is not None:
            self.jobMetaInfo.writeInfoXML(mrNode)
        if (self.fieldResults):
            fieldResultsNode = etree.SubElement(mrNode,
                fields.FieldComparisonResult.XML_INFO_LIST_TAG)
            for fieldResult in self.fieldResults:
                fieldResult.writeInfoXML(fieldResultsNode)

        # Write the files
        if not os.path.exists(outputDir): os.makedirs(outputDir)
        fullPath = os.path.join(outputDir, filename)
        outFile = open(fullPath, 'w')
        writeXMLDoc(xmlDoc, outFile, prettyPrint)
        outFile.close()
        return fullPath

    def readFromRecordXML(self, xmlFilename):
        # parse in doc
        xmlDoc = etree.parse(xmlFilename)
        root = xmlDoc.getroot()
        assert root.tag == self.XML_INFO_TAG
        self.modelName = root.find('modelName').text
        self.outputPath = root.find('outputPath').text
        jmiNode = root.find('jobMetaInfo')
        #TODO: temporarily put import in here to avoid cyclic import
        import credo.jobrunner
        self.jobMetaInfo = credo.jobrunner.readJobMetaInfoFromXMLNode(jmiNode)
        # TODO: here we would also read analysisOp results, if they were
        #  being recorded.

def readModelResultFromPath(path):
    xmlFiles = glob.glob(os.path.join(path, "ModelResult*.xml"))
    if len(xmlFiles) != 1:
        raise ValueError("Expected directory to only contain 1 ModelResult"\
            " XML file, but it contained %d." % len(xmlFiles))
    recordFile = xmlFiles[0]
    mRes = ModelResult("place", path)
    mRes.readFromRecordXML(recordFile)
    return mRes

#####

def getSimInfoFromFreqOutput(outputPath):
    """utility function to get basic information about the simulation
    from the FrequentOutput.dat, given a particular output Path.

    .. seealso:: :mod:`credo.io.stgfreq`."""

    freqOut = stgfreq.FreqOutput(path=outputPath)
    freqOut.populateFromFile()
    recordDict = freqOut.getRecordDictAtStep(freqOut.finalStep())
    tSteps = freqOut.finalStep()
    try:
        simTime = recordDict['Time']
    except KeyError:
        # For now, allow none as simTime
        simTime = None
    return tSteps, simTime

######

# TODO: not sure if below approach to operate on ModelResult XML directly is best ....
#  Maybe it would be better to "unpickle" a ModelResult from XML, and then modify
#  directly, then write out to file again.

def updateModelResultsXMLFieldInfo(filename, newFieldResult, prettyPrint=True):
    """Update an existing XML record of a :class:`.ModelResult` with info
    about a particular fieldResult."""
    assert filename != ""

    xmlDoc = etree.parse(filename)
    root = xmlDoc.getroot()

    # Because we just grabbed a reference to the root, the find will
    # look relative to the root
    fieldResultsNode = xmlDoc.find(fields.FieldComparisonResult.XML_INFO_LIST_TAG)
    # It may not exist, if there were no field results already,
    # in which case grab existing
    if fieldResultsNode is None:
        fieldResultsNode = etree.SubElement(root,
            fields.FieldComparisonResult.XML_INFO_LIST_TAG)
    else:
        # TODO: Check the field to add is not in the list already
        pass

    newFieldResult.writeInfoXML(fieldResultsNode)

    # Write the file, default name if filename provided is empty
    outFile = open(filename, 'w')
    writeXMLDoc(xmlDoc, outFile, prettyPrint)
    outFile.close()
