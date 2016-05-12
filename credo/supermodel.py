##  Copyright (C), 2010, Monash University
##  Copyright (C), 2010, Victorian Partnership for Advanced Computing (VPAC)
##  Copyright (C), 2016, University of Auckland
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

""" This module implements the supports for the AUTOUGH2/TOUGH2 simulator.

These classes are concrete implementatins of ModelRun and ModelResult, core
modules for CREDO.  They defines and manages running models of AUTOUGH2
simulator.

This module depends heavily on the PyTOUGH library.

Primary interface is via the :class:`ModelRun`, which enables you to specify,
configure and run a Model, and save records of this as an XML. This process will
produce a :class:`credo.modelresult.ModelResult` class.
"""

from credo.modelrun import ModelRun
from credo.modelresult import ModelResult

DEFAULT_COMMAND = "supermodel.exe"

class SuperModelRun(ModelRun):
    """ for supermodel
    """
    def __init__(self, name, input_filename,
                 simulator=DEFAULT_COMMAND,
                 basePath=None, outputPath=None, logPath=None,
                 ):
        super(SuperModelRun, self).__init__(name, basePath, outputPath, logPath)

        self._input_filename = input_filename
        self._simulator = simulator

    def getModelRunCommand(self, extraCmdLineOpts=None):
        """ Note: this is called AFTER .preRunPreparation() """
        if self._input_filename:
            return " ".join([self._simulator, self._input_filename])
        else:
            return self._simulator

    def createModelResult(self):
        """ Note: this is called AFTER .postRunCleanup() """
        mres = SuperModelResult(self.name, self.outputPath)
        return mres

class SuperModelResult(ModelResult):
    """ for supermodel
    """
    def __init__(self, name, outputPath):
        from os.path import dirname
        super(SuperModelResult, self).__init__(name, outputPath)
        self.name = name

    def getFieldAtStep(self, field, time_step):
        pass

    def getPositions(self):
        pass
