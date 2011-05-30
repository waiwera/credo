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
from credo.analysis.fields import FieldTest

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
modelName += "-referenceTest"
# Do the following live on an options struct?
outputPath = 'output'+os.sep+modelName
expectedPath = 'expected'+os.sep+modelName
nproc=1

mRun = ModelRun(modelName, inputFiles, outputPath, nproc=nproc)

# TODO: responsibility of SystemTest class?
createReference = False
# For a reference test, these are standard fields to be tested.
standardFields = ['VelocityField','PressureField']
runSteps=10

if createReference:
    mRun.outputPath = expectedPath
    mRun.simParams = SimParams(nsteps=runSteps, cpevery=runSteps, dumpevery=0)
    mRun.cpFields = standardFields
else:
    mRun.simParams = SimParams(nsteps=runSteps, cpevery=0, dumpevery=0)
    fTests = mRun.analysis['fieldTests']
    fTests.testTimestep = runSteps
    fTests.useReference = True
    fTests.referencePath = expectedPath
    defFieldTol = 1e-2
    for fieldName in standardFields:
        fTests.add(FieldTest(fieldName, tol=defFieldTol))

mRun.writeInfoXML()

# This will generate an additional XML to require StGermain/Underworld to do
# any requested extra analysis (eg compare fields), and run for the
# appropriate number of timesteps etc.
mRun.analysisXMLGen()

credo.prepareOutputLogDirs(mRun.outputPath, mRun.logPath)

# This will run the model, and also save basic results (e.g. walltime)
results = credo.modelrun.runModel(mRun)

if not createReference:
    # TODO: This step necessary since currently convergence files saved
    # in directory of run may be better handled within the runModel
    credo.moveConvergenceResults(os.getcwd(), mRun.outputPath)

    results.fieldResults = fTests.testConvergence(outputPath)

    credo.modelresult.writeModelResultsXML(results, path=mRun.outputPath)

    #Now do any required post-processing, depending on type of script
    credo.cleanupOutputLogDirs(mRun.outputPath, mRun.logPath)
