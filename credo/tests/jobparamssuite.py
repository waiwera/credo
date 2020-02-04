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

import unittest

import credo.modelrun
from xml.etree import ElementTree as etree

class JobParamsTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def teatDown(self):
        pass

    def test_create(self):
        jp = credo.modelrun.JobParams(nproc=1)
        self.assertEqual(jp['nproc'], 1)
        self.assertEqual(jp['maxRunTime'], credo.modelrun.DEF_MAX_RUN_TIME)
        self.assertEqual(jp['pollInterval'], credo.modelrun.DEF_POLL_INTERVAL)
        jp['PBS'] = {"queue":"run_1_week", "nameLine":"#PBS -n myJob"}
        self.assertEqual(jp['PBS']['queue'], "run_1_week")

    def test_writeInfoXML(self):
        el = etree.Element('myElement')
        jp = credo.modelrun.JobParams(nproc=1)
        jp['PBS'] = {"queue":"run_1_week", "nameLine":"#PBS -n myJob"}
        jp.writeInfoXML(el)
        self.assertEqual(etree.tostring(el),
            """<myElement><jobParams><maxRunTime>None</maxRunTime><pollInterval>1</pollInterval><PBS><queue>run_1_week</queue><nameLine>#PBS -n myJob</nameLine></PBS><nproc>1</nproc></jobParams></myElement>""")

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(JobParamsTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
