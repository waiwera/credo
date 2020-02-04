#!/usr/bin/env python
import os
import copy
from credo.systest import *
from testAll import testSuite

mgSuite = copy.deepcopy(testSuite)
# Customise to run each test with Multigrid options
mgSuite.suiteName += "-mg"
mgSetup = "MultigridEXPERI.xml"
mgOpts = "options-uzawa-mg.opt"
for sysTest in mgSuite.sysTests:
    sysTest.testName += "-mg"
    sysTest.updateOutputPaths(sysTest.outputPathBase + "-mg")
    sysTest.inputFiles.append(mgSetup)
    sysTest.solverOpts = mgOpts

if __name__ == "__main__":
    testRunner = SysTestRunner()
    testRunner.runSuite(mgSuite)
