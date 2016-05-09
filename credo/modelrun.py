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

"""A core module for CREDO, since it defines and manages running models of a
StGermain-based code such as Underworld.

Primary interface is via the :class:`ModelRun`, which enables you to specify,
configure and run a Model, and save records of this as an XML. This process will
produce a :class:`credo.modelresult.ModelResult` class.
"""

import os, sys
from datetime import timedelta
import shutil
import inspect
from xml.etree import ElementTree as etree
from credo.io.stgxml import writeXMLDoc
import credo.modelresult
from credo.io import stgxml
from credo.io import stgpath
from credo.io import stgcmdline
from credo.analysis import fields
import credo.utils

# Global list of allowed Python types that can be saved as StGermain SimParams
#  I.E. that StGermain's Dictionary knows how to handle.
_allowedModelParamTypes = [int, float, long, bool, str]

CREDO_ANALYSIS_RECORD_FILENAME = "credo-analysis.xml"
SOLVER_OPTS_RECORD_FILENAME = "solverOptsUsed.opt"

# Global variables (defaults) used by the JobParams dict class.
DEF_NPROC = 1
DEF_MAX_RUN_TIME = None
DEF_POLL_INTERVAL = 1

class ModelRun(object):
    """ An abstract class that defines the common interface of various model
    runs (for different simultors).

    JobRunner only uses the following attributes:
        .name .basePath .outputPath .jobParams .logPath
        .getModelRunCommand() .getStdOutFilename() .getStdErrFilename()
        .checkValidRunConfig() .preRunPreparation() .postRunCleanup()
        .createModelResult()

    """
    def __init__(self, name, basePath=None, outputPath=None, logPath=None):
        self.name = name
        if basePath is None:
            # Default to the path of the calling script
            self.basePath = credo.utils.getCallingPath(1)
        else:
            self.basePath = basePath
        self.basePath = os.path.abspath(self.basePath)
        if outputPath is None:
            # Sensible default is output/name
            self.outputPath = os.path.join("output", name)
        else:
            self.outputPath = outputPath
        if logPath is None:
            self.logPath = self.outputPath
        else:
            self.logPath = logPath
        self.jobParams = JobParams()

    def getModelRunCommand(self, extraCmdLineOpts=None):
        """ Construct the command needed to run that model, and return as a
        string. This is mainly called by JobRunner.

        :keyword extraCmdLineOpts: any extra command line options, to be
          passed straight through to the model.

        JobRunner may add mpiexec or profiler related commands in the front.
        JobRunner may also pass additional commandline options that belongs to
        the simulator.
        """
        raise NotImplementedError(".getModelRunCommand()")

    def getStdOutFilename(self):
        """Get the name of the file this Model's stdout needs to/has been
        saved to."""
        return os.path.join(self.outputPath, "%s.stdout" % self.name)

    def getStdErrFilename(self):
        """Get the name of the file this Model's stderr needs to/has been
        saved to."""
        return os.path.join(self.outputPath, "%s.stderr" % self.name)

    def checkValidRunConfig(self):
        pass

    def preRunPreparation(self):
        pass

    def postRunCleanup(self):
        pass

    def createModelResult(self):
        """ This is to be called by JobRunner to generate ModelResult.  It
        returns a ModelResult object that matches the ModelRun object.
        """
        raise NotImplementedError(".createModelResult()")

