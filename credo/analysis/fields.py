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


"""CREDO functions and classes for doing analysis of Fields in StGermain-based
codes.

Currently this is primarily based on the FieldTest component/plugin within
StgFEM, which allows comparison between one or more Fields in a model run (eg
"VelocityField"), and either saved reference fields, or analytic solutions.

The CREDO Field functions allow either single-model comparisons, e.g. those
defined by :class:`.FieldComparisonOp`, or analysis on fields to be performed
across multiple runs, e.g. :func:`~calcFieldCvgWithScale`.

.. Note::
   In future it's planned to add functions that load a checkpointed field result
   into Python for further analysis, but this feature is not yet implemented.
"""

import os
import math
from xml.etree import ElementTree as etree

import credo.io.stgpath as stgpath
from credo.analysis import AnalysisOperation
from credo.io import stgxml, stgcvg
import credo.analysis.stats as stats

class FieldComparisonOp:
    '''Class for setting up and performing a comparison between two Fields.
    Currently uses the functionality of the FieldTest component in StgFEM,
    and requires using a :class:`FieldComparisonList` to run a group of
    FieldComparisons at once (this is as a result of the structure of the
    FieldTest component).
    
    .. attribute:: name
    
       name of the field that is being compared (to an analytic or ref soln).
    '''

    def __init__(self, fieldName):
        self.name = fieldName

    def writeInfoXML(self, parentNode):
        '''Writes info about a comparison op: currently assumes will be called
        by :meth:`FieldComparisonList.writeInfoXML`.'''
        return etree.SubElement(parentNode, 'field', name=self.name)

    def getResult(self, modelResult):
        '''Gets the result of the operator on the given fields (as a
        :class:`.FieldComparisonResult`), given a 
        modelResult (:class:`~credo.modelresult.ModelResult`) which
        refers to a directory containing field comparisons
        (i.e. cvg files, see :mod:`credo.io.stgcvg`).
        '''
        cvgIndex = stgcvg.genConvergenceFileIndex(modelResult.outputPath)
        try:
            cvgFileInfo = cvgIndex[self.name]
        except KeyError:     
            # TODO: create a new exception type here?
            raise KeyError("Field '%s' not found in the known list of"\
                " convergence results (%s) for model run '%s'"\
                % (self.name, cvgIndex.keys(),modelResult.modelName))
        dofErrors = stgcvg.getDofErrors_ByDof(cvgFileInfo, steps="last")
        fieldResult = FieldComparisonResult(self.name, dofErrors)
        fieldResult.cvgFileInfo = cvgFileInfo
        return fieldResult


