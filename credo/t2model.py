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

# Allow MPI command to be overriden by env var.
AUT2_COMMAND = "AUT2_COMMAND"
DEFAULT_AUT2_COMMAND = "autough2_4"

class T2ModelRun(ModelRun):
    """ for AUT2

    TODO: ?? do I need to include the optional geometry file? which could help
    as it can be passed into ModelResult so that modelresult can return
    positions of elements etc.

    """
    def __init__(self, name, dat_filename, save_filename='', incon_filename='',
                 simulator=DEFAULT_AUT2_COMMAND,
                 basePath=None, outputPath=None, logPath=None,
                 ):
        super(T2ModelRun, self).__init__(name, basePath, outputPath, logPath)

        self._dat_filename = dat_filename
        self._save_filename = save_filename
        self._incon_filename = incon_filename
        self._simulator = simulator

        # initialised in .preRunPreparation()
        self._runCommand = None
        self._lstbase = None

    def preRunPreparation(self):
        from os.path import basename, join
        datbase, savebase, inconbase = self._aut2FileNameBases()
        runfilename = datbase + '_' + basename(self._simulator) + '.in'
        with open(join(self.basePath, runfilename),'w') as f:
            f.write('\n'.join([
                savebase,
                inconbase,
                datbase,]))
        self._runCommand = "%s < %s" % (self._simulator, runfilename)
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
            other_exts = ['.listing', '.pdat', '.autogeners']
            return [datbase+ext for ext in other_exts] + main_files
        def files_to_clean():
            return [n+'.data' for n in ['gener', 'lineq', 'mesh', 'table', 'vers']]
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
        lst_filename = join(self.outputPath, self._lstbase+'.listing')
        mres = T2ModelResult(self.name, lst_filename)
        return mres

class T2ModelResult(ModelResult):
    """ for AUT2
    """
    def __init__(self, name, lst_filename):
        from os.path import dirname
        super(T2ModelResult, self).__init__(name, dirname(lst_filename))
        self.name = name
        self._lst = t2listing(lst_filename)

    def getFieldAtStep(self, field, time_step):
        self._lst.step = time_step
        return self._lst.element[field]

