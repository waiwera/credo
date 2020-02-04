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
import tempfile
import unittest
import shutil
import glob

from credo.io import stgpath
from xml.etree import ElementTree as etree

class StgPathTestCase(unittest.TestCase):

    def setUp(self):
        self.basedir = os.path.realpath(tempfile.mkdtemp())
        os.environ['STG_BASEDIR'] = os.path.abspath(
            os.path.join('..', '..', '..', '..'))

    def tearDown(self):
        shutil.rmtree(self.basedir)

    def test_checkAllXMLInputFilesExist(self):
        sampleXMLs = glob.glob(os.path.join("sampleData", "stgXML", "*.xml"))
        try:
            stgpath.checkAllXMLInputFilesExist(sampleXMLs)
        except IOError:
            self.fail("Shouldn't produce IO error")
        self.assertRaises(IOError, stgpath.checkAllXMLInputFilesExist, ["boo"])

    def test_convertLocalXMLFilesToAbsPaths(self):
        sampleXMLsOrig = glob.glob(os.path.join(
            "sampleData", "stgXML", "*.xml"))
        sampleXMLsUp = stgpath.convertLocalXMLFilesToAbsPaths(sampleXMLsOrig,
            "Underworld/SysTests")
        self.assertEqual(sampleXMLsOrig, sampleXMLsUp)

    def test_convertLocalXMLFilesToAbsPaths_ConvertNeeded(self):
        testCallingPath = "Underworld/SysTests"
        sampleXMLsOrig = glob.glob(os.path.join(
            "sampleData", "stgXML", "*.xml"))
        sampleXMLsOrig.append(os.path.join("rel","notExist.xml"))
        sampleXMLsUp = stgpath.convertLocalXMLFilesToAbsPaths(sampleXMLsOrig,
            testCallingPath)
        self.assertEqual(sampleXMLsOrig[:-1], sampleXMLsUp[:-1])
        self.assertEqual(sampleXMLsUp[-1],
            os.path.join(testCallingPath, "rel", "notExist.xml"))

# TODO: more tests required!

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(StgPathTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