class FieldComparisonResult:
    '''Simple class for storing CREDO FieldComparisonOp Results, so they can be
    analysed and saved.
    
    By default only contains the difference between the field DOFs at the final
    timestep - but recording a reference to the
    :class:`credo.io.stgcvg.CvgFileInfo` for this field allows more complex
    analysis.
    
    .. attribute:: fieldName

       Name of the field that has been compared.

    .. attribute:: dofErrors

       Comparison errors for each DOF of the field, at the final timestep
       that was run.

    .. attribute:: cvgFileInfo

       A :class:`credo.io.stgcvg.CvgFileInfo` allowing detailed access to the CVG
       result for this field. Required for plotting etc. Is optional, needs
       to be recorded after the class has been constructed.
    
    .. attribute:: plottedCvgFilename

       If the :meth:`.plotOverTime` method has been called, this attribute
       will record the filename the plot was saved to.
    '''

    # These are for reading/writing StGermain XML.
    XML_INFO_TAG = "fieldResult"
    XML_INFO_LIST_TAG = "fieldResults"

    def __init__(self, fieldName, dofErrors):
        self.fieldName = fieldName
        self.dofErrors = []
        # Allow the user to pass in just a single error value result for
        # simple fields
        if isinstance(dofErrors, int):
            dofErrors = [dofErrors]

        for errorStr in dofErrors:
            self.dofErrors.append(float(errorStr))
        
        self.cvgFileInfo = None
        self.plottedCvgFilename = None
    
    def writeInfoXML(self, fieldResultsNode):
        '''Writes information about a FieldComparisonResult into an existing,
         open XML doc node'''
        fr = etree.SubElement(fieldResultsNode, self.XML_INFO_TAG)
        fr.attrib['fieldName'] = self.fieldName
        if self.plottedCvgFilename:
            fr.attrib['plottedCvgFilename'] = self.plottedCvgFilename
        for dofIndex in range(len(self.dofErrors)):
            dr = etree.SubElement(fr, 'dofResult')
            dr.attrib['dof'] = str(dofIndex)
            dr.attrib['error'] = str(self.dofErrors[dofIndex])
    
    def plotOverTime(self, save=True, show=False, dofIndex=None, path="."):
        """Plot the result of a FieldComparison over all timesteps of a model.
        Requires the cvgFileInfo paramater to have been set to give access to
        the cvg info of this field.

        .. Note::
           Requires you to have the
           `Matplotlib <http://matplotlib.sourceforge.net/>`_ library installed.
        
        'show', 'save' and 'path' parameters are the same as for
        :meth:`credo.io.stgfreq.FreqOutput.plotOverTime`. The optional 'dofIndex'
        parameter allows you to only plot a particular DOF of the field,
        otherwise all dofs will be plotted on separate graphs."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
        except ImportError:
            print "Error, to use CREDO built-in plot functions, please "\
                " install the matplotlib python library."
            return    
        
        assert self.cvgFileInfo

        dofErrorsArray = stgcvg.getDofErrors_ByDof(self.cvgFileInfo)

        numDofs = len(self.dofErrors)

        if dofIndex is not None:
            dofRange = [0]
            dofIndices = [dofIndex]
        else:
            dofRange = range(numDofs)    
            dofIndices = range(numDofs)
            
        plt.subplots_adjust(wspace=0.4)

        for dofI in dofRange:
            plt.subplot(1,len(dofRange),dofI+1)
            plot = plt.plot(dofErrorsArray[dofIndices[dofI]])
            # TODO: only the within tolerance test should add this.
            #plt.axhline(y=self.tol, label='tolerance', linewidth=3, color='r')

            plt.xlabel("Timestep")
            # TODO: title should change depending on analytic or reference
            plt.ylabel("Dof %d: Error vs analytic soln" % dofIndices[dofI])
            # Only display the title once on left
            if len(dofRange) == 1:
                plt.title("Convergence of field '%s' with analytic solution,"\
                    " for DOF %d" % (self.fieldName, dofIndices[dofI]))
            else:
                if dofI == 0:
                    plt.suptitle("Convergence of field '%s' with analytic"\
                        " solution" % (self.fieldName), fontsize=14)
                plt.title("DOF %d" % dofI)

        if save:
            filename = os.path.join(path, self.fieldName+"-cvg.png")
            plt.savefig(filename, format="png")
            self.plottedCvgFilename = filename
        if show: plt.show()

    def withinTol(self, tol):
        """Checks that the difference between the fields is within a given
        tolerance, at the final timestep."""
        for dofError in self.dofErrors:
            if dofError > tol: return False
        return True    


class FieldComparisonList(AnalysisOperation):
    '''Class for maintaining and managing a list of field comparisons
    (managed as a list of :class:`FieldComparisonOp` objects),
    including IO from StGermain XML files.
    
    Currently maps to the "FieldTest" component's functionality in StgFEM.

    .. Note:: Currently the whole _list_ of Field comparisons is a single
       :class:`credo.analysis.api.AnalysisOperation`,
       because this is the design of the FieldTest component
       in StgFEM. In future we may look at modularising this functionality
       further so that single comparisons can be managed as operators.
    
    .. attribute:: fields

       A dictionary mapping field names that need to be compared, to
       :class:`.FieldComparisonOp` to perform the comparison.
       
    .. attribute:: fromXML

       If True, means the list of fields to compare (ie :attr:`.fields`)
       should be read from the Model XML files of the model to attach to.
       If False, the user has to manually specify the fields to compare.

    .. attribute:: useReference

       Determines whether fields are compared against a reference solution
       (if True), or analytic (if False). If useReference is true, user
       must also specify :attr:`.referencePath` so that the appropriate
       StGermain XML for the operation can be written.

    .. attribute:: useHighResReference

       Determines whether fields are compared against a high-res reference
       solution (if True), or analytic (if False). If useHighResReference
       is true, user must also specify :attr:`.referencePath` so that
       the appropriate StGermain XML for the operation can be written.

       .. note:: Don't also specify :attr:`useReference`, choose one or the
          other.

    .. attribute:: referencePath

       (Relative or absolute) path to the reference solutions for the 
       specified fields.

    .. attribute:: testTimestep

       Integer, the timestep of the model that the comparison will occur at.
       If 0, means the final timestep. Based on the capability of the 
       StGermain FieldTest component.
    '''

    # These attributes are all needed as to read/write the XML description
    # of this Op in StGermain (FieldTest).
    stgXMLCompType = 'FieldTest'
    stgXMLCompName = 'credoFieldTester'
    # This component is unusual in that it needs a "pluginData" struct
    # separate to the actual component definition.
    stgXMLSpecName = 'pluginData'
    stgXMLSpecFList = 'FieldMappings'
    stgXMLSpecRList = 'ReferenceFields'

    def __init__(self, fieldsList=None):
        self.fromXML = False
        if fieldsList == None:
            self.fields = {}
        self.useReference = False
        self.useHighResReference = False
        self.referencePath = None
        self.testTimestep = 0

    def getCmpSrcString(self):
        """Returns an appropriate string to document the comparison source 
        of the fields being compared - i.e. either reference or analytic."""
        if self.useReference == True:
            return "reference"
        elif self.useHighResReference == True:
            return "highResReference"
        else:
            return "analytic"

    def add(self, fieldComparisonOp):
        """Add another :class:`FieldComparisonOp` to the list to compare."""
        self.fields[fieldComparisonOp.name] = fieldComparisonOp    

    def postRun(self, modelRun, runPath):
        """Implements :meth:`AnalysisOperation.postRun`. In this case, moves
        all CVG files created to output path."""
        stgpath.moveAllToTargetPath(runPath, 
            os.path.join(modelRun.basePath, modelRun.outputPath),
            stgcvg.CVG_EXT)
    
    def writeInfoXML(self, parentNode):
        '''Writes information about this class into an existing, open XML
         doc node, in a child element.'''

        if len(self.fields) == 0: return

        ftNode = etree.SubElement(parentNode, 'fieldComparisonList')
        ftNode.attrib['fromXML']=str(self.fromXML)
        ftNode.attrib['useReference']=str(self.useReference)
        ftNode.attrib['useHighResReference']=str(self.useHighResReference)
        ftNode.attrib['referencePath']=str(self.referencePath)
        ftNode.attrib['testTimestep']=str(self.testTimestep)
        fListNode = etree.SubElement(ftNode, 'fields')
        for fTest in self.fields.values():
            fTest.writeInfoXML(fListNode)

    def writeStgDataXML(self, rootNode):
        '''Writes the necessary StGermain XML to enable these specified
         fields to be compared.'''

        # If there are no fields to test, no need to write StGermain XML
        if len(self.fields) == 0: return

        if self.fromXML:
            # In this case, just make sure the printing of comparison info
            #  enabled.
            pluginDataElt = etree.SubElement(rootNode, stgxml.STG_STRUCT_TAG,
                name=self.stgXMLSpecName, mergeType="merge")
            stgxml.writeParam(pluginDataElt, 'appendToAnalysisFile', 'True',
                mt="replace")
        else:
            # Append the component to component list
            compElt = stgxml.writeMergeComponent(rootNode, self.stgXMLCompName,
                self.stgXMLCompType)
            # Create the plugin data
            pluginDataElt = etree.SubElement(rootNode, stgxml.STG_STRUCT_TAG,
                name=self.stgXMLSpecName, mergeType="replace")
            xmlFieldTestsList = self.fields.keys()
            # This is necessary due to format of this list in FieldTest plugin:
            # <FieldName> <# of analytic func> - both as straight params
            ii=0
            for index in range(1,len(self.fields)*2,2):
                xmlFieldTestsList.insert(index, str(ii))
                ii+=1

            if self.useReference or self.useHighResReference:
                stgxml.writeParamSet(pluginDataElt, {
                    'referenceSolutionFilePath':self.referencePath,
                    'useReferenceSolutionFromFile':self.useReference,
                    'useHighResReferenceSolutionFromFile':self.useHighResReference })
                stgxml.writeParamList(pluginDataElt, self.stgXMLSpecRList,
                    self.fields.keys())
            
            # Current plugin seems to require using a numeric fields list
            # For both analytic and ref solns.
            stgxml.writeParamList(pluginDataElt, self.stgXMLSpecFList,
                xmlFieldTestsList)

            stgxml.writeParamSet(pluginDataElt, {
                'IntegrationSwarm':'gaussSwarm',
                'ConstantMesh':'constantMesh',
                'testTimestep':self.testTimestep,
                'ElementMesh':'linearMesh',
                'normaliseByAnalyticSolution':'True',
                'context':'context',
                'appendToAnalysisFile':'True'})
    
    def readFromStgXML(self, inputFilesList, basePath):
        '''Read in the list of fields that have already been specified to 
         be tested from a set of StGermain input files. Useful when e.g. 
         working with an Analytic Solution plugin.'''
        self.fromXML = True

        # create a flattened file
        absInputFiles = stgpath.convertLocalXMLFilesToAbsPaths(inputFilesList,
            basePath)
        ffile=stgxml.createFlattenedXML(absInputFiles)
        xmlDoc = etree.parse(ffile)
        stgRoot = xmlDoc.getroot()
        # Go and grab necessary info from XML file
        fieldTestDataEl = stgxml.getStructNode(stgRoot, self.stgXMLSpecName)
        fieldTestListEl = stgxml.getListNode(fieldTestDataEl,
            self.stgXMLSpecFList)

        fieldTestEls = fieldTestListEl.getchildren()
        # As per the current spec, the field names are followed by an index 
        # of analytic solution
        ii = 0
        while ii < len(fieldTestEls):
            fieldName = fieldTestEls[ii].text
            self.fields[fieldName] = FieldComparisonOp(fieldName)
            # Skip the index
            ii+=1
            ii+=1
        # NB: not reading in all the other specifying stuff currently. Possibly
        # would be useful to do this in future.
        os.remove(ffile)

    def checkStgXMLResultsEnabled(self, inputFilesList, basePath):
        """Checks that the field comparison has the writing of comparison
        info to file enabled (returning Bool)."""
        absInputFiles = stgpath.convertLocalXMLFilesToAbsPaths(inputFilesList,
            basePath)
        ffile=stgxml.createFlattenedXML(absInputFiles)
        xmlDoc = etree.parse(ffile)
        stgRoot = xmlDoc.getroot()
        fieldTestDataEl = stgxml.getStructNode(stgRoot, self.stgXMLSpecName)
        appendNode = stgxml.getParamNode(fieldTestDataEl,
            "appendToAnalysisFile")
        appendBool = stgxml.strToBool(appendNode.text)
        os.remove(ffile)
        return appendBool

    def getAllResults(self, modelResult):
        """Return a list of :class:`FieldComparisonResult` based on all the
        :class:`FieldComparisonOps` specified to be done during
        a run, from the given modelResult
        (:class:`~credo.modelresult.ModelResult`)."""

        fComps = self.fields.values()
        return [fCompOp.getResult(modelResult) for fCompOp in fComps]

#--------------------------------------
# Functions below useful for doing convergence analysis with length scale

def getFieldScaleCvgData_SingleCvgFile(cvgFilePath):
    '''Given a path that CVG files reside in, returns the length scales of
    each run (as a list), and a list of field error data for each field/cvg
    info in the given path.
    Thus is a utility function for generating necessary fieldErrorData for a
    multi-res convergence analysis.
    
    .. Note::

       This assumes all cvg info is stored in the same 
       convergence file (the default approach of the legacy SYS tests)
    '''
    cvgIndex = stgcvg.genConvergenceFileIndex(cvgFilePath)
    fieldErrorData = {}
    for fieldName, cvgFileInfo in cvgIndex.iteritems():
        #NB: assumes all cvg files and all fields have same len scales.
        lenScales = stgcvg.getRes(cvgFileInfo.filename)
        dofErrors = stgcvg.getDofErrors_ByDof(cvgFileInfo)
        fieldErrorData[fieldName] = dofErrors
    return lenScales, fieldErrorData


def calcFieldCvgWithScale(fieldName, lenScales, dofErrors):
    '''Gets the convergence and correlation of a field with resolution
    (taking the log10 of both).
    
    lenScales argument should simply be an array of length scales for the
    different runs.
    dofErrors must be a list, for each dof of the field, of the error
    vs some expected solution at the corresponding length scale.

    returns a list of tuples, one per dof, where each tuple contains:
    (convergence rate, pearson correlation) over the set of scales.
    ''' 

    print "Testing convergence for field '%s'" % fieldName
    #print "Length scales are %s" % lenScales
    #print "Dof errors for %d dofs are %s" % (len(dofErrors), dofErrors)
    scaleLogs = map(math.log10, lenScales)
    convResults = []
    for errorArray in dofErrors:
        errLogs = map(math.log10, errorArray)
        cvgRate, intercept, rSq = stats.linreg(scaleLogs, errLogs)
        pearsonCorr = math.sqrt(rSq)
        convResults.append((cvgRate, pearsonCorr))
    return convResults        

