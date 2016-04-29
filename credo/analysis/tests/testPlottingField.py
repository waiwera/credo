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

from credo.modelresult import ModelResult
from credo.analysis.fields import FieldComparisonOp, FieldComparisonList
from credo.io import stgcvg

fComps = FieldComparisonList()
fComps.add(FieldComparisonOp('VelocityField'))
# TODO: perhaps should be an interface that doesn't require a full mRes?
mRes = ModelResult("testMod", "./output/realistic")
results = fComps.getAllResults(mRes)

fr = results[0]

fr.plotOverTime(show=True, dofIndex=0, path="./output/realistic")

#Plotting
#dofErrors = stgcvg.getDofErrors_ByDof( fr.cvgFileInfo )

#import matplotlib
#matplotlib.use('Agg')
#import matplotlib.pyplot as plt
#plt.plot(dofErrors[0])
#plt.axhline(y=fr.tol, label='tolerance', linewidth=3, color='r')
#plt.xlabel("Timestep")
#plt.ylabel("Error vs analytic soln")
#plt.title("Convergence of field '%s', dof %d, with analytic solution"
#    % (fr.fieldName,0))
#plt.savefig(fr.fieldName+"-cvg.png",format="png")
#plt.show()
