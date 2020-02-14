from __future__ import print_function
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

import matplotlib.pyplot as plt
import credo.analysis.fields as fields
from credo.systest.fieldCvgWithScaleTC import *
import credo.analysis.fields as fields

# Convergence checker
# StgFEM case
print("\n** Results from real StgFEM data - from a Convergence file**")
cvgFilePath = "./output/cvgTest"
lenScales, fErrorData = fields.getFieldScaleCvgData_SingleCvgFile(cvgFilePath)
overallRes = testAllCvgWithScale(lenScales, fErrorData,
    defFieldScaleCvgCriterions)

velCvg = fields.calcFieldCvgWithScale("VelocityField", lenScales,
     fErrorData["VelocityField"])
pCvg = fields.calcFieldCvgWithScale("PressureField", lenScales,
     fErrorData["PressureField"])

velResult = testCvgWithScale("VelocityField", velCvg,
    defFieldScaleCvgCriterions["VelocityField"])
pResult = testCvgWithScale("PressureField", pCvg,
     defFieldScaleCvgCriterions["PressureField"])
