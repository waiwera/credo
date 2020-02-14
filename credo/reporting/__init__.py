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

"""This module allows reporting on CREDO's major objects
:class:`credo.systest.api.SysTest` and potentially others like Suites
and Experiments."""
from __future__ import print_function

# This maps acronyms usable in factory method below to modules to use
GenNameToModuleMaps = {
    "RST":"rst", "ReST":"rst", "reST":"rst",
    "ReportLab":"reportLab", "reportLab":"reportLab"}

def getGenerators(genNames, *args, **kwargs):
    """Factory method for getting a list of ReportLab generators"""
    import sys
    generators = []
    for genName in genNames:
        try:
            modName = GenNameToModuleMaps[genName]
        except KeyError:
            raise ValueError("passed in generator name '%s', but this is"\
                " not one of the known report generators (%s)." \
                    % (genName, list(GenNameToModuleMaps.keys())))
        try:
            fullName = "credo.reporting.%s" % modName
            imp = __import__(fullName)
            mod = sys.modules[fullName]
        except ImportError as e:
            print("failed to import and create a generator of type '%s', msg"\
                " was: %s" % (genName, e))
            continue
        generators.append(mod.generator(*args, **kwargs))
    return generators
