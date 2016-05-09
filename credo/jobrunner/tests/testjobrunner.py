import unittest
import os, sys

from credo.jobrunner import SimpleJobRunner
from credo.modelrun import JobParams
from credo.modelresult import ModelResult

TEST_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_run_dir')

class MockModelRun(object):
    def __init__(self):
        self.name = 'mock_model_run'
        self.basePath = TEST_PATH
        self.outputPath = os.path.join("output", self.name)
        self.logPath = self.outputPath
        self.jobParams = JobParams()

    def getModelRunCommand(self, extraCmdLineOpts=None, absXMLPaths=False):
        return 'dir'

    def getStdOutFilename(self):
        """Get the name of the file this Model's stdout needs to/has been
        saved to."""
        return os.path.join(self.logPath, "%s.stdout" % self.name)

    def getStdErrFilename(self):
        """Get the name of the file this Model's stderr needs to/has been
        saved to."""
        return os.path.join(self.logPath, "%s.stderr" % self.name)

    def checkValidRunConfig(self):
        pass

    def preRunPreparation(self):
        pass

    def postRunCleanup(self):
        pass

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


if __name__ == '__main__':
    unittest.main()

