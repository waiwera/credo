"""Test running benchmark test with dummy model, effectively a
one-cell model with time-dependent response determined by an
analytical function foo(x, t).
"""

import os
import unittest
import numpy as np
from functools import partial

from credo.modelrun import ModelRun
from credo.modelresult import ModelResult
from credo.systest import SciBenchmarkTest
from credo.systest import CREDO_PASS
from credo.systest import FieldWithinTolTC
from credo.systest import HistoryWithinTolTC
from credo.jobrunner import SimpleJobRunner

THIS_DIR = os.path.dirname(os.path.realpath(__file__))

output_positions = np.array([-0.5])
output_times = np.array([0., 2., 7.])
def foo(x, t): return x * np.exp(t)

class FooModelRun(ModelRun):
    """Dummy model run with analytical function."""
    def __init__(self, name,
                 basePath=None, outputPath=None, logPath=None,
                 perturbation = 0):
        super(FooModelRun, self).__init__(name, basePath, outputPath, logPath)
        self.perturbation = perturbation

    def getModelRunCommand(self, extraCmdLineOpts=None):
        return "python --version"

    def createModelResult(self):
        return FooModelResult(self.name, self.outputPath,
                              perturbation = self.perturbation)

class FooModelResult(ModelResult):
    """Dummy model result with analytical function."""
    def __init__(self, name, outputPath, perturbation = 0):
        super(FooModelResult, self).__init__(name, outputPath)
        self.name = name
        self.perturbation = perturbation

    def _getFieldAtOutputIndex(self, field, outputIndex):
        if field == 'foo':
            t = output_times[outputIndex]
            return np.full(1, foo(output_positions[0], t) + self.perturbation)
        else:
            raise Exception('Unknown field %s.' % field)

    def _getFieldHistoryAtCell(self, field, cellIndex):
        if field == 'foo':
            if cellIndex == 0:
                return output_times,\
                    foo(output_positions[0], output_times) + self.perturbation
            else:
                raise Exception('Unknown cell index %d.' % cellIndex)
        else:
            raise Exception('Unknown field %s.' % field)

    def _getPositions(self):
        return output_positions

    def _getTimes(self):
        return output_times

class TestFooModelResult(unittest.TestCase):

    def setUp(self):
        self.result = FooModelResult('test', outputPath = THIS_DIR)

    def tearDown(self):
        pass

    def test_getfield(self):
        for i,t in enumerate(output_times):
            y = self.result.getFieldAtOutputIndex('foo', i)
            self.assertTrue(np.allclose(y, foo(output_positions[0], t)))

    def test_getposition(self):
        x = self.result.getPositions()
        self.assertTrue(np.allclose(x, output_positions))

    def test_gettimes(self):
        t = self.result.getTimes()
        self.assertTrue(np.allclose(t, output_times))

    def test_gethistory(self):
        t, y = self.result.getFieldHistoryAtCell('foo', 0)
        self.assertTrue(np.allclose(t, output_times))
        expected_foo = np.array([foo(output_positions[0], t) for t in output_times])
        self.assertTrue(np.allclose(y, expected_foo))

    def test_test(self):

        model_dir = './run'
        output_dir = './output'
        if not os.path.exists(model_dir): os.mkdir(model_dir)
        base_path = os.path.realpath(model_dir)
        run_index = 0
        test_fields = ['foo']
        tol = 0.01

        for np in [1, 2]:

            run_name = "foo_run"
            mpi = np > 1

            for perturbation in [0.5 * tol, 1.5 * tol]:

                expected_pass = perturbation < tol
                expected_status = 'pass' if expected_pass else 'fail'
                test_name = "foo_test_np_%d_%s" % (np, expected_status)
                test = SciBenchmarkTest(test_name, nproc = np)
                model_run = FooModelRun(run_name, basePath = base_path,
                                        perturbation = perturbation)
                model_run.jobParams['nproc'] = np
                test.mSuite.addRun(model_run, run_name)

                expected_result = FooModelResult("expected", "")

                test.setupEmptyTestCompsList()
                for ti in range(len(output_times)):
                    test.addTestComp(run_index, "field at time index %d" % ti,
                                     FieldWithinTolTC(fieldsToTest = test_fields,
                                                      defFieldTol = 0.01,
                                                      expected = partial(foo, t = output_times[ti]),
                                                      testOutputIndex = ti))

                test.addTestComp(run_index, "model result field at time index %d" % 2,
                                 FieldWithinTolTC(fieldsToTest = test_fields,
                                                  defFieldTol = tol,
                                                  expected = expected_result,
                                                  testOutputIndex = 2))

                cell_index = 0
                test.addTestComp(run_index, "history at cell %d" % cell_index,
                              HistoryWithinTolTC(fieldsToTest = test_fields,
                                                 defFieldTol = tol,
                                                 expected = expected_result,
                                                 testCellIndex = cell_index))

                self.assertEqual(len(test.testComps), 1)
                self.assertEqual(len(test.testComps[0]), len(output_times) + 2)

                jrunner = SimpleJobRunner(mpi = mpi)
                test_result, model_results = test.runTest(jrunner, createReports = True)

                self.assertEqual(isinstance(test.testStatus, CREDO_PASS), expected_pass)

if __name__ == '__main__':
    unittest.main()
