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
from credo.modelrun import ModelRun, SimParams
import credo.analysis
from credo.analysis.fields import FieldTest

# This test will run a model for n timesteps, checkpointing half-way:- then
#  re-start the model mid way through, and check the values at the end are
#  the same.

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
nproc=1

# For a restart test, these are standard fields to be tested.
modelName+="-restartTest"
outputPath = 'output'+os.sep+modelName
standardFields = ['VelocityField','PressureField']
runSteps=20
assert runSteps % 2 == 0

print "Initial run:"
mRun = ModelRun(modelName+"-initial", inputFiles, outputPath, nproc=nproc)
initialOutputPath = outputPath+os.sep+"initial"
mRun.outputPath = initialOutputPath
mRun.simParams = SimParams(nsteps=runSteps, cpevery=runSteps/2, dumpevery=0)
mRun.cpFields = standardFields

mRun.writeInfoXML()
credo.prepareOutputLogDirs(mRun.outputPath, mRun.logPath)
# This will run the model, and also save basic results (e.g. walltime)
analysisXML = mRun.analysisXMLGen()
results = credo.modelrun.runModel(mRun)
credo.modelresult.writeModelResultsXML(results, path=mRun.outputPath)

print "Restart run:"
mRun.name = modelName+"-restart"
mRun.outputPath = outputPath+os.sep+"restart"
mRun.cpReadPath = initialOutputPath
# Note we could modify existing SimParams rather than create new, but below is
# probably easier
mRun.simParams = SimParams(nsteps=runSteps/2, cpevery=0, dumpevery=0, \
    restartstep=runSteps/2)
fTests = mRun.analysis['fieldTests']
fTests.testTimestep = runSteps
fTests.useReference = True
fTests.referencePath = initialOutputPath
defFieldTol = 1e-5
for fieldName in standardFields:
    fTests.add(FieldTest(fieldName, tol=defFieldTol))

mRun.writeInfoXML()
analysisXML = mRun.analysisXMLGen()
credo.prepareOutputLogDirs(mRun.outputPath, mRun.logPath)
# This will run the model, and also save basic results (e.g. walltime)
results = credo.modelrun.runModel(mRun)

print "Processing results"

# TODO: This step necessary since currently convergence files saved
# in directory of run may be better handled within the runModel
credo.moveConvergenceResults(os.getcwd(), mRun.outputPath)
results.fieldResults = fTests.testConvergence(mRun.outputPath)

credo.modelresult.writeModelResultsXML(results, path=mRun.outputPath)

#Now do any required post-processing, depending on type of script
credo.cleanupOutputLogDirs(mRun.outputPath, mRun.logPath)
