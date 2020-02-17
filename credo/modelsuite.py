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

"""This module allows the running of a whole suite of related
:class:`~credo.modelrun.ModelRun` s, and managing and analysing their results
as a consistent set.

The key class in this module is the :class:`.ModelSuite`.

For example usage, see the CREDO documentation Examples section,
:ref:`credo-examples`, e.g. :ref:`credo-examples-raytay-run-suite`.

This class also performs a key role in the System tests provided in the
:mod:`credo.systest` module.
"""
from builtins import zip
from builtins import map
from builtins import object

import copy
import os, glob
import itertools
import operator
import csv

import credo
from credo import modelrun as mrun
from credo import modelresult as mres

# The below is for Python 2.5 compatibility
try:
    import itertools
    product = itertools.product
except AttributeError:
    import credo.utils
    product = credo.utils.productCalc

class ModelResultNotExistError(Exception):
    """Exception for specifying that a Model Result that CREDO was asked
    to read in, doesn't exist."""
    pass


class ModelVariant(object):
    """ A class that can be added to a :class:`.ModelSuite` to help
    auto-generate a suite of ModelRuns to perform, where a particular
    parameter is being varied over a certain range.

    This is an abstract base class, you should select an actual ModelVariant.

    .. attribute:: paramRange

       A list, containing the values that the parameter should be varied
       over. E.g. [0,1,2], or [5.6, 7.8, 9.9]. Needs to be of the correct
       type for the particular parameter. The Python
       `range() <http://docs.python.org/library/functions.html#range>`_
       function can be useful in generating such a list."""

    def __init__(self, paramRange):
        self.paramRange = paramRange

    def applyToModel(self, modelRun, ii):
        """Function to apply the ii-th value of paramRange to a model."""
        raise NotImplementedError("Abstract base method, please over-ride"\
            " in your implementation.")

    def valLen(self):
        """Returns the length of the list of parameter values to vary
        specified in :attr:`.paramRange`."""
        return len(self.paramRange)

    def valStr(self, ii):
        """Return a string version of the ii-th parameter value."""
        paramVal = self.paramRange[ii]
        if type(paramVal) == float:
            valStr = "%g" % paramVal
        else:
            valStr = str(paramVal)
        return valStr


class StgXMLVariant(ModelVariant):
    """
    A :class:`.ModelVariant` designed to modify StGermain XML model input
    parameters.

    .. attribute:: paramPath

       The value to use when over-riding the parameter in a StGermain
       dictionary, using the StGermain command line format.

       E.g. Setting "gravity" would override the gravity parameter in
       the dictionary, whereas setting to
       "components.initialConditionsShape.startX" would override the
       startX parameter, within the initialConditionsShape component.
    """
    def __init__(self, paramPath, paramRange):
        ModelVariant.__init__(self, paramRange)
        self.paramPath = paramPath

    def applyToModel(self, modelRun, ii):
        """Apply the ii-th value in the attr:`.paramRange` to a particular
        :class:`~credo.modelrun.ModelRun`."""
        modelRun.paramOverrides[self.paramPath] = self.paramRange[ii]

    def cmdLineStr(self, ii):
        """Return the command-line string to apply this value."""
        return credo.io.stgcmdline.paramStr(self.paramPath, self.paramRange[ii])


class JobParamVariant(ModelVariant):
    """A :class:`.ModelVariant` designed to modify job parameters.

    .. attribute: jobParam:

       string name of parameter you wish to vary (eg "nproc").
    """
    def __init__(self, jobParam, paramRange):
        ModelVariant.__init__(self, paramRange)
        self.jobParam = jobParam

    def applyToModel(self, modelRun, ii):
        """Apply the ii-th value in the attr:`.paramRange` to a particular
        :class:`~credo.modelrun.ModelRun`."""
        modelRun.jobParams[self.jobParam] = self.paramRange[ii]

    def cmdLineStr(self, ii):
        """Return the command-line string to apply this value."""
        return credo.io.stgcmdline.paramStr(self.jobParam, self.paramRange[ii])


def getParamValuesIter(modelVariants, iterGen):
    """Given a list of model variants and an iterator generator function
    (eg itertools.izip or itertools.product) to use, generates
    a specific iterator that can be used on the modelVariants to obtain
    the actual param values."""
    paramIter = iterGen(*list(map(operator.attrgetter('paramRange'),
        iter(modelVariants.values()))))
    return paramIter

def getParamValues(modelVariants, iterGen):
    """Shortcut to create a list of param values using
    :func:`.getParamValuesIter`"""
    paramIter = getParamValuesIter(modelVariants, iterGen)
    return list(paramIter)

def getVariantIndicesIter(modelVariants, iterGen):
    """Given a list of model variants and iterator generator function to use,
    generates an iterator of indices into the modelVariants list."""
    variantLens = [mv.valLen() for mv in modelVariants.values()]
    indexIterator = iterGen(*list(map(range, variantLens)))
    return indexIterator

def getVariantNameDicts(modelVariants, indicesIt):
    """Generates a list of dictionaries of parameters to be modified for each
    model run, given a list of :class:`.StgXMLVariant` and an iterator into
    them (e.g. generated by :func:`.getVariantIndicesIter`.
    """
    paramDicts = []
    modelVarList = list(modelVariants.values())
    for indexSet in indicesIt:
        newDict = {}
        for mvI, mvEntry in enumerate(modelVariants.items()):
            mvName, modelVar = mvEntry
            paramVal = modelVar.paramRange[indexSet[mvI]]
            newDict[mvName] = paramVal
        paramDicts.append(newDict)
    return paramDicts

def getVariantParamPathDicts(modelVariants, indicesIt):
    """Generates a list of dictionaries of parameters to be modified for each
    model run, given a list of :class:`.StgXMLVariant` and an iterator into
    them (e.g. generated by :func:`.getVariantIndicesIter`.
    """
    for mv in modelVariants.values():
        assert isinstance(mv, StgXMLVariant)
    paramDicts = []
    for indexSet in indicesIt:
        newDict = {}
        for mvI, modelVar in enumerate(modelVariants.values()):
            paramVal = modelVar.paramRange[indexSet[mvI]]
            newDict[modelVar.paramPath] = paramVal
        paramDicts.append(newDict)
    return paramDicts

def getVariantCmdLineOverrides(modelVariants, indicesIt):
    """Generates a list of strings to use at cmd line for each
    model run, given a list of :class:`.StgXMLVariant` and an iterator into
    them (e.g. generated by :func:`.getVariantIndicesIter`.
    """
    overrideCmdLines = []
    for indexSet in indicesIt:
        overStrs = []
        for mvI, modelVar in enumerate(modelVariants.values()):
            overStrs.append(modelVar.cmdLineStr(indexSet[mvI]))
        overrideCmdLines.append(" ".join(overStrs))
    return overrideCmdLines

def getSubdirTextParamVals(modelVariants, paramIndices):
    """Creates a subdirectory text based on the names and values of each
    variant."""
    subDirName = ""
    varTexts = []
    for mvI, mvEntry in enumerate(modelVariants.items()):
        mvName, modelVar = mvEntry
        valStr = modelVar.valStr(paramIndices[mvI])
        varTexts.append("%s_%s" % (mvName, valStr))
    subDirName = "-".join(varTexts)
    return subDirName

def getTextParamValsSubdirs(modelVariants, indicesIt):
    """Given a list of :class:`ModelVariants` and an index iterator,
    returns a list of all subDirs to use."""
    subDirs = []
    for indexSet in indicesIt:
        subDirs.append(getSubdirTextParamVals(modelVariants, indexSet))
    return subDirs

def getVarRunIs(varName, modelVariants, runDicts):
    """Given a variant name, modelVariants dict and iterGen function,
    returns a mapping of values of the named modelVariant to run indices"""
    varRunIs = {}
    for varValue in modelVariants[varName].paramRange:
        varRunIs[varValue] = []
        for runI, runDict in enumerate(runDicts):
            if runDict[varName] == varValue:
                varRunIs[varValue].append(runI)
    return varRunIs

def getResultsByVarRunIs(varRunIsMap, results):
    """Given a varRunIsMap generated by :func:`getVarRunIs` and an array of
    results, gives a mapping directly from variant values to corresponding result."""
    resultsMap = {}
    for varValue, varRunIs in varRunIsMap.items():
        resultsMap[varValue] = [results[runI] for runI in varRunIs]
    return resultsMap

def getOtherParamValsByVarRunIs(varRunIsMap, varDicts, otherParam):
    """Given a varRunIsMaps generated by :func:`varRunIsMap`, a varDict and
    the name of another variant param in the dict, returns a mapping from
    the variant values to the values of the other param at the same indices."""
    otherValsMap = {}
    for varValue, varRunIs in varRunIsMap.items():
        otherValsMap[varValue] = [varDicts[runI][otherParam] for runI \
            in varRunIs]
    return otherValsMap

################

def getSubdir_TextParamVals(modelRun, modelVariants, paramIndices, runIndex):
    """Generate an output sub-directory name for a run with
    a printed version of :attr:`ModelSuite.modelVariants` names,
    and vales for this run.
    (Good in the sense of being fairly self-describing, but can
    be long if you have many model variants)."""
    subPath = getSubdirTextParamVals(modelVariants, paramIndices)
    return subPath

def getSubdir_RunIndex(modelRun, modelVariants, paramIndices, runIndex):
    """Simply prints the index of the run as a subdirectory."""
    return "%.5d" % runIndex

def getSubdir_RunIndexAndText(modelRun, modelVariants, paramIndices, runIndex):
    """Subdir is based on both the run index, and the textual variant names."""
    subPath = getSubdirTextParamVals(modelVariants, paramIndices)
    return "%.5d-%s" % (runIndex, subPath)

class ModelSuite(object):
    '''A class for running a suite of Models (e.g. a group for profiling,
    or a System Test that requires multiple runs).

    The two main ways of using this class are:

    * Creating a :class:`.ModelSuite`, and then adding
      :class:`~credo.modelrun.ModelRun` s to the suite using
      the :meth:`.addRun` method.
    * Creating a :class:`.ModelSuite`, and providing a
      :class:`~credo.modelrun.ModelRun` as a template, then adding
      :class:`.StgXMLVariant` s to define what sort of parameter
      sweep should be performed. In this case, :meth:`.generateRuns()`
      needs to be called after all variants have been added.

    .. attribute:: outputPathBase

       The base path to use for saving model results under.

    .. attribute:: runs

       A list of :class:`~credo.modelrun.ModelRun` s to be run as part of the
       suite. See :meth:`.generateRuns` and :meth:`.addRun`.

    .. attribute:: runDescrips

       Short (eg 1 line) textual description for each ModelRun stored in the
       :attr:`.runs`.

    .. attribute:: runCustomOptSets

       Custom sets of options (to be used at the command line) associated
       with each run in :attr:`.runs` (strings).

    .. attribute:: resultsList

       Initially `None`, after the suite has been run (using :meth:`.runAll`),
       saves a reference to all :class:`~credo.modelresult.ModelResult` s
       generated.

    .. attribute:: subOutputPathGenFunc

       This function will can be used to customise the model sub-path based
       on each modelRun. Override it if you wish to use other than the default.

    .. attribute:: templateMRun

       (Optional) setting this to an :class:`~credo.modelresult.ModelRun`
       means this run can be used as a "template" to add variants to,
       and create a parameter sweep over this run.

       .. seealso: :meth:`.addVariant`, :meth:`generateRuns`, and
          :class:`.StgXMLVariant`.

    .. attribute:: iterGen

       (Related to auto-generation): A generator function to create an
       iterator to use when auto-generating a suite based on modelVariants.
       See Python module :mod:`itertools` module for more.

    .. attribute:: modelVariants

       Set of :class:`.StgXMLVariant` s to apply to the template run in
       order to auto-generate a suite to vary certain parameters. See
       :attr:`.templateMRun` for more.

    '''

    def __init__(self, outputPathBase, templateMRun=None):
        self.outputPathBase = outputPathBase
        self.runs = []
        self.runDescrips = []
        self.runCustomOptSets = []
        self.resultsList = []
        self.subOutputPathGenFunc = getSubdir_RunIndex
        # Parameters related to dynamic generation
        self.templateMRun = templateMRun
        self.iterGen = None
        self.modelVariants = {}

        # TODO: AY: this seems to be WIP, should I set attribute here?
        # a list of image file(names), and model images for report
        self.analysisImages = []
        self.modelImagesToDisplay = None

    def addRun(self, modelRun, runDescrip=None, runCustomOpts=None,
            forceOutputPathBaseSubdir=True):
        """Add a model run to the list of those to be run.

        :param modelRun: A :class:`~credo.modelrun.ModelRun` to be added.
        :keyword runDescrip: An (optional) string describing the run.
        :keyword runCustomOpts: (optional) string of any custom options
          that should be passed through to StGermain, only for this run.
        :keyword forceOutputPathBaseSubdir: if True (default), will
          update the model run's output dir to enforce it's a subdir of
          :attr:`.outputPathBase`
        :returns: the index of the newly added run in the modelRun list."""
        if not isinstance(modelRun, mrun.ModelRun):
            raise TypeError("Error, given run not an instance of a"\
                " ModelRun" % runI)
        if forceOutputPathBaseSubdir:
            commonPrefix = os.path.commonprefix([self.outputPathBase,
                modelRun.outputPath])
            if commonPrefix != self.outputPathBase:
                newPath = os.path.join(self.outputPathBase, modelRun.name)
                modelRun.outputPath = newPath
                modelRun.logPath = newPath
        self.runs.append(modelRun)
        self.runDescrips.append(runDescrip)
        self.runCustomOptSets.append(runCustomOpts)
        # Return the index of the newly added run.
        return len(self.runs) - 1

    def getRunByName(self, runName):
        """Get a modelRun instance from the suite with a particular name."""
        for modelRun in self.runs:
            if modelRun.name == runName:
                return modelRun

    def getRunIndex(self, runName):
        """Get the index within the suite of a run with the given name."""
        for runI, modelRun in enumerate(self.runs):
            if modelRun.name == runName:
                return runI

    def preRunCleanup(self):
        """Convenience function to call all sub-methods for tasks to do
        before running to clean up directories."""
        self.cleanAllOutputPaths()
        self.cleanAllLogFiles()

    def cleanAllOutputPaths(self):
        '''Remove all files in each model's output path. Useful to get rid of
        results still there from previous jobs. Doesn't delete sub-directories,
        in case they are other model runs' results that should be ignored.'''
        startDir = os.getcwd()
        for modelRun in self.runs:
            os.chdir(modelRun.basePath)
            for filePath in glob.glob(os.path.join(modelRun.outputPath,"*")):
                if os.path.isfile(filePath):
                    os.unlink(filePath)
            os.chdir(startDir)

    def cleanAllLogFiles(self):
        """Remove all stdout and stderr files from each ModelRun's designated
        output and log paths."""
        startDir = os.getcwd()
        for modelRun in self.runs:
            os.chdir(modelRun.basePath)
            logFiles = [modelRun.getStdOutFilename(),
                modelRun.getStdErrFilename()]
            for fname in logFiles:
                if os.path.isfile(fname):
                    os.unlink(fname)
            os.chdir(startDir)

    def addVariant(self, name, modelVariant):
        """Add a :class:`.StgXMLVariant` to the list to be applied to a
        template run. See :attr:`.modelVariants`."""
        self.modelVariants[name] = modelVariant

    def generateRuns(self, iterGen=product):
        """When using a template modelRun, will generate runs for the suite
        based on it. The generated runs are saved to
        the :attr:`.runs` attribute ready to be run using :meth:`.runAll`.

        This requires that there are one or more :class:`.StgXMLVariant`
        recorded on the class already.

        :param iterGen: this determines what iterator strategy should be
          used to generate the runs. Defaults to a product, but a simple
          "zip" style can be achieved using the itertools.izip iterator
          generating function.
          See the Python :mod:`itertools` module for more.
        """

        assert self.templateMRun

        # Save the strategy passed in.
        self.iterGen = iterGen
        # Empty the "runs", in case it has values in there already
        self.runs = []

        # Strategy used below is instead of iterating directly over the
        # parameters we are applying to each run, create indices into the
        # modelVariants lists to work out which to apply for each run.
        indexIterator = getVariantIndicesIter(self.modelVariants, self.iterGen)

        for runI, paramIndices in enumerate(indexIterator):
            # First create a copy of the template model run
            newMRun = copy.deepcopy(self.templateMRun)
            # Now, apply each variant to it as appropriate
            for varI, modelVar in enumerate(self.modelVariants.values()):
                modelVar.applyToModel(newMRun, paramIndices[varI])

            subPath = self.subOutputPathGenFunc(newMRun, self.modelVariants,
                paramIndices, runI)
            newMRun.name += "-%s" % (subPath)
            newMRun.outputPath = os.path.join(self.outputPathBase, subPath)
            newMRun.logPath = os.path.join(self.outputPathBase, subPath)
            self.runs.append(newMRun)
            self.runDescrips.append(subPath)
            self.runCustomOptSets.append(None)

    def writeAllModelRunXMLs(self):
        """Save an XML record of each ModelRun currently in :attr:`.runs`."""
        for runI, modelRun in enumerate(self.runs):
            modelRun.writeInfoXML()

    def writeAllModelResultXMLs(self):
        """Save an XML record of each ModelResult currently in
        :attr:`.resultsList`."""
        for runI, mResult in enumerate(self.resultsList):
            mResult.writeRecordXML()

    def getCustomOpts(self, runI, extraCmdLineOpts):
        """Get the custom opts (as a string) to apply for modelRun runI."""
        customOpts = None
        if self.runCustomOptSets[runI]:
            customOpts = self.runCustomOptSets[runI]
        if extraCmdLineOpts:
            if customOpts == None: customOpts = ""
            customOpts += extraCmdLineOpts
        return customOpts

    def readResultsFromPath(self, basePath, overrideOutputPath=None,
            checkAllPresent=True):
        """Read the results generated for a given ModelSuite located off the
        given basePath where the suite was run, and return the list of results.

        This will ignore results in the directory not related to this suite.

        :arg overrideOutputPath: if specified, this path overrides the default
          outputPath of the suite itself to search for the results.
          (I.e. useful if you are reading from a previous suite with different
          output path.)
        :arg checkAllPresent: if True this will check that all runs expected
          for the suite were found in the list of results.

        .. note:
           Currently this just relies on model result names for the suite
           matching up correctly. In future, should really scan the ModelResult
           XMLs and check they match correctly.
        """
        if overrideOutputPath is not None:
            outputPathBase = overrideOutputPath
        else:
            outputPathBase = self.outputPathBase
        # First read all results
        # TODO: passing in the 'name' below is hacky:- really should be
        #  reading this in from model result XMLs
        if self.templateMRun:
            baseName = self.templateMRun.name
        else:
            baseName = None
        readResults = getModelResultsArray(baseName,
            os.path.join(basePath, outputPathBase))
        # Now check through, and build a new list only contained in this index
        sResults = []
        for result in readResults:
            runIndex = self.getRunIndex(result.modelName)
            if runIndex == None: continue
            else:
                sResults.append((runIndex, result))
        mResults = [None] * len(sResults)
        # Now put them in the right order
        for runIndex, result in sResults:
            mResults[runIndex] = result
        # Finally, check each run in the suite is present in the returned list
        if checkAllPresent:
            resultNames = [res.modelName for res in mResults]
            for runI, mRun in enumerate(self.runs):
                if mRun.name not in resultNames:
                    raise ModelResultNotExistError("Error, given basePath"\
                        " for reading model"\
                        " results from, %s, with output path %s, is missing"\
                        " result for suite's run '%s' (index %d)."\
                        "\n(names read are %s)." %\
                        (basePath, outputPathBase, mRun.name, runI,
                         resultNames))
        return mResults

# TODO: here perhaps would be where we have tools to generate stats/plots
# of various properties of the suite, e.g. memory usage? Or should
# this be a capability of some sort of uber-results list? Or profiling
# tools?

def writeInputsOutputsToCSV(mSuite, observablesDict, fname):
    """Write a CSV file, containing all the ModelVariants defined for a
    ModelSuite, and also all the observables in the observablesDict.

    :param observablesDict: a dictionary of 'observables', each entry in
      the form 'obsName':[obsVals for each run], e.g. "vrms":[0.6, 0.8, 0.9].
    :param fname: file name of the CSV file to create, inside the model
      suite's base output path.

    .. note:: Could be a function on the ModelSuite?
    """
    target = open(os.path.join(mSuite.runs[0].basePath, mSuite.outputPathBase, fname), "w" )
    wtr = csv.writer(target)
    # Need to do sorting to make sure keys here match those below.
    sortedVarNames = list(mSuite.modelVariants.keys())
    sortedVarNames.sort()
    wtr.writerow(sortedVarNames + list(observablesDict.keys()))
    indexIt = getVariantIndicesIter(mSuite.modelVariants, mSuite.iterGen)
    varDicts = getVariantNameDicts(mSuite.modelVariants, indexIt)
    for varDict, observs in zip(varDicts, list(zip(*iter(observablesDict.values())))):
        sortedValues = [varDict[varName] for varName in sortedVarNames]
        wtr.writerow(sortedValues + list(observs))
    target.close()

def getModelResultsArray(baseName, baseDir):
    """Post-processing: given a base model name and base output directory,
    search this directory for model results, and read into a list of
    :class:`~credo.modelresult.ModelResult` .

    .. note:: Needs more checking added, and ability to recover metadata
       about the ModelRuns.
    """
    modelResults = []
    for fName in os.listdir(baseDir):
        fullPath = os.path.join(baseDir, fName)
        if os.path.isdir(os.path.join(baseDir, fName)):
            dirName = fName
            if baseName == None:
                modelName = dirName
            else:
                modelName = "%s-%s" % (baseName, dirName)
            mResult = mres.readModelResultFromPath(fullPath)
            #ModelResult(modelName, fullPath)
            # TODO: When func ready, search for an XML file containing
            #  job meta info, and attach here
            # mResult.jobMetaInfo = ...
            modelResults.append(mResult)
    return modelResults
