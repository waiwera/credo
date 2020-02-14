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


"""Collection of utility functions for plotting interesting aspects of models
"""
from __future__ import division
from __future__ import print_function
from builtins import zip
from past.utils import old_div

#!/usr/bin/env python

import os
import operator as op
import credo
try:
    # For why we use Agg backend, see
    # http://matplotlib.sourceforge.net/faq/howto_faq.html#matplotlib-in-a-web-application-server
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
except ImportError:
    print("Error, to use CREDO built-in plot functions, please "\
        " install the matplotlib python library.")

def getValsFromAllRuns(mResults, outputName):
    resVals = [mRes.freqOutput.getValuesArray(outputName) for mRes in mResults]
    return resVals

def plotOverAllRuns(mResults, outputName, depName='Timestep', show=False,
        save=True, path=".", labelNames=True):
    """Create a plot of values over multiple runs."""
    resVals = getValsFromAllRuns(mResults, outputName)
    depVals = getValsFromAllRuns(mResults, depName)
    plot = plt.clf()   # Start by clearing any pre-existing figure
    for ii, mRes in enumerate(mResults):
        lab = "%d" % ii
        if labelNames == True: lab += ": %s" % mRes.modelName
        plt.plot(depVals[ii], resVals[ii], label=lab)
    plt.xlabel(depName)
    plt.ylabel(outputName)
    plt.legend(loc='best')#, prop={'size':'small'})
    plt.title("Output parameter '%s' over %s"\
        % (outputName, depName))
    if save:
        if not os.path.exists(path):
            os.makedirs(path)
        for fmt in ['svg', 'png']:
            filename = os.path.join(path,
                outputName+"-multiRunTimeSeries.%s" % fmt)
            plt.savefig(filename, format=fmt, dpi=120)
    if show: plt.show()
    return plt

def getSpeedups(mRuns, mResults, profilerName=None):
    if profilerName == None:
        #TODO: get a default
        profilerName = "UnixTimeCmd"
    resList = []
    for mRun, mRes in zip(mRuns, mResults):
        nProc = mRun.jobParams["nproc"]
        wallTimeStr = mRes.jobMetaInfo.performance[profilerName]['walltime']
        wallTime = float(wallTimeStr)
        resList.append((nProc, wallTime))
    lowestProcEntry = min(resList)
    lowestProc = lowestProcEntry[0]
    lowestTime = lowestProcEntry[1]
    #NB: if lowestProc == 1 (often will be), then serialTime == lowestTime
    serialTime = lowestTime * lowestProc
    speedups = [old_div(serialTime, res[1]) for res in resList]
    return speedups

def plotSpeedups(mRuns, mResults, profilerName=None, show=False,
        save=True, path=".", showIdeal=True):
    """Plot the speedup of a set of mResults, by processor."""
    nprocs = [mRun.jobParams["nproc"] for mRun in mRuns]
    speedups = getSpeedups(mRuns, mResults, profilerName)
    plot = plt.clf()   # Start by clearing any pre-existing figure
    plt.xlabel("# procs")
    plt.ylabel("speedup")
    #plt.legend(loc='best', prop={'size':'small'})
    plt.plot(nprocs, speedups, "o:", label="actual")
    if showIdeal == True:
        idealProcs = [1, nprocs[-1]]
        idealSpeedup = [1, nprocs[-1]]
        plt.plot(idealProcs, idealSpeedup, "g-", label="ideal")
    plt.ylim(ymin=0)
    plt.title("Parallel Speedup for given runs.")
    plt.legend(loc='best')#, prop={'size':'small'})
    if save:
        if not os.path.exists(path):
            os.makedirs(path)
        for fmt in ['svg', 'png']:
            filename = os.path.join(path,
                "speedups.%s" % fmt)
            plt.savefig(filename, format=fmt, dpi=120)
    if show: plt.show()
    return plt

