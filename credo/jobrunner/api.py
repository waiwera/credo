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

import platform
import operator
from datetime import timedelta, datetime
from xml.etree import ElementTree as etree
import credo.modelrun
import credo.modelresult
from credo.io import stgcmdline
from credo.io import stgpath

class PerformanceProfiler:
    """Class to use to attach to :class:`JobRunner` instances, which will then
    profile performance of each ModelRun ran by given JobRunner.

    This is an abstract base class, user code will have to select a concrete
    instantiation.

    .startTimer() and .stopTimer() are optional for most profilers, it s really
    only designed for a dumb profiler implemented using pure Python.
    """
    def __init__(self, typeStr):
        self.typeStr = typeStr

    def setup(self, modelName, modelBasePath, modelOutputPath, jobMetaInfo):
        """Do any necessary setup functions."""
        raise NotImplementedError("Error, virtual func on base class")

    def modifyRun(self, modelRun, modelRunCommand, jobMetaInfo):
        raise NotImplementedError("Error, virtual func on base class")

    def startTimer(self):
        pass

    def stopTimer(self):
        pass

    def attachPerformanceInfo(self, jobMetaInfo, modelResult):
        #Open result filename
        #getResDict(filename)
        #Save this resDict on the jobMetaInfo (in a subdirectory)
        raise NotImplementedError("Error, virtual func on base class")


class JobMetaInfo:
    '''A simple class for recording meta info about a job, such as walltime,
    memory usage, etc.

    .. attribute:: simtime

       Simulated time the model ran for.
    '''

    XML_INFO_TAG = "jobMetaInfo"

    def __init__(self, simtime):
        self.runType = None
        self.submitTime = None
        self.platform = {}
        self.performance = {}
        if simtime is None:
            self.simtime = "unknown"
        else:
            self.simtime = float(simtime)
        # Will be used if you pass handlers around.
        self.profilerHandles = {}

    def writeInfoXML(self, xmlNode):
        '''Writes information about this class into an existing, open
         XML doc node'''
        jmNode = etree.SubElement(xmlNode, self.XML_INFO_TAG)
        etree.SubElement(jmNode, 'runType').text = str(self.runType)
        etree.SubElement(jmNode, 'simtime').text = str(self.simtime)
        etree.SubElement(jmNode, 'submitTime').text = str(self.submitTime)
        piNode = etree.SubElement(jmNode, 'platformInfo')
        #Just write out each entry in the platform dictionary.
        for kw, val in self.platform.iteritems():
            etree.SubElement(piNode, kw).text = str(val)
        perfNode = etree.SubElement(jmNode, 'performanceInfo')
        #Just write out each entry in the performance dictionaries
        for profType, subDict in self.performance.iteritems():
            perfProfNode = etree.SubElement(perfNode, "profilerInfo")
            perfProfNode.attrib["profType"] = profType
            for kw, val in subDict.iteritems():
                #TODO: good to save units here as an attrib?
                etree.SubElement(perfProfNode, kw).text = str(val)

    def verbPlatformString(self):
        '''Returns a useful string about the platform, for printing.'''
        return "Node '%s', of type %s, running %s (%s)" \
            % tuple([self.platform[kw] for kw in 'node', 'machine', 'system',
                'release'])

    def readFromXMLNode(self, xmlNode):
        self.simtime = float(xmlNode.find('simtime').text)
        #TODO: how to convert ...
        #self.submitTime = xmlNode.find('submitTime').text
        #TODO: platformInfo
        #TODO: profiler info
        profilersNode = xmlNode.find('performanceInfo')
        for profNode in profilersNode.findall('profilerInfo'):
            profType = profNode.attrib['profType']
            self.performance[profType] = {}
            perfDict = self.performance[profType]
            for profStatNode in profNode:
                # TODO: hack assuming as floats, ideally should read and
                #  handle properly based on some sort of saved unit.
                perfDict[profStatNode.tag] = float(profStatNode.text)
        return

