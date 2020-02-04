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

fCompListMgr = FieldCompListMgr()

# if reading from XML
fCompListMgr.readFromStgXML()
# means we can now access fCompListMgr.fieldCompares

# Comparing two straight fields.
fComp = FieldCompare("VelocityField", "PressureField")

# Comparing against analytic
tempAnalytic = AnalyticPluginField("StgFEM_CosineHillRotate", 0)
fComp = FieldCompare("TemperatureField", tempAnalytic)
0)

# Comparing against reference
tempRef = ReferenceField("PressureField", "expected/Multigrid-referenceTest")
fComp = FieldCompare("PressureField", tempRef)

# TODO: how do we write Stg XML - and package the individual ops into a list?
for fComp in [fComp1, fComp2, fComp3]:
    fCompListMgr.add(fComp)

fCompListMgr.writeStgXML()

# Qtns: does the above suggest the fields will actually operable in Python, i.e.
# to get out data from them?

# Get results

fCompRes = fCompOp.getResult()
# fCompRes then contains convergence info ...

# Operate on result?
status = fCompRes.checkWithinTol( 0.1, "last" )
fCompRes.plotOverTime()
fComp.writeInfoXML()
fCompRes.writeInfoXML()

# Or general funcs?
fields.plotOverTime(fComp, fCompRes)
fields.writeInfoXML(fComp, fCompRes)
