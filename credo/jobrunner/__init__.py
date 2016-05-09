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

"""This module allows running CREDO jobs using various approaches - e.g. via
MPI locally, via PBS scripts in a queueing system, or via grid submission."""

from credo.jobrunner.simplejobrunner import SimpleJobRunner, SimpleJobMetaInfo
from credo.jobrunner.pbsjobrunner import PBSJobMetaInfo

jobMetaInfoMapping = {
    "Simple": SimpleJobMetaInfo,
    "PBS": PBSJobMetaInfo}

def jobMetaInfoFactoryCreate(runTypeStr):
    jmiClass = jobMetaInfoMapping[runTypeStr]
    jobMetaInfo = jmiClass()
    return jobMetaInfo

def defaultRunner():
    defRunner = SimpleJobRunner()
    return defRunner

def readJobMetaInfoFromXMLNode(jmiNode):
    runTypeStr = jmiNode.find('runType').text
    jobMetaInfo = jobMetaInfoFactoryCreate(runTypeStr)
    jobMetaInfo.readFromXMLNode(jmiNode)
    return jobMetaInfo