class UnderworldModelRun(ModelRun):
    """A class to keep records about a StgDomain/Underworld Model Run,
    including access to the underlying XML of the actual model.

    This is one of the key core classes in CREDO, useful on it's own for
    managing analysis, but also underlying the :mod:`credo.systest` module.

    The basic usage pattern of this class is that a ModelRun needs to be
    constructed and configured to specify the basic XML files defining
    a StGermain Model, but also any customisations and
    :class:`credo.analysis.api.AnalysisOperation` classes attached to be
    performed.

    After the model is run (see :mod:`credo.jobrunner`),
    a :class:`~credo.modelresult.ModelResult` will be produced as a record of
    the run and for further analysis.

    Examples of using the ModelRun are documented in CREDO, see
    :ref:`credo-examples-analysis`.

    Key attributes:

    .. attribute:: name

       name of the modelRun.

    .. attribute:: basePath

       The path from which all paths to model input files (on the local machine)
       are specified relative to, and which the job will run in (if running
       on local machine).

    .. attribute:: modelInputFiles

       'Input files' that comprise the XML model that will be run.

    .. attribute:: outputPath

       Output path that all model results will be saved to (is passed
       through to StGermain).

    .. attribute:: cpReadPath
    # TODO:[ Refactor] remove, StGermain specific (maybe)

       Path that checkpoints are read from (is passed through to StGermain).

    .. attribute:: logPath

       Path that log files of the run will be saved to.

    .. attribute:: jobParams

       A :class:`.JobParams` class, to record options needed to define
       how the model should be actually run (eg number of procs to use).

    .. attribute:: simParams

       A :class:`.SimParams` object, recording key parameters to control the
       model. This defaults to `None`, unless the user specifically
       instantiates one either in the constructor or subsequently sets this
       directly later. This idiom assumes that if simParams is `None`, all
       the necessary parameters are defined in the StGermain XML directly.

       .. note:: You shouldn't provide a particular parameter in both a
          SimParams object, and as an override of the ModelRun's
          :attr:`.paramOverrides` list. At both construction-time and
          just before the model is run, a check is performed that this
          has not occurred.

    .. attribute:: solverOpts

       The name of the file storing options passed through to the
       `PETSc <http://www.mcs.anl.gov/petsc>`_
       numerical solver framework. Depending on the Model being solver,
       these can have
       an important role determining the performance and numerical
       approach taken. See the 'System Routines' section of
       `PETSc 2.0.16 Changes log
       <http://www.mcs.anl.gov/petsc/petsc-2/documentation/changes/2016.html>`_.
       This option file is separate to the :attr:`~paramOverrides` attribute,
       although the options passed through to PETSc may be used to further
       customise matrices specified as part of StGermain components.

       A file recording the options used for a modelRun will be saved in
       the output path, with name specified in
       :const:`credo.modelrun.SOLVER_OPTS_RECORD_FILENAME`.

       .. note:: the interface here has been kept as specifying a filename with
          the options rather than using a Python list, as the solver options
          can run into the hundreds, and generally several of these files are
          available and maintained by the developers for different solvers.

    .. attribute:: paramOverrides

       A list of StGermain XML parameter overrides that should be applied,
       in the form (XML_param_path, override_value). These will then be
       passed through at the command line.

       E.g. if paramOverrides is set to [("gravity",0.8)], it means that
       the "gravity" model parameter will be set to the value 0.8.

       .. note:: Currently this is a conceptual "catch-all" for overriding
          model parameters, for things not specific to the :attr:`.simParams`
          list. In future this approach may be refactored.

    .. attribute:: analysisOps
    # TODO:[ Refactor] remove, StGermain specific

       A list of :class:`credo.analysis.api.AnalysisOperation` that are
       associated with this ModelRun, and will be applied when the
       model is actually run (which involves writing and submitting
       additional StGermain XML).

    .. attribute:: analysisXML
    # TODO:[ Refactor] remove, StGermain specific

       Initally `None`, this will be populated with the filename of the
       additional XML document written containing parameter overrides,
       and requested analysis operations.

    .. attribute:: cpFields
    # TODO:[ Refactor] remove, StGermain specific

       A list of fields that the user wishes to checkpoint in the run.
       Defaults to [], in which case the list (if any) in the model
       run's XML will be left as-is.
    """

    solverOptsRecordFilename = "solverOptsUsed.opt"

    def __init__(self, name, modelInputFiles, outputPath=None, basePath=None,
            logPath=None,
            cpReadPath=None, nproc=1, simParams=None,
            paramOverrides=None, solverOpts=None, xmlExtras=None,
            inputFilePath=None):
        self.name = name
        # Be forgiving if the user passes a single string input file, rather
        # than list
        if isinstance(modelInputFiles, str):
            modelInputFiles = [modelInputFiles]
        self.modelInputFiles = modelInputFiles
        if outputPath is None:
            # Sensible default is output/name
            self.outputPath = os.path.join("output", name)
        else:
            self.outputPath = self.setPath(outputPath)
        if basePath is None:
            # Default to the path of the calling script
            self.basePath = credo.utils.getCallingPath(1)
        else:
            self.basePath = basePath
        self.basePath = os.path.abspath(self.basePath)
        self.cpReadPath = self.setPath(cpReadPath)
        if logPath is None:
            self.logPath = self.outputPath
        else:
            self.logPath = self.setPath(logPath)
        self.jobParams = JobParams(nproc=nproc)
        self.simParams = simParams
        self.paramOverrides = paramOverrides
        if self.paramOverrides == None:
            self.paramOverrides = {}
        checkParamOverridesTypes(self.paramOverrides)
        if self.simParams:
            self.simParams.checkNoDuplicates(self.paramOverrides.keys())
        self.solverOpts = solverOpts
        self.checkSolverOptsFile()
        self.inputFilePath = inputFilePath
        self.analysisOps = {}
        self.cpFields = []
        self.analysisXML = None

    def checkValidRunConfig(self):
        """Check the given modelRun is valid and ready to be run."""
        stgpath.checkAllXMLInputFilesExist(self.modelInputFiles)

        # Pre-run checks for validity - e.g. at least one input file,
        # nproc is sensible value
        if self.simParams:
            self.simParams.checkValidParams()
            self.simParams.checkNoDuplicates(self.paramOverrides.keys())
        if self.solverOpts:
            self.checkSolverOptsFile()
        # TODO: should there be a convention to return anything here, or more
        # explicit Exception handling?

    def checkSolverOptsFile(self):
        if self.solverOpts == None: return
        if not isinstance(self.solverOpts, str):
            raise TypeError("Solver options must be specified as a filename"\
                " string, not type %s." % type(self.solverOpts))
        solverOptsAbs = os.path.join(self.basePath, self.solverOpts)
        if not os.path.exists(solverOptsAbs):
            raise IOError("Solver options file specified, '%s', doesn't"\
                " exist relative to base path %s." % \
                (self.solverOpts, self.basePath))

    def preRunPreparation(self):
        """Do any preparation necessary before the run itself proceeds."""
        # Do necessary pathing preparation
        self.prepareOutputLogDirs()
        # Now create the XML file for custom analysis commands
        self.analysisXMLGen()

    def getModelRunAppExeCommand(self):
        """Return the full path of the executable of the modelling program.
        (e.g. "/usr/local/bin/StGermain") """
        return stgpath.getVerifyStgMainExecutablePath()

    def getModelRunCommand(self, extraCmdLineOpts=None,
            absXMLPaths=False):
        """Given a model run, construct the command needed to run that model,
        and return as a string.

        :keyword extraCmdLineOpts: any extra command line options, to be
          passed straight through to the model.
        :keyword absXMLPaths: if True, converts any Model XML input files to
          absolute paths first in cmd line."""
        runExe = self.getModelRunAppExeCommand()
        stgRunStr = "%s " % (runExe)
        if absXMLPaths == False:
            inputFiles = self.modelInputFiles
        else:
            inputFiles = [os.path.join(self.basePath, iFile) for iFile in \
                self.modelInputFiles]
            inputFiles = map(os.path.abspath, inputFiles)
        stgRunStr = " ".join([runExe] + inputFiles)
        if self.analysisXML:
            if absXMLPaths == False:
                stgRunStr += " " + self.analysisXML
            else:
                stgRunStr += " " + os.path.abspath(self.analysisXML)

        stgRunStr += " " + credo.modelrun.getParamOverridesAsStr(
            self.paramOverrides)
        if self.solverOpts:
            stgRunStr += " " + stgcmdline.solverOptsStr(self.solverOpts)
        if extraCmdLineOpts:
            stgRunStr += " " + extraCmdLineOpts
        return stgRunStr

    def postRunCleanup(self):
        """function designed to be run after a modelRun has completed, and will
        do any post-run cleanup to get ready for analysis - e.g. moving files
        into the output directory that were created to configure the run and
        need to be kept."""
        absOutputPath = os.path.join(self.basePath, self.outputPath)
        if not os.path.exists(absOutputPath):
            os.makedirs(absOutputPath)

        shutil.move(self.analysisXML,
            os.path.join(absOutputPath, self.analysisXML))

        # Keep a record of any solver options used.
        if self.solverOpts:
            soCopyPath = os.path.join(absOutputPath,
                SOLVER_OPTS_RECORD_FILENAME)
            shutil.copy(self.solverOpts, soCopyPath)

        # Allow all analysis operators to do any post-run cleanup
        for opName, analysisOp in self.analysisOps.iteritems():
            analysisOp.postRun(self, self.basePath)

        try:
            self.customPostRunCleanup(self)
        except AttributeError:
            # If this hook isn't implemented, keep going.
            pass

    def defaultModelRunFilename(self):
        """Calculates and returns a default filename for the ModelRun's XML
        record filename."""
        return 'ModelRun-'+self.name+'.xml'

    def prepareOutputLogDirs(self):
        """Prepare the output and log dirs - usually in preparation
        for running a :class:`credo.modelrun.ModelRun`."""
        absOutputPath = os.path.join(self.basePath, self.outputPath)
        if not os.path.exists(absOutputPath):
            os.makedirs(absOutputPath)

        absLogPath = os.path.join(self.basePath, self.logPath)
        if not os.path.exists(absLogPath):
            os.makedirs(absLogPath)

    def getStdOutFilename(self):
        """Get the name of the file this Model's stdout needs to/has been
        saved to."""
        return os.path.join(self.logPath, "%s.stdout" % self.name)

    def getStdErrFilename(self):
        """Get the name of the file this Model's stderr needs to/has been
        saved to."""
        return os.path.join(self.logPath, "%s.stderr" % self.name)

    def setPath(self, inPath):
        """Do any needed manipulations when setting paths.
        """
        if inPath == None:
            return None
        else:
            return inPath

    def getSimParams(self):
        """Utility function to get SimParams - since in the current design
        the self.simParams parameter may be 'None', and we need to read
        from the model XML."""
        if self.simParams is not None:
            simParams = self.simParams
        else:
            simParams = SimParams()
            paramOverridesStr = getParamOverridesAsStr(self.paramOverrides)
            simParams.readFromStgXML(self.modelInputFiles, self.basePath,
                paramOverridesStr)
        return simParams

    def writeInfoXML(self, writePath="", filename="", update=False,
            prettyPrint=True):
        """Writes an XML recording the key details of this ModelRun, in CREDO
        format - useful for benchmarking etc.

        `writePath` and `filename` can be specified, if not they will use
        default values (the outputPath of the model, and the value returned by
        :attr:`defaultModelRunFilename()`, respectively)."""
        if filename == "":
            filename = self.defaultModelRunFilename()
        if writePath == "":
            writePath=os.path.join(self.basePath, self.outputPath)
        writePath+=os.sep

        # create XML document
        root = etree.Element('StgModelRun')
        xmlDoc = etree.ElementTree(root)
        # Write key entries:
        # Model description (grab from XML file perhaps)
        name = etree.SubElement(root, 'name')
        name.text = self.name
        filesList = etree.SubElement(root, 'modelInputFiles')
        for xmlFilename in self.modelInputFiles:
            modFile = etree.SubElement(filesList, 'inputFile')
            modFile.text = xmlFilename
        etree.SubElement(root, 'basePath').text = self.basePath
        etree.SubElement(root, 'outputPath').text = self.outputPath
        if self.cpReadPath:
            etree.SubElement(root, 'cpReadPath').text = self.cpReadPath
        self.jobParams.writeInfoXML(root)
        if not self.simParams:
            # In this case:
            # We will write a copy of the simParams read from actual model
            # XMLs, plus the over-ride parameters)
            simParams = self.getSimParams()
            simParams.writeInfoXML(root)
        else:
            self.simParams.writeInfoXML(root)

        writeParamOverridesInfoXML(self.paramOverrides, root)
        writeSolverOptsInfoXML(self.solverOpts, root)

        analysisNode = etree.SubElement(root, 'analysisOps')
        for opName, analysisOp in self.analysisOps.iteritems():
            analysisOp.writeInfoXML(analysisNode)
        # TODO : write info on cpFields?
        # Write the file
        if not os.path.exists(writePath):
            os.makedirs(writePath)
        outFile = open(writePath+filename, 'w')
        writeXMLDoc(xmlDoc, outFile, prettyPrint)
        outFile.close()
        return writePath+filename

    def analysisXMLGen(self, filename=None):
        """Generates an XML file, in StGermainData XML format, to over-ride
        necessary parameters of the model as specified on this ModelRun
        instance. Returns the name of the just-written XML file.

        Overrides can have the following main sources:

        * Over-ridden simulation parameters that have been specified
          as members of the ModelRun itself, such as cpReadPath, and cpFields;
        * Over-ridden simulation parameters on this ModelRun's SimParams
          attribute (if it exists);
        * Requested analysis operations that've been added to the ModelRun,
          as specified in the self.analysisOps member list.

        .. note::
           Remember that as well as those overrides written to this XML,
           the user can over-ride particular parameters in the ModelRun via the
           command line by setting the self.paramOverrides member dictionary.
        """
        xmlDoc, root = stgxml.createNewStgDataDoc()
        # Write key entries:
        stgxml.writeParam(root, 'outputPath', self.outputPath, mt='replace')
        if self.cpReadPath:
            stgxml.writeParam(root, 'checkpointReadPath', self.cpReadPath,
                mt='replace')
        if self.simParams:
            self.simParams.writeStgDataXML(root)
        for analysisName, analysisOp in self.analysisOps.iteritems():
            analysisOp.writeStgDataXML(root)

        # This is so we can checkpoint fields list: defined in FieldVariable.c
        if len(self.cpFields):
            # Have used the Merge mergeType, because the solvers for the
            # models in use may have a minimum set of fields to checkpoint.
            stgxml.writeParamList(root, 'FieldVariablesToCheckpoint',
                self.cpFields, mt='merge')

        if filename is None:
            #By default, store this file in the output path.
            absOutputPath = os.path.join(self.basePath, self.outputPath)
            if not os.path.exists(absOutputPath):
                os.makedirs(absOutputPath)
            filename = os.path.join(absOutputPath,
                CREDO_ANALYSIS_RECORD_FILENAME)
        stgxml.writeStgDataDocToFile(xmlDoc, filename)
        self.analysisXML = filename
        return filename

    def genFlattenedXML(self, cmdLineOverrides=None, flatFilename=None):
        self.analysisXMLGen()
        xmls = self.modelInputFiles + [self.analysisXML]
        overridesStr = getParamOverridesAsStr(self.paramOverrides)
        if cmdLineOverrides != None:
            overridesStr = " ".join([overridesStr, cmdLineOverrides])

        fFilename = stgxml.createFlattenedXML(xmls, overridesStr,
            flatFilename=flatFilename)
        return fFilename