class JobRunner:
    """Class used for running ModelRun instances. This is an abstract base
    class, user code will need to choose a concrete implementation.
    Is designed to allow both serial, and parallel non-blocking job
    submission and reporting.

    .. attribute:: runSuiteNonBlockingDefault

       Determines that for a given job runner, whether suites should be run
       in non-blocking mode by default, or

    .. attribute:: profilers

       List of :class:`.PerformanceProfiler` that will be applied to report
       on any ModelRuns that this JobRunner is used for.

    .. attribute:: defaultProfiler

       Profiler that will be used to provide "default" results in the
       JobMetaInfo.
    """
    def __init__(self):
        self.runSuiteNonBlockingDefault = False
        self.profilers = []
        self.defaultProfiler = None

    def setup(self):
        """Does any necessary setup checks to run models.

        By default, does nothing - sub-classes need to override."""
        pass

    def submitRun(self, modelRun, prefixStr=None, extraCmdLineOpts=None,
            dryRun=False, maxRunTime=None):
        """Submit the job to be run.
        TODO: comment on parameters ...
        Returns: a jobMetaInfo (that can later be attached ... )
        """
        raise NotImplementedError("Error, virtual func on base class")

    def blockResult(self, modelRun, jobMetaInfo):
        """Block on a modelRun until the result is completed ...
        requires appropriate info to be passed in the jobMetaInfo object."""
        raise NotImplementedError("Error, virtual func on base class")

    # TODO: should the args be passed through as unnamed kwArgs,
        # then interpreted by submitRun?
    def runModel(self, modelRun, prefixStr=None, extraCmdLineOpts=None,
            dryRun=False, maxRunTime=None):
        """Run the specified modelRun, and return the ModelResult.

        :param modelRun: the :class:`~credo.modelrun.ModelRun` to be run.
        :keyword prefixStr: optional precursor string for running the model,
           e.g. for timing.
        :keyword extraCmdLineOpts: if specified, these extra cmd line opts will
           be passed through on the command line to the run, extra to any
           :attr:`.ModelRun.simParams` or :attr:`.ModelRun.paramOverrides`.
        :keyword dryRun: If set to True, just print out what *would* be run,
           but don't actually run anything.
        :keyword maxRunTime: maximum time (in seconds) a model should be
          allowed to run for before killing the job.
        :returns: A :class:`~credo.modelresult.ModelResult` recording
          the results of the run."""

        # TODO: handle dryRun at this level...?
        jobMetaInfo = self.submitRun(modelRun, prefixStr,
            extraCmdLineOpts, dryRun, maxRunTime)
        if dryRun is False:
            modelResult = self.blockResult(modelRun, jobMetaInfo)
            return modelResult
        else:
            return None

    def submitSuite(self, modelSuite, prefixStr=None, extraCmdLineOpts=None,
            dryRun=False, maxRunTime=None, writeRecords=True):
        """Submits each modelRun in a suite to be run, and returns a list
        of all jobMetaInfos for the submitted jobs."""
        jobMetaInfos = []
        for runI, modelRun in enumerate(modelSuite.runs):
            if writeRecords == True:
                modelSuite.writeAllModelRunXMLs()
            customOpts = modelSuite.getCustomOpts(runI, extraCmdLineOpts)
            jobMetaInfo = self.submitRun(modelRun, prefixStr, customOpts,
                dryRun, maxRunTime)
            if jobMetaInfo:
                jobMetaInfos.append(jobMetaInfo)
        return jobMetaInfos

    def blockSuite(self, modelSuite, jobMetaInfos):
        """Blocks on each ModelRun in a Suite, given a list of
        JobMetaInfos for each run."""
        modelSuite.resultsList = []
        for modelRun, jobMetaInfo in zip(modelSuite.runs, jobMetaInfos):
            # TODO: ideally if we implemented a "testResult" func, could
            #  loop through and poll/report as they complete,
            #  rather than just in sequential order ...
            result = self.blockResult(modelRun, jobMetaInfo)
            print "ModelRun '%s' complete." % modelRun.name
            assert isinstance(result, credo.modelresult.ModelResult)
            modelSuite.resultsList.append(result)
        return modelSuite.resultsList

    def runSuite(self, modelSuite, prefixStr=None, extraCmdLineOpts=None,
            dryRun=False, maxRunTime=None, runSuiteNonBlocking=None,
            writeRecords=True):
        """Run each ModelRun in the suite - with optional extra cmd line opts.
        Will also write XML records of each ModelRun and ModelResult in the
        suite.

        Input arguments same as for :meth:`.runModel`, except those listed
        below:

        :keyword runSuiteNonBlocking: controls whether the suite will be
           run "non-blocking", i.e. all modelRuns submitted initially, then
           a separate phase to block until they're all completed.

        :keyword writeRecords: sets whether you want each ModelRun in the
           suite, and each ModelResult generated, to automatically write
           an XML record of itself in default location as it is run/produced.

        :returns: a reference to the :attr:`.resultsList` containing all
           the ModelResults generated."""

        print "Running the %d modelRuns specified in the suite" % \
            (len(modelSuite.runs))

        if runSuiteNonBlocking is None:
            runSuiteNonBlocking = self.runSuiteNonBlockingDefault

        if runSuiteNonBlocking:
            jobMetaInfos = self.submitSuite(modelSuite, prefixStr,
                extraCmdLineOpts, dryRun, maxRunTime, writeRecords)
            resultsList = self.blockSuite(modelSuite, jobMetaInfos)
            if writeRecords == True:
                modelSuite.writeAllModelResultXMLs()
            return resultsList
        else:
            modelSuite.resultsList = []
            for runI, modelRun in enumerate(modelSuite.runs):
                if not isinstance(modelRun, credo.modelrun.ModelRun):
                    raise TypeError("Error, stored run %d not an instance of a"\
                        " ModelRun" % runI)
                print "Doing run %d/%d (index %d), of name '%s':"\
                    % (runI+1, len(modelSuite.runs), runI, modelRun.name)
                print "ModelRun description: \"%s\"" % \
                    (modelSuite.runDescrips[runI])

                print "Running the Model (saving results in %s):"\
                    % (modelRun.outputPath)

                customOpts = modelSuite.getCustomOpts(runI, extraCmdLineOpts)
                if writeRecords == True:
                    modelRun.writeInfoXML()
                result = self.runModel(modelRun, prefixStr, customOpts,
                    dryRun, maxRunTime)
                if dryRun == True: continue
                assert isinstance(result, credo.modelresult.ModelResult)
                modelSuite.resultsList.append(result)
                if writeRecords == True:
                    result.writeRecordXML()

        return modelSuite.resultsList

    def attachPlatformInfo(self, jobMI):
        """Attach provenance info relevant to the platform used to run the
        job to the JobMetaInfo object."""
        jobMI.platform = {}
        platInfo = ['system', 'version', 'release', 'machine', 'node']
        aGetter = operator.attrgetter(*platInfo)
        pFuncs = aGetter(platform)
        for prop, pFunc in zip(platInfo, pFuncs):
            jobMI.platform[prop] = pFunc()

    def attachPerformanceInfo(self, jobMI):
        """Attach relevant performance information to the jobMI
        (:class:`~JobMetaInfo`), such as time use,
        memory use, etc"""
        raise NotImplementedError("Error, virtual func on base class")


