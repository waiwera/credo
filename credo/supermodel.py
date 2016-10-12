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

DEFAULT_COMMAND = "supermodel"

class SuperModelRun(ModelRun):
    """ for supermodel

    TODO: should I add suport of .ordering_map? Supermodel does not use dummy
    blocks.
    """
    def __init__(self, name, input_filename,
                 fieldname_map=None,
                 simulator=DEFAULT_COMMAND,
                 basePath=None, outputPath=None, logPath=None,
                 ):
        super(SuperModelRun, self).__init__(name, basePath, outputPath, logPath)

        self._input_filename = input_filename
        self._simulator = simulator

        self._fieldname_map = fieldname_map

    def getModelRunCommand(self, extraCmdLineOpts=None):
        """ Note: this is called AFTER .preRunPreparation() """
        if self._input_filename:
            return " ".join([self._simulator, self._input_filename])
        else:
            return self._simulator

    def createModelResult(self):
        """ Note: this is called AFTER .postRunCleanup() """
        mres = SuperModelResult(self.name, self.outputPath,
                                self._getH5Filename(),
                                fieldname_map=self._fieldname_map)
        return mres

    def _getH5Filename(self):
        """ Returns the hdf5 output filename of a model run.

        Supermodel's output filename is default to have the same name as the
        input filename, with extension .h5.  It can also be specified by user in
        the input (json) file.
        """
        import json
        import os
        input_fn = os.path.join(self.basePath, self._input_filename)
        try:
            with open(input_fn, 'r') as jf:
                jdata = json.load(jf)
            h5_fn = jdata['output']['filename']
        except KeyError:
            h5_fn = os.path.splitext(input_fn) + '.h5'
        return h5_fn

class SuperModelResult(ModelResult):
    """ for supermodel
    """
    def __init__(self, name, outputPath, h5_filename,
                 fieldname_map=None):
        from os.path import dirname
        super(SuperModelResult, self).__init__(name, outputPath,
                                               fieldname_map=fieldname_map)
        self.name = name

        import h5py
        # have to keep it open, unless copy all data, which is not ideal.
        self._data = h5py.File(h5_filename, 'r')
        # obtain slicing arrays for converting values back to natural ordering
        self.cell_idx = self._data['cell_interior_index'][:,0] # cell_fields/*
        self.geom_idx = self._data['cell_index'][:,0] # fields/cell_geometry

    def _getFieldAtOutputIndex(self, field, outputIndex):
        return self._data['cell_fields'][field][outputIndex][self.cell_idx]

    def _getFieldHistoryAtCell(self, field, cellIndex):
        return self._data['cell_fields'][field][:,cellIndex]

    def _getPositions(self):
        # cannot do self._data['fields'][cell_geometry][self.geom_idx,:3]
        # it would have to be in increasing order
        return self._data['fields']['cell_geometry'][:,:3][self.geom_idx]

    def _getTimes(self):
        return self._data['time']