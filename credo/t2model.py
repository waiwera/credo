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

from t2listing import t2listing
from mulgrids import mulgrid
from t2data import t2data

DEFAULT_COMMAND = "autough2_4"

class T2ModelRun(ModelRun):
    """ for AUT2

    TODO: ?? do I need to include the optional geometry file? which could help
    as it can be passed into ModelResult so that modelresult can return
    positions of elements etc.

    """
    def __init__(self, name, dat_filename, save_filename='', incon_filename='',
                 geo_filename=None, ordering_map=None, fieldname_map=None,
                 simulator=DEFAULT_COMMAND,
                 basePath=None, outputPath=None, logPath=None,
                 ):
        super(T2ModelRun, self).__init__(name, basePath, outputPath, logPath)

        self._dat_filename = dat_filename
        self._save_filename = save_filename
        self._incon_filename = incon_filename
        self._geo_filename = geo_filename # optional
        self._simulator = simulator

        self._ordering_map = ordering_map
        self._fieldname_map = fieldname_map

        # initialised in .preRunPreparation()
        self._runCommand = None
        self._lstbase = None

    def preRunPreparation(self):
        from os.path import basename, join
        datbase, savebase, inconbase = self._aut2FileNameBases()

        # check cases of filename for later use
        self._dat_case_upper = datbase[0].isupper()

        runfilename = datbase + '_' + basename(self._simulator) + '.in'
        with open(self.getStdInFilename(), 'w') as f:
            f.write('\n'.join([
                savebase,
                inconbase,
                datbase,]))
        self._runCommand = self._simulator
        self._lstbase = datbase

    def getModelRunCommand(self, extraCmdLineOpts=None):
        """ Note: this is called AFTER .preRunPreparation() """
        # AUT2 does not care these
        return self._runCommand

    def _aut2FileNameBases(self):
        """ Returns the basenames of the three model files (datbase, savebase,
        inconbase)
        """
        from os.path import splitext, basename
        datbase,ext = splitext(self._dat_filename)
        if self._save_filename == '':
            savebase = datbase
        else:
            savebase,ext = splitext(self._save_filename)
        if self._incon_filename == '':
            inconbase = datbase
        else:
            inconbase,ext = splitext(self._incon_filename)
        return (datbase, savebase, inconbase)

    def postRunCleanup(self):
        # AUT2 handles files differently from TOUGH2-MP and TOUGH2
        # TODO: deal with case of .save/.incon etc. on some systems
        def files_to_keep():
            datbase, savebase, inconbase = self._aut2FileNameBases()
            main_files = [
                self._dat_filename,
                self._save_filename,
                self._incon_filename,
                ]
            if self._geo_filename:
                main_files = main_files + [self._geo_filename]
            if self._dat_case_upper:
                other_exts = ['.LISTING', '.PDAT', '.AUTOGENERS']
            else:
                other_exts = ['.listing', '.pdat', '.autogeners']
            return [datbase+ext for ext in other_exts] + main_files
        def files_to_clean():
            if self._dat_case_upper:
                return [n+'.data' for n in ['gener', 'lineq', 'mesh', 'table', 'vers']]
            else:
                return [n+'.DATA' for n in ['GENER', 'LINEQ', 'MESH', 'TABLE', 'VERS']]
        import os
        import shutil
        absOutputPath = os.path.join(self.basePath, self.outputPath)
        if self.basePath != self.outputPath:
            for f in files_to_keep():
                if os.path.isfile(f):
                    shutil.copy2(f, os.path.join(absOutputPath, f))
        for f in files_to_clean():
            if os.path.isfile(f):
                os.remove(f)

    def createModelResult(self):
        """ Note: this is called AFTER .postRunCleanup() """
        from os.path import join
        if self._dat_case_upper:
            lst_ext = '.LISTING'
        else:
            lst_ext = '.listing'
        lst_filename = join(self.outputPath, self._lstbase+lst_ext)
        if self._geo_filename:
            geo_filename = join(self.outputPath, self._geo_filename)
        else:
            geo_filename = self._geo_filename
        dat_filename = join(self.outputPath, self._dat_filename)
        mres = T2ModelResult(self.name, lst_filename,
                             dat_filename,
                             geo_filename,
                             ordering_map=self._ordering_map,
                             fieldname_map=self._fieldname_map)
        return mres

class T2ModelResult(ModelResult):
    """ for AUT2
    """
    def __init__(self, name, lst_filename, dat_filename=None, geo_filename=None,
                 ordering_map=None, fieldname_map=None):
        from os.path import dirname
        super(T2ModelResult, self).__init__(name, dirname(lst_filename),
                                            ordering_map=ordering_map,
                                            fieldname_map=fieldname_map)
        self.name = name
        self._lst = t2listing(lst_filename)
        if geo_filename:
            self._geo = mulgrid(geo_filename)
        if dat_filename:
            self._dat = t2data(dat_filename)

    def _getOtherValues(self, field):
        if field is 'rock_porosity':
            return [b.rocktype.porosity for b in self._dat.grid.blocklist]
        if field is 'rock_permeability1':
            return [b.rocktype.permeability[0] for b in self._dat.grid.blocklist]
        if field is 'rock_permeability2':
            return [b.rocktype.permeability[1] for b in self._dat.grid.blocklist]
        if field is 'rock_permeability3':
            return [b.rocktype.permeability[2] for b in self._dat.grid.blocklist]
        elif field is 'geom_volume':
            return [b.volume for b in self._dat.grid.blocklist]
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
        self._lst.step = self._lst.fullsteps[outputIndex]
        return self._lst.element[field]

    def _getFieldHistoryAtCell(self, field, cellIndex):
        ele = self._lst.element.row_name[cellIndex]
        hist = self._lst.history(('e', ele, field), short=False)
        return hist[1]

    def _getPositions(self):
        return [self._geo.block_centre(self._geo.layer_name(b), self._geo.column_name(b)) for b in self._geo.block_name_list]

    def _getTimes(self):
        return self._lst.fulltimes
