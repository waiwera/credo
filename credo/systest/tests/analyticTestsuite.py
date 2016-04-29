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
import cPickle as pickle
import shutil
import tempfile
import unittest

from credo.systest.analyticTest import AnalyticTest

class AnalyticTestTestCase(unittest.TestCase):

    def setUp(self):
        self.basedir = os.path.realpath(tempfile.mkdtemp())
        #os.makedirs(os.path.join(self.basedir,self.results_dir,'StGermain'))
            #self.results_xml = open(os.path.join(self.basedir,
                #self.results_dir, 'StGermain', 'TEST-FooSuite.xml'), 'w')
        self.sysTest = AnalyticTest("TestModel.xml", "./output/analyticTest")

    def tearDown(self):
        shutil.rmtree(self.basedir)

    def test_checkGenSuite(self):
        # TODO
        mrSuite = self.sysTest.genSuite()
        self.fail("Not written yet")

    def test_checkModelResultsValid(self):
        # TODO
        self.fail("Not written yet")

    def test_getStatus(self):
        # TODO
        self.fail("Not written yet")

    def test_writeXML(self):
        # TODO
        self.fail("Not written yet")

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AnalyticTestTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