class ModelRunError(Exception):
    """Base class of ModelRunError exception hierarchy."""
    def __init__(self, modelName):
        self.modelName = modelName


class ModelRunRegularError(ModelRunError):
    """An Exception for when Models fail to run."""
    def __init__(self, modelName, retCode, stdOutFilename, stdErrFilename):
        ModelRunError.__init__(self, modelName)
        self.retCode = retCode
        self.stdOutFilename = stdOutFilename
        self.stdErrFilename = stdErrFilename
        self.tailLen = 20
        stdOutFile = open(stdOutFilename, "r")
        stdErrFile = open(stdErrFilename, "r")
        self.stdErrMsg = stdErrFile.read()
        # TODO: this is a bit inefficient and could be done with proper
        # tail function using seek etc.
        stdOutFileLines = stdOutFile.readlines()
        total = len(stdOutFileLines)
        start = 0
        if total > self.tailLen: start = total - self.tailLen
        self.stdOutFileTail = stdOutFileLines[start:]
        stdOutFile.close()
        stdErrFile.close()

    def __str__(self):
        return "Failed to run model '%s', ret code was %s\n"\
            "Std out and error logs saved to files %s and %s, "\
            "Std error msg was:\n%s\nLast %d lines of std out msg was:\n%s"\
            % (self.modelName, self.retCode,
                self.stdOutFilename, self.stdErrFilename,
                self.stdErrMsg, self.tailLen,
                "".join(self.stdOutFileTail))


class ModelRunTimeoutError(ModelRunRegularError):
    """An Exception for when Models fail to run due to timing out.

    .. attribute:: maxRunTime

       maximum time to run that the model exceeded, in seconds.
    """
    def __init__(self, modelName, stdOutFilename, stdErrFilename,
            maxRunTime):
        ModelRunRegularError.__init__(self, modelName, None, stdOutFilename,
            stdErrFilename)
        self.maxRunTime = maxRunTime

    def __str__(self):
        return "Failed to run model '%s' due to timeout, max time was"\
            " %s\n"\
            "Std out and error logs saved to files %s and %s, "\
            "Std error msg was:\n%s\nLast %d lines of std out msg was:\n%s"\
            % (self.modelName, str(timedelta(seconds=self.maxRunTime)),
                self.stdOutFilename, self.stdErrFilename,
                self.stdErrMsg, self.tailLen,
                "".join(self.stdOutFileTail))

class ModelRunLaunchError(ModelRunError):
    """An Exception for when Models fail to run due to being unable to launch
    the run process in some way.

    .. attribute:: runExecCmd

       command used to launch the job.
    """
    def __init__(self, modelName, runExecCmd, launchHint=None):
        ModelRunError.__init__(self, modelName)
        self.runExecCmd = runExecCmd
        self.launchHint = launchHint

    def __str__(self):
        retStr = "Failed to run model '%s' due to being unable to launch"\
            " run with command '%s'.\n"\
            % (self.modelName, self.runExecCmd)
        if self.launchHint is not None:
            retStr += " (%s)" % self.launchHint
        return retStr

