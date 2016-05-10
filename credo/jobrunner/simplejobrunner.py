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

import os
import sys
import signal
import subprocess
import time
import shlex
import operator
from xml.etree import ElementTree as etree
from datetime import timedelta, datetime
from credo.jobrunner.api import *
from credo.modelresult import ModelResult
from credo.modelresult import getSimInfoFromFreqOutput
from credo.jobrunner.unixTimeCmdProfiler import UnixTimeCmdProfiler

# Allow MPI command to be overriden by env var.
MPI_RUN_COMMAND = "MPI_RUN_COMMAND"
DEFAULT_MPI_RUN_COMMAND = "mpiexec"

class SimpleJobMetaInfo(JobMetaInfo):
    def __init__(self):
        JobMetaInfo.__init__(self, 0)
        self.runType = "Simple"
        self.runCommand = None
        self.procHandle = None

    def writeInfoXML(self, xmlNode):
        JobMetaInfo.writeInfoXML(self, xmlNode)
        jmNode = xmlNode.find(self.XML_INFO_TAG)
        etree.SubElement(jmNode, 'runCommand').text = str(self.runCommand)


class SimpleJobRunner(JobRunner):
    def __init__(self, mpi=False):
        JobRunner.__init__(self)
        self.mpi = mpi
        defProfiler = None
        # TODO: perhaps a more declarative approach to choosing profiler
        #  to use better in future than what's below ... e.g. have a profiler
        #  factory that chooses based on platform info, job runner type,
        #  and installed software.
        if sys.platform[0:len("linux")] == "linux":
            # Add at least a UnixTimeCmdProfiler
            defProfiler = UnixTimeCmdProfiler()
            self.profilers.append(defProfiler)
        self.defaultProfiler = defProfiler

    def setup(self):
        # TODO: check mpd is running, if necessary
        pass

    def submitRun(self, modelRun, prefixStr=None, extraCmdLineOpts=None,
            dryRun=False, maxRunTime=None):
        """See :meth:`credo.jobrunner.api.JobRunner.submit`."""
        jobMI = SimpleJobMetaInfo()

        # Navigate to the model's base directory
        startDir = os.getcwd()
        if modelRun.basePath != startDir:
            print "Changing to ModelRun's specified base path '%s'" % \
                (modelRun.basePath)
            os.chdir(modelRun.basePath)

        modelRun.checkValidRunConfig()
        modelRun.preRunPreparation() #This includes finalising input files
        runCommand = self._getRunCommandLine(modelRun, prefixStr,
            extraCmdLineOpts)

        # Run the run command, sending stdout and stderr to defined log paths
        print "Model: \"%s\"" % (modelRun.name)
        print "Command: \"%s\"" % (runCommand)

        # If we're only doing a dry run, return here.
        if dryRun == True:
            os.chdir(startDir)
            return None

        #NB: currently archiving this without the detailed profiler info.
        jobMI.runCommand = runCommand
        self.archiveRunCommand(modelRun, runCommand)

        for profiler in self.profilers:
            profiler.setup(modelRun.name, modelRun.basePath,
                modelRun.outputPath, jobMI)
            #The func below may add extra things to the input files, as well
            #As run command line
            runCommand = profiler.modifyRun(modelRun, runCommand, jobMI)

        # Do the actual run
        runAsArgs = shlex.split(runCommand)
        stdOutFile = open(modelRun.getStdOutFilename(), "w+")
        stdErrFile = open(modelRun.getStdErrFilename(), "w+")
        jobMI.stdOutFile = stdOutFile
        jobMI.stdErrFile = stdErrFile
        jobMI.submitTime = datetime.now()
        try:
            # shell=True needed when using shell features: '<' redirection
            procHandle = subprocess.Popen(runAsArgs, shell=True,
                stdout=stdOutFile, stderr=stdErrFile)
            jobMI.procHandle = procHandle
        except OSError:
            # TODO: [Refactor] this is not always correct? rewrite.
            raise ModelRunLaunchError(modelRun.name, runAsArgs[0],
                "You can set the MPI_RUN_COMMAND env. variable to control"
                " the MPI command used.")

        # TODO: record extra info in "provenance" dict of jobMI,
        #  eg hostname, run command used, prefix, etc...
        if modelRun.basePath != startDir:
            print "Restoring initial path '%s'" % \
                (startDir)
            os.chdir(startDir)
        self.attachPlatformInfo(jobMI)
        return jobMI

    def _getRunCommandLine(self, modelRun, prefixStr, extraCmdLineOpts):
        """ Obtain run command from ModelRun object, if use MPI, related command
        will be added.
        """
        modelRunCommand = modelRun.getModelRunCommand(extraCmdLineOpts)
        # Construct full run line
        if self.mpi:
            if MPI_RUN_COMMAND in os.environ:
                mpiRunCommand = os.environ[MPI_RUN_COMMAND]
            else:
                mpiRunCommand = DEFAULT_MPI_RUN_COMMAND
            mpiPart = "%s -np %d" % (mpiRunCommand,
                modelRun.jobParams['nproc'])
            runCommand = " ".join([mpiPart, modelRunCommand])
        else:
            runCommand = modelRunCommand
        if prefixStr is not None:
            # NB: in the case of MPI runs, we prefix the prefixStr before MPI
            # command and args ... appropriate for things like timing stuff.
            runCommand = " ".join([prefixStr, runCommand])
        return runCommand

    def blockResult(self, modelRun, jobMI):
        # CHeck jobMI is of type MPI ...
        maxRunTime = modelRun.jobParams['maxRunTime']
        pollInterval = modelRun.jobParams['pollInterval']
        procHandle = jobMI.procHandle

        # Navigate to the model's base directory
        startDir = os.getcwd()
        if modelRun.basePath != startDir:
            print "Changing to ModelRun's specified base path '%s'" % \
                (modelRun.basePath)
            os.chdir(modelRun.basePath)

        if maxRunTime == None or maxRunTime <= 0:
            timeOut = False
            retCode = procHandle.wait()
        else:
            if pollInterval > maxRunTime: pollInterval = maxRunTime
            totalTime = 0
            timeOut = True
            while totalTime <= maxRunTime:
                # Note: current strategy in this loop means 'totalTime'
                #  recorded here will only be as accurate as size of
                #  pollInterval.
                #  Thus this is a fall-back for recording time taken.
                time.sleep(pollInterval)
                totalTime += pollInterval
                retCode = procHandle.poll()
                if retCode is not None:
                    timeOut = False
                    break
            if timeOut:
                # At this point, we know the process has run too long.
                # From Python 2.6, change this to procHandle.kill()
                print "Error: passed timeout of %s, sending quit signal." % \
                    (str(timedelta(seconds=maxRunTime)))
                os.kill(procHandle.pid, signal.SIGQUIT)
        # TODO: set finishTime

        # Check status of run (eg error status)
        stdOutFilename = modelRun.getStdOutFilename()
        stdErrFilename = modelRun.getStdErrFilename()
        if timeOut == True:
            raise ModelRunTimeoutError(modelRun.name, stdOutFilename,
                stdErrFilename, maxRunTime)
        if retCode != 0:
            raise ModelRunRegularError(modelRun.name, retCode, stdOutFilename,
                stdErrFilename)
        else:
            # Taking advantage of os.path.join functionality to automatically
            #  over-ride later absolute paths.
            absOutPath = os.path.join(modelRun.basePath, modelRun.outputPath)
            absLogPath = os.path.join(modelRun.basePath, modelRun.logPath)
            print "Model ran successfully (output saved to path %s" %\
                (absOutPath),
            if absLogPath != absOutPath:
                print ", std out & std error to %s" % (absLogPath),
            print ")."

        # Now tidy things up after the run.
        jobMI.stdOutFile.close()
        jobMI.stdErrFile.close()
        print "Doing post-run tidyup:"
        modelRun.postRunCleanup()

        # Construct a modelResult
        mResult = modelRun.createModelResult()
        mResult.jobMetaInfo = jobMI
        try:
            #TODO: the below should be a standard method of ModelResult
            tSteps, simTime = getSimInfoFromFreqOutput(mResult.outputPath)
        except ValueError:
            # For now, allow runs that didn't create a freq output
            tSteps, simTime = None, None
        #Now collect profiler performance info.
        for profiler in self.profilers:
            profiler.attachPerformanceInfo(jobMI, mResult)

        if modelRun.basePath != startDir:
            print "Restoring initial path '%s'" % \
                (startDir)
            os.chdir(startDir)
        return mResult

    def archiveRunCommand(self, modelRun, runCommand):
        """Save the given runCommand to a file in output directory."""
        if not os.path.exists(modelRun.outputPath):
            os.makedirs(modelRun.outputPath)
        fName = os.path.join(modelRun.outputPath, "runCommand.sh")
        f = open(fName, "w")
        f.write("#!/bin/sh\n")
        f.write("cd %s\n" % modelRun.basePath)
        f.write(runCommand+"\n")
        f.close()
        #Set as executable
        os.chmod(fName, 0770)

    def attachPlatformInfo(self, jobMI):
        JobRunner.attachPlatformInfo(self, jobMI)
        # TODO: MPI-specific info.
