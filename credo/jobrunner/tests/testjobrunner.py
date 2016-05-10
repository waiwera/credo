import unittest
import os, sys

from credo.jobrunner import SimpleJobRunner
from credo.modelrun import ModelRun, JobParams
from credo.modelresult import ModelResult
from credo.t2model import T2ModelRun

TEST_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_run_dir')

class MockModelRun(ModelRun):
    def __init__(self):
        super(MockModelRun, self).__init__('mock_model_run', TEST_PATH)

    def getModelRunCommand(self, extraCmdLineOpts=None, absXMLPaths=False):
        return 'dir'

    def createModelResult(self):
        """ This is a new interface, to be called by JobRunner to generate
        ModelResult.  It returns a ModelResult object that matches the ModelRun
        object.

        Here it just use ModelResult (before refactoring)
        """
        absOutPath = os.path.join(self.basePath, self.outputPath)
        mres = ModelResult(self.name, absOutPath)
        return mres


class TestJobRunner(unittest.TestCase):
    def setUp(self):
        if not os.path.exists(TEST_PATH):
            os.makedirs(TEST_PATH)

    def tearDown(self):
        pass

    def test_jobrunner(self):
        mrun = MockModelRun()
        jrunner = SimpleJobRunner()
        jmi = jrunner.submitRun(mrun)
        mres = jrunner.blockResult(mrun, jmi)

    def test_jobrunner_mpi(self):
        mrun = MockModelRun()
        jrunner = SimpleJobRunner(mpi=True)
        jmi = jrunner.submitRun(mrun)
        mres = jrunner.blockResult(mrun, jmi)

    def test_aut2(self):
        mrun = T2ModelRun('test_aut2',
                          'coarse.dat',
                          basePath=TEST_PATH,
                          outputPath=TEST_PATH)
        jrunner = SimpleJobRunner(mpi=False)
        jmi = jrunner.submitRun(mrun)
        mres = jrunner.blockResult(mrun, jmi)


if __name__ == '__main__':
    unittest.main()

