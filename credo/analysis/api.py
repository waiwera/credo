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

"""This is the core interface for analysis operations in CREDO."""
from builtins import object

# TODO: add some documentation about the archicture of AnalysisOps, and how this
# could be related/integrated with gLucifer.

class AnalysisOperation(object):
    '''Abstract base class for Analysis Operations in CREDO: i.e. that require
    some analysis to be done during a
    :class:`~credo.modelrun.ModelRun`. All instances should provide at least
    this standard interface so that records of analysis can be stored.'''

    def writeInfoXML(self, parentNode):
        '''Virtual method for writing Information XML about an analysis op,
        that will be saved as a record of the analysis applied.'''

        raise NotImplementedError("This is a virtual method and must be"\
            " overwritten")

    def writeStgDataXML(self, rootNode):
        '''Writes the necessary StGermain XML to require the analysis to take
        place. This is likely to include creating and configuring Components,
        and adding them to the Components dictionary. See
        :mod:`credo.io.stgxml` for the interface for setting these up.'''

        raise NotImplementedError("This is a virtual method and must be"\
            " overwritten")

    def postRun(self, modelRun, runPath):
        '''Does any required post-run actions for this analysis op, e.g. moving
        generated files into the correct output directory. Is passed
        a reference to a :class:`~credo.modelrun.ModelRun`, so can use it's
        attributes such as :attr:`~credo.modelrun.ModelRun.outputPath`.'''

        raise NotImplementedError("This is a virtual method and must be"\
            " overwritten")
