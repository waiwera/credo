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

from __future__ import print_function
import getopt
import sys
import os
from credo.systest import *
import credo.jobrunner

# Temporary input processing
opts, args = getopt.getopt(sys.argv[1:], "hs", ["help","setup"])

# Temp process options
setupMode = False
for optTuple in opts:
    if optTuple[0] == "--setup":
        setupMode = True

#For now just copy all args as input files
inputFiles = args
modelName, ext = os.path.splitext(args[0])
modelName += "-referenceTest"
outputPath = 'output/'+modelName

refTest = ReferenceTest(inputFiles, outputPath, nproc=1, basePath=os.getcwd())

if setupMode == True:
    print("Running in setup mode only:")
    refTest.regenerateFixture()
    print("Setup completed, exiting.")
    sys.exit()

testRunner = SysTestRunner()
testRunner.runSingleTest(refTest)