class JobParams(dict):
    """Small class, to record parameters that specify job control of a ModelRun,
    such as numbers of processors used.

    All attributes are stored as regular dictionary parameters, to facilitate
    easy updating.
    """
    def __init__(self, **kwargs):
        # allow special handling of maxRunTime
        if 'maxRunTime' in kwargs and isinstance(kwargs['maxRunTime'], timedelta):
            mrTime = kwargs['maxRunTime']
            # Convert to a flat seconds number
            kwargs['maxRunTime'] = mrTime.days * 24 * 3600 + mrTime.seconds
        dict.__init__(self, kwargs)
        if 'nproc' not in self.keys():
            self['nproc'] = DEF_NPROC
        if 'maxRunTime' not in self.keys():
            self['maxRunTime'] = DEF_MAX_RUN_TIME
        if 'pollInterval' not in self.keys():
            self['pollInterval'] = DEF_POLL_INTERVAL

    def writeInfoXML(self, parentNode):
        '''Writes information about this class into an existing, open XML
         doc node, in a child list'''
        # TODO: perhaps could change to a general function later
        # for writing Python dicts to my preferred XML system
        jpNode = etree.SubElement(parentNode, 'jobParams')
        self._writeInfoXML_Recurse(jpNode, self)

    def _writeInfoXML_Recurse(self, baseNode, paramDict):
        for kw, value in paramDict.iteritems():
            if isinstance(value, dict):
                subDict = value
                #Write a hierarchical sub-dict
                dictNode = etree.SubElement(baseNode, kw)
                self._writeInfoXML_Recurse(dictNode, subDict)
            else:
                etree.SubElement(baseNode, kw).text = str(value)


