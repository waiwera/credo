#!/usr/bin/env python
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

import getopt
import sys
import os

import credo
from credo import modelrun as mrun
from credo import modelresult as mres
import credo.analysis

defaultFieldTol = 3e-2

#process input args

#modelName, options = credo.processInput(argv, argc)
# Keep allowing options file for now in default scripts:- though for a
 # custom script, user could easily write their own
#credo.processOptionsFile(options, "./options.dat")

# This is where we create the key data structure, the mRun.
 # It will be a key data structure storing info about the directories
 # used, timestep, fields checkpointed, and be used in APIs to access info.

opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])

#For now just copy all args as input files
inputFiles = args
modelName, ext = os.path.splitext(args[0])
# Do the following live on an options struct?
outputPath = 'output/'+modelName
nproc=1

resSet = [(10,10),(20,20),(30,30),(40,40)]

print "Running all resolutions in resolution set:"
print resSet

for res in resSet:
    mOutputPath = outputPath+os.sep+mrun.strRes(res)

    mRun = mrun.ModelRun(modelName, inputFiles, mOutputPath, nproc=nproc)

    customOpts = mrun.generateResOpts(res)

    # For analytic test, assume the user has specified what fields to
    # analyse in the XML
    # (In the background this will generate the flattened XML for the model
    mRun.analysis['fieldTests'] = mrun.getXMLFieldTestInfo(mRun.modelInputFiles)
    # Set all field tolerances at once. Of course, should allow this
    # to be over-ridden
    mRun.setAllFieldTolerances(defaultFieldTol)

    mrun.writeModelRunXML(mRun)

    # This will generate an additional XML to require StGermain/Underworld
    # to do any requested extra analysis (eg compare fields), and run
    # for the appropriate number of timesteps etc.
    mRun.analysisXML = mrun.analysisXMLGen(mRun)

    credo.prepareOutputLogDirs(mRun.outputPath, mRun.logPath)

    # This will run the model, and also save basic results (e.g. walltime)
    results = mrun.runModel(mRun, customOpts)

    # TODO: This step necessary since currently convergence files saved
    # in directory of run,
    # may be better handled within the runModel
    credo.moveConvergenceResults(os.getcwd(), mRun.outputPath)
    results.fieldResults = \
        mrun.analysis['fieldTests'].testConvergence(mRun.outputPath)
    mres.writeModelResultsXML(results, path=mRun.outputPath)

    #Now do any required post-processing, depending on type of script
    credo.cleanupOutputLogDirs(mRun.outputPath, mRun.logPath)