def getNumEls(mRun):
    """Calculate the number of elements used by a model run."""
    #TODO: this should be abstracted a service of models perhaps ...
    #res = mRun.getResolution()
    from credo.io import stgxml
    from credo.io import stgpath
    import credo.modelrun as mrun
    from xml.etree import ElementTree as etree
    paramOverridesStr = mrun.getParamOverridesAsStr(mRun.paramOverrides)
    iFiles = mRun.modelInputFiles
    if mRun.analysisXML is not None: iFiles += [mRun.analysisXML]
    absInputFiles = stgpath.convertLocalXMLFilesToAbsPaths(
        iFiles, mRun.basePath)
    ffile = stgxml.createFlattenedXML(absInputFiles, paramOverridesStr)
    xmlDoc = etree.parse(ffile)

    stgRoot = xmlDoc.getroot()
    resX = stgxml.getParamValue(stgRoot, "elementResI", int)
    resY = stgxml.getParamValue(stgRoot, "elementResJ", int)
    resZ = stgxml.getParamValue(stgRoot, "elementResK", int)
    if resZ == 0: resZ = 1  #(Just in case)
    numEls = resX * resY * resZ
    return numEls

def getTimePerEls(mRuns, mResults, profilerName=None):
    if profilerName == None:
        #TODO: get a default
        profilerName = "UnixTimeCmd"
    runInfos = []
    for mRun, mRes in zip(mRuns, mResults):
        numEls = getNumEls(mRun)
        wallTimeStr = mRes.jobMetaInfo.performance[profilerName]['walltime']
        wallTime = float(wallTimeStr)
        runInfos.append((numEls, wallTime))
    timePerEls = [old_div(r[1], r[0]) for r in runInfos]
    return timePerEls

def plotTimePerEls(mRuns, mResults, profilerName=None, show=False,
        save=True, path=".", showIdeal=True):
    """Plot the speedup of a set of mResults, by processor."""
    nEls = [getNumEls(mRun) for mRun in mRuns]
    timePerEls = getTimePerEls(mRuns, mResults, profilerName)
    plot = plt.clf()   # Start by clearing any pre-existing figure
    plt.xlabel("# elements")
    plt.ylabel("time(s)/element")
    #plt.legend(loc='best', prop={'size':'small'})
    plt.plot(nEls, timePerEls, "o:", label="actual")
    plt.ylim(ymin=0)
    plt.title("Solver time/model element, given runs.")
    plt.legend(loc='best')#, prop={'size':'small'})
    if save:
        if not os.path.exists(path):
            os.makedirs(path)
        for fmt in ['svg', 'png']:
            filename = os.path.join(path,
                "timePerEls.%s" % fmt)
            plt.savefig(filename, format=fmt, dpi=120)
    if show: plt.show()
    return plt

def plotWalltimesByRuns(mRuns, mResults, profilerName=None, show=False,
        save=True, path=".", showIdeal=True):
    if profilerName == None:
        #TODO: get a default
        profilerName = "UnixTimeCmd"
    nEls = [getNumEls(mRun) for mRun in mRuns]
    walltimes = [mRes.jobMetaInfo.performance[profilerName]['walltime'] \
        for mRes in mResults]
    plot = plt.clf()   # Start by clearing any pre-existing figure
    plt.xlabel("# elements")
    plt.ylabel("walltime(s)")
    #plt.legend(loc='best', prop={'size':'small'})
    plt.plot(nEls, walltimes, "o:", label="actual")
    plt.ylim(ymin=0)
    plt.title("Walltime against # elements - given runs.")
    plt.legend(loc='best')#, prop={'size':'small'})
    if save:
        if not os.path.exists(path):
            os.makedirs(path)
        for fmt in ['svg', 'png']:
            filename = os.path.join(path,
                "walltimeVsNumEls.%s" % fmt)
            plt.savefig(filename, format=fmt, dpi=120)
    if show: plt.show()
    return plt