class StgParamInfo:
    '''A simple Class that keeps track of the type of a StgParam, and it's full
    name.

    .. attribute:: stgName

       The name of this parameter used in the StGermain dictionary and Model
       XML files.

    .. attribute:: pType

       Type of this parameter (will be used in casting etc).

    .. attribute:: defVal

       Default value of the parameter.
    '''
    def __init__(self, stgName, pType, defVal):
        self.stgName = str(stgName)
        assert isinstance(pType, type)
        assert pType in _allowedModelParamTypes
        self.pType = pType
        # Allow None as a special value, else the default value should be of
        # correct type during construction
        if defVal is not None:
            assert isinstance(defVal, self.pType)
        self.defVal = defVal

    def checkType(self, value):
        """Checks that the value is of the correct type of this parameter."""
        if (value is not None) and (not isinstance(value, self.pType)):
            raise ValueError("Tried to set StgParam \"%s\" to %s, of type %s,"\
                "but this param is of type %s" % \
                (self.stgName, str(value), str(type(value)), str(self.pType)))


class SimParams:
    """A class to keep records about the simulation parameters used for a
     StgDomain/Underworld Model Run, such as number of timesteps to run for.
     Has functionality to save this list to an XML record, and also read
     them from a StGermain XML.

     After construction, it will make all these parameters directly available
     as attributes of the SimParams object.

     .. attribute:: stgParamInfos

        A dictionary of :class:`.StgParamInfo`, specifying which parameters
        are actually controlled by this class. The keys are the short-hand
        names which can be used to refer to them, as well as Stgermain names."""

    stgParamInfos = { \
        'nsteps':StgParamInfo("maxTimeSteps", int, None), \
        'stoptime':StgParamInfo("stopTime",float, None), \
        'cpevery':StgParamInfo("checkpointEvery",int, 100), \
        'dumpevery':StgParamInfo("dumpEvery",int, 1), \
        'restartstep':StgParamInfo("restartTimestep",int, None) }

    def __init__(self, **kwargs):
        for paramName, stgParamInfo in self.stgParamInfos.iteritems():
            self.setParam(paramName, stgParamInfo.defVal)

        # Set all parameters provided to init function
        for param, val in kwargs.iteritems():
            paramFound = False
            # Allow the user to set by param name on this class, or actual name
            if param in self.stgParamInfos.keys():
                paramFound = True
                self.setParam(param, val)
            else:
                for paramName, stgParamInfo in self.stgParamInfos.iteritems():
                    if param == stgParamInfo.stgName:
                        paramFound = True
                        self.setParam(paramName, val)
                        break

            if paramFound == False:
                valueErrorStr = "provided Sim Parameter '%s' not in allowed"\
                    " list of parameters to set, which is %s" %\
                    (param, self.stgParamInfos.keys())
                raise ValueError(valueErrorStr)

    def setParam(self, paramName, val):
        assert paramName in self.stgParamInfos.keys()
        self.__dict__[paramName] = val
        self.stgParamInfos[paramName].checkType(val)

    def getParam(self, paramName):
        """Get the value of a parameter with given paramName."""
        return self.__dict__[paramName]

    def checkValidParams(self):
        """Checks that the parameter set is valid to run a StGermain model
        (e.g. that either the stop time, or total number of steps, is set)."""
        if (self.nsteps is None) and (self.stoptime is None):
            raise ValueError("neither nsteps nor stoptime set")

    def checkNoDuplicates(self, paramOverridesList):
        """Function to check there are no duplicates between sim param
        overrides set, and cmd-line parameter overrides."""

        stgParamNamesSet = [simPInfo.stgName for simPInfo in \
            self.stgParamInfos.itervalues()]

        for modelPath in paramOverridesList:
            if modelPath in stgParamNamesSet:
                raise ValueError("Parameter '%s' found in both the model's"\
                    " SimParams class and the paramater override list. Please"\
                    " use only one of these methods for setting the parameter."\
                    % modelPath)

    def nearestDumpStep(self, finalStep, inputStep):
        """Utility method to get the nearest step at which a dump result
        was created."""
        dEvery = self.dumpevery
        lastImgStep = finalStep / dEvery * dEvery
        nearestDumpStep = int(round(inputStep / float(dEvery))) * dEvery
        nearestDumpStep = min([nearestDumpStep, lastImgStep])
        return nearestDumpStep

    def writeInfoXML(self, parentNode):
        '''Writes information about this class into an existing, open XML doc
         node, in a child list'''
        spNode = etree.SubElement(parentNode, 'simParams')
        for param in self.stgParamInfos:
            assert(param in self.__dict__)
            etree.SubElement(spNode, param).text = str(self.__dict__[param])

    def writeStgDataXML(self, xmlNode):
        '''Writes the parameters of this class as parameters in a StGermain
         XML file'''
        for paramName, stgParam in self.stgParamInfos.iteritems():
            val = self.getParam(paramName)
            if val is not None:
                stgxml.writeParam(xmlNode, stgParam.stgName, val,\
                    mt='replace')

    def readFromStgXML(self, inputFilesList, basePath, cmdLineOverrides):
        '''Reads all the parameters of this class from a given StGermain
        set of input files'''
        absInputFiles = stgpath.convertLocalXMLFilesToAbsPaths(
            inputFilesList, basePath)
        ffile=stgxml.createFlattenedXML(absInputFiles, cmdLineOverrides)
        xmlDoc = etree.parse(ffile)
        stgRoot = xmlDoc.getroot()
        for param, stgParam in self.stgParamInfos.iteritems():
            # some of these may be none, but is ok since will check below
            val = stgxml.getParamValue(stgRoot, stgParam.stgName,\
                stgParam.pType)
            self.setParam(param, val)

        self.checkValidParams()
        os.remove(ffile)

