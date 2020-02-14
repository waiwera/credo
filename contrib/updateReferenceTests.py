#!/usr/bin/env python

"""This is a work-in-progress example to show modification of an existing
set of suites to check if any Reference tests have changed output results
significantly, and report on this.

Example created:- 2011/04/20, PatrickSunter"""
from __future__ import print_function

import os, sys
import credo.jobrunner
import credo.systest.systestrunner as srRunner

# This is a factor increase from the existing defined error tolerance
#  (which is specified in the original test suite)
allowedTolChange = 1.1
suiteModNames = ["SysTest.RegressionTests.testAll_lowres"]
tSuites = srRunner.getSuitesFromModules(suiteModNames)

# TODO: really should post-proc from existing, but this isn't working perfectly
# yet for basic sys tests.
problemTests = []
jobRunner = credo.jobrunner.defaultRunner()
for tSuite in tSuites:
    for sysTest in tSuite.sysTests:
        if sysTest.testType == "Reference":
            sysTest.setupTest()
            testResult, mResults = sysTest.runTest(jobRunner,
                    postProcFromExisting=False, createReports=True)
            for tCompDict in sysTest.testComps:
                for tcName, tComp in tCompDict.items():
                    fErrors = tComp.fieldErrors
                    for fName, error in fErrors.items():
                        fTol = tComp.getTolForField(fName)
                        for eComp in error:
                            if eComp > fTol * allowedTolChange:
                                problemTests.append((sysTest, fName,
                                    fTol, eComp))

if len(problemTests) > 1:
    print("Error, at least one test failed to be within factor %g of original"\
        " tolerance:" % (allowedTolChange))
    for test in problemTests:
        print("Test '%s', field '%s': orig fTol = %g, current error = %g" % \
            (test[0].testName, test[1], test[2], test[3]))
        print("  (Test basepath = %s)" % test[0].basePath)
else:
    print("All tests within factor %g of original tolerance." % allowedTolChange)
    for tSuite in tSuites:
        print("Updating systest reference solutions in suite %s" % \
            tSuite.suiteName)
        for sysTest in tSuite.sysTests:
            if sysTest.testType == "Reference":
                sysTest.regenerateFixture(jobRunner)
