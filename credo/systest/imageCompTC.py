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

import os
from xml.etree import ElementTree as etree

from .api import SingleRunTestComponent, CREDO_PASS, CREDO_FAIL
import credo.analysis.images as imageAnalysis

def floatsToStr(floatList):
    """Convert a list/tuple of tolerance to a nice string to print"""
    return "(%s)" % ", ".join(["%g" % val for val in floatList])

class ImageCompTC(SingleRunTestComponent):
    """Checks whether an image produced by the run (eg by gLucifer)
    is within a given "tolerance" of an expected image, using
    functionality of :mod:`credo.analysis.images` module.

    .. attribute:: imageFilename

       Filename of the image to be tested.

    .. attribute:: tol

       Tolerance tuple that the resultant image compared to the reference
       image must be within. In form required by
       :func:`credo.analysis.images.compare` .
    
    .. attribute:: refPath

       Path to look for reference images.

    .. attribute:: genPath

       Path to look for generated images (if left as `None`, will default to
       ModelRun's specified output path.)

    .. attribute:: imageResults

       List, indexed by run number, of result of comparison test for each run.

    .. attribute:: imageErrors

       List, indexed by run number, containing errors between reference and
       generated images after comparison.
    """
    DEFAULT_TOLS = (0.1, 0.05)
    DEFAULT_REFPATH = os.path.join('.', 'expected')

    def __init__(self, imageFilename,
            tol=None,
            refPath=None,
            genPath=None):
        SingleRunTestComponent.__init__(self, "imagesWithinTol")
        self.imageFilename = imageFilename
        if tol is not None:
            self.tol = tol
        else:
            self.tol = self.DEFAULT_TOLS
        if refPath is not None:
            self.refPath = refPath
        else:
            self.refPath = self.DEFAULT_REFPATH
        if genPath is not None:
            self.genPath = genPath
        else:
            # in this case, we will read from the model's output dir.
            self.genPath = None
        self.imageResults = None
        self.imageErrors = None

    def attachOps(self, modelRun):
        """Implements base class
        :meth:`credo.systest.api.SingleRunTestComponent.attachOps`."""
        # Nothing to do here - requires that the user has defined their
        # model XMLs correctly to generate the images.

    def check(self, mResult):
        """Implements base class
        :meth:`credo.systest.api.SingleRunTestComponent.check`."""
        self.imageResults = []
        self.imageErrors = []
        statusMsg = ""
        overallResult = True
        refImageFname = os.path.join(self.refPath, self.imageFilename)
        if not os.path.exists(refImageFname):
            statusMsg += "Reference image '%s' not found!\n" % refImageFname
            print statusMsg
            self._setStatus(False, statusMsg)
            return False

        if self.genPath is not None:
            genPath = self.genPath
        else:
            genPath = mResult.outputPath
        genImageFname = os.path.join(genPath, self.imageFilename)
        if not os.path.exists(genImageFname):
            statusMsg += "Generated image '%s' not found!\n" % genImageFname
            print statusMsg
            self._setStatus(False, statusMsg)
            return False

        self.imageErrors = imageAnalysis.compare(refImageFname, genImageFname)
        self.imageResults = []
        for diff, tol in zip(self.imageErrors, self.tol):
            self.imageResults.append(diff <= tol)
        overallResult = all(self.imageResults)
        if not overallResult:
            statusMsg += "Image comp for image file '%s' errors %s not"\
                " within tol %s of reference image\n"\
                % (self.imageFilename, floatsToStr(self.imageErrors),
                    floatsToStr(self.tol))
        else:
            statusMsg = "Image comp error within tolerances %s"\
                " of ref image.\n"\
                % (floatsToStr(self.tol))
        print statusMsg
        self._setStatus(overallResult, statusMsg)
        return overallResult

    def _writeXMLCustomSpec(self, specNode):
        etree.SubElement(specNode, 'imageFilename').text = self.imageFilename
        tolsNode = etree.SubElement(specNode, 'tolerances')
        for tolI, tolVal in enumerate(self.tol):
            tolNode = etree.SubElement(tolsNode, 'tol')
            tolNode.attrib['comp'] = str(tolI)
            tolNode.attrib['value'] = str(tolVal)
        etree.SubElement(specNode, 'refPath').text = self.refPath
        if self.genPath is not None:
            etree.SubElement(specNode, 'genPath').text = self.genPath

    def _writeXMLCustomResult(self, resNode, mResult):
        irNode = etree.SubElement(resNode, 'imageResults')
        errorsNode = etree.SubElement(resNode, "imgErrors")
        for compI, compError in enumerate(self.imageErrors):
            eNode = etree.SubElement(errorsNode, "compError")
            eNode.attrib["num"] = str(compI)
            eNode.attrib["error"] = "%6e" % compError
            eNode.attrib["withinTol"] = str(self.imageResults[compI])
