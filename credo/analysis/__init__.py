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


"""
The CREDO Analysis module is to group together tools for analysis of the
results of Underworld models: for use in both individual user scripts, and as
part of system testing (see :mod:`credo.systest`).

For analysis operations that are designed to be added to
:class:`~credo.modelrun.ModelRun` instances, and possibly used as part of
system testing, these should inherit from
:class:`~credo.analysis.api.AnalysisOperation`.
There are also several functions
that can be used to access and post-process Underworld results in a more direct
manner, using the :mod:`credo.io` interface.

For examples of using the analysis operations with models, see the
:ref:`credo-examples-analysis` section of the documentation.
"""

from credo.analysis.api import *
