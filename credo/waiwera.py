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

DEFAULT_COMMAND = "waiwera"

class WaiweraModelRun(ModelRun):
    """ for Waiwera

    TODO: should I add suport of .ordering_map? Waiwera does not use dummy
    blocks.
    """
    def __init__(self, name, input_filename,
                 fieldname_map={},
                 simulator=DEFAULT_COMMAND,
                 basePath=None, outputPath=None, logPath=None,
                 ):
        super(WaiweraModelRun, self).__init__(name, basePath, outputPath, logPath)

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
        mres = WaiweraModelResult(self.name, self.outputPath,
                                self._getH5Filename(),
                                input_filename=self._input_filename,
                                fieldname_map=self._fieldname_map)
        return mres

    def _getH5Filename(self):
        """ Returns the hdf5 output filename of a model run.

        Waiwera's output filename is default to have the same name as the
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

class WaiweraModelResult(ModelResult):
    """ for Waiwera
    """
    def __init__(self, name, outputPath, h5_filename, input_filename=None,
                 fieldname_map={}):
        from os.path import dirname
        super(WaiweraModelResult, self).__init__(name, outputPath,
                                               fieldname_map=fieldname_map)
        self.name = name

        import h5py
        # have to keep it open, unless copy all data, which is not ideal.
        self._data = h5py.File(h5_filename, 'r')
        # obtain slicing arrays for converting values back to natural ordering
        self.cell_idx = self._data['cell_index'][:,0] # cell_fields/*
        if 'source_index' in self._data:
            self.source_idx = self._data['source_index'][:,0]
        else:
            self.source_idx = None
        self.num_cells = len(self.cell_idx)
        import json
        self._input = {}
        if input_filename is not None:
            with open(input_filename, 'r') as fin:
                self._input = json.load(fin)

    def _getOtherValues(self, field):
        import numpy
        # TODO: sync with Waiwera's internal default
        if field is 'rock_porosity':
            v = numpy.full(self.num_cells, 0.1)
            for rock in self._input['rock']['types']:
                for i in rock['cells']:
                    v[i] = rock['porosity']
            return v
        if field is 'rock_permeability1':
            v = numpy.full(self.num_cells, 1.0e-13)
            for rock in self._input['rock']['types']:
                for i in rock['cells']:
                    v[i] = rock['permeability'][0]
            return v
        if field is 'rock_permeability2':
            v = numpy.full(self.num_cells, 1.0e-13)
            for rock in self._input['rock']['types']:
                for i in rock['cells']:
                    v[i] = rock['permeability'][1]
            return v
        if field is 'rock_permeability3':
            v = numpy.full(self.num_cells, 1.0e-13)
            for rock in self._input['rock']['types']:
                for i in rock['cells']:
                    v[i] = rock['permeability'][2]
            return v
        elif field is 'geom_volume':
            return self._data['cell_fields']['cell_geometry_volume'][:][self.cell_idx]
        else:
            raise Exception

    def _getFieldAtOutputIndex(self, field, outputIndex):
        other_field_names = [
            'rock_porosity',
            'rock_permeability1',
            'rock_permeability2',
            'rock_permeability3',
            'geom_volume']
        if field in other_field_names:
            return self._getOtherValues(field)
        return self._data['cell_fields'][field][outputIndex][self.cell_idx]

    def _getFieldHistoryAtCell(self, field, cellIndex):
        t = self._data['time'][:,0]
        val = self._data['cell_fields'][field][:,self.cell_idx[cellIndex]]
        return t, val

    def _getFieldHistoryAtSource(self, field, sourceIndex):
        if self.source_idx is not None:
            t = self._data['time'][:,0]
            val = self._data['source_fields'][field][:,self.source_idx[sourceIndex]]
            return t, val
        else:
            raise Exception('No sources in model %s' % (self.name))

    def _getPositions(self):
        return self._data['cell_fields']['cell_geometry_centroid'][:][self.cell_idx]

    def _getTimes(self):
        return self._data['time'][:,0]

def t2_to_waiwera(geofilename, datfilename, incfilename =  None, basepath = None):
    """ convert tough2 model into Waiwera, saves input files and return the
    name of main input file

    TODO: maybe this should be external, and formalised more as utility
    TODO: maybe this should return ordering map, to be used in testing, eg. use
    standard geo.num_atmosphere_blocks to generate a normal one?  but this is
    not always true.
    """
    from mulgrids import mulgrid
    from t2incons import t2incon
    from t2data_json import t2data_export_json
    from os import getcwd, chdir
    from os.path import splitext, basename
    import json

    if basepath is None:
        basepath = getcwd()
    startpath = getcwd()
    if basepath != startpath:
        print "Changing to specified base path '%s'" % (basepath)
        os.chdir(basepath)

    geo = mulgrid(geofilename)
    dat = t2data_export_json(datfilename)

    geobase, ext = splitext(basename(geofilename))
    datbase, ext = splitext(basename(datfilename))
    mesh_filename = geobase+'.exo'
    input_filename = datbase + '.json'

    if incfilename:
        inc = t2incon(incfilename)
        incbase, ext = splitext(basename(incfilename))
        initial_filename = incbase  + '_ss.h5'
    else:
        inc = None
        initial_filename = None

    geo.write_exodusii(mesh_filename)
    print '  Mesh file %s created.' % mesh_filename
    jsondata = dat.json(geo, mesh_filename,
                        incons = initial_filename,
                        bdy_incons = inc)
    with open(input_filename, 'w') as jf:
        json.dump(jsondata, jf, indent=2)
        print '  Input file %s created.' % input_filename

    if basepath != startpath:
        print "Restoring initial path '%s'" % (startpath)
        os.chdir(startpath)

    return input_filename