# Stuff for managing a paramOverrides list
# TODO: as a class, sub-classing dict?

def checkParamOverridesTypes(paramOverrides):
    """Checks that, for a given list of paramOverrides, each is of a valid
    type that can actually be successfully used in a StGermain dictionary."""
    for modelPath, paramVal in paramOverrides.iteritems():
        if type(paramVal) not in _allowedModelParamTypes:
            raise ValueError("One of the parameters in paramOverrides"\
                " list, '%s', has value '%s', of type '%s', which"\
                " isn't in allowed types list [%s]"\
                % (modelPath, str(paramVal), type(paramVal),\
                _allowedModelParamTypes))

def getParamOverridesAsStr(paramOverrides):
    """Given a list of parameter overrides, return these as a string ready for
    passing to StGermain on the command line. """
    if paramOverrides == []: return ""

    checkParamOverridesTypes(paramOverrides)
    paramOverridesStr = ""
    #create the string in sorted order, for tidiness and user-friendliness
    modelPaths = paramOverrides.keys()
    modelPaths.sort()
    overrideStrs = []
    for modelPath in modelPaths:
        paramVal = paramOverrides[modelPath]
        overrideStrs.append(stgcmdline.paramStr(modelPath, paramVal))
    paramOverridesStr = " ".join(overrideStrs)
    return paramOverridesStr


def writeParamOverridesInfoXML(paramOverrides, parentNode):
    """Writes a record, under the given parentNode, of all the
    parameter overrides specified in the list paramOverrides."""
    paramOversNode = etree.SubElement(parentNode, 'paramOverrides')
    for modelPath, paramVal in paramOverrides.iteritems():
        paramNode = etree.SubElement(paramOversNode, 'param')
        paramNode.attrib['modelPath'] = modelPath
        paramNode.attrib['paramVal'] = str(paramVal)

#TODO: does this solverOpts stuff need to be a class?
def writeSolverOptsInfoXML(solverOpts, parentNode):
    """Writes a record, under the given parentNode, of the
    solver options file used."""
    solverOptsNode = etree.SubElement(parentNode, 'solverOpts')
    if solverOpts is not None:
        solverOptsNode.text = solverOpts

##################

def strRes(resTuple):
    '''Turn a given tuple of resolutions into a string, suitable for using
     as an output dir'''
    assert len(resTuple) in range(2,4)
    resStr = ""
    for res in resTuple[:-1]: resStr += str(res)+"x"
    resStr += str(resTuple[-1])
    return resStr

def generateResOpts(resTuple):
    '''Given a tuple of desired resolutions for a model, convert this to
    options to pass to StG on the command line'''
    # ResParams should probably be part of a useful struct/dict stored in
    # standard place.
    resParams=["elementResI","elementResJ","elementResK"]
    assert len(resTuple) in range(2,4)
    resOptsStr=""
    for ii in range(len(resTuple)):
        resOptsStr += stgcmdline.paramStr(resParams[ii],resTuple[ii]) + " "

    # This is to ensure, since we're overriding, if only 2D model is being
    # run, it ignores any 3rd dimension spec set in the original model file
    resOptsStr += stgcmdline.paramStr("dim",len(resTuple))
    return resOptsStr
