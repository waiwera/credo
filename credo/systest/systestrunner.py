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

"""Package for manipulation of a suite of system tests.
Analogous to the role of the Pythun unittest TestRunner."""

import os
import sys
import inspect
from xml.etree import ElementTree as etree

import credo.jobrunner
import credo.io.stgxml
from credo.systest.api import *

# Relevant to the XML Results. Designed to be compatible with the tags used
#  by the Python unittest-xml-reporting package
#  (http://pypi.python.org/pypi/unittest-xml-reporting), which are very
#  similar to those used by Java's Ant.
XML_RESULT_TAG_BASENODE = 'CREDO_SuiteResultSummary'
XML_RESULT_TAG_SUITE = 'testsuite'
XML_RESULT_TAG_TESTCASE = 'testcase'

XML_SUITE_ATTR_NAME = 'name'
XML_SUITE_ATTR_PROJECT = 'project'
XML_SUITE_ATTR_TESTS = 'tests'
XML_SUITE_ATTR_FAILURES = 'failures'
XML_SUITE_ATTR_ERRORS = 'errors'

XML_TESTCASE_ATTR_NAME = 'name'
XML_TESTCASE_ATTR_TYPE = 'type'
XML_TESTCASE_ATTR_STATUS = 'status'
XML_TESTCASE_ATTR_RECORDFILE = 'recordfile'

class SysTestRunner:
    """Class that runs a set of :class:`~credo.systest.api.SysTest`, usually
    collected into :class:`~credo.systest.systestsuite.SysTestSuite` collections.

    For examples of how to use, see the CREDO documentation, especially
    :ref:`credo-examples-run-systest-direct`.
    """

    def __init__(self):
        return

    def runSingleTest(self, sysTest, **kwargs):
        """Convenience function to setup and run a single SysTest.
        .. note:: all keywords appopriate to
           :meth:`credo.systest.api.SysTest.runTest()` are passed
           through directly in the kwargs parameter.
        """
        sysTest.setupTest()
        jobRunner = credo.jobrunner.defaultRunner()
        testRes, mResults = sysTest.runTest(jobRunner, **kwargs)
        return testRes

    def runTests(self, sysTests, projName=None, suiteName=None,
            printSummary=True, **kwargs):
        """Run all tests in the sysTests list.
        Will also save all appropriate XMLs and print a summary of results.

        :keyword projName: the name of the 'project' to report these tests as
          belonging to.
        :keyword suiteName: the name of the suite these tests should be
          reported as belonging to.

        .. note:: all keywords appopriate to
           :meth:`credo.systest.api.SysTest.runTest()` are passed
           through directly in the kwargs parameter.
        """
        results = []
        testTotal = len(sysTests)
        for testI, sysTest in enumerate(sysTests):
            sysTest.setupTest()
            jobRunner = credo.jobrunner.defaultRunner()
            print "Running System test %d/%d, with name '%s':" \
                % (testI+1, testTotal, sysTest.testName)
            testRes, mResults = sysTest.runTest(jobRunner, **kwargs)
            results.append(testRes)
        if printSummary:
            self.printResultsSummary(sysTests, results, projName, suiteName)
        return results

    def runSuite(self, suite,
        runSubSuites=True, subSuiteMode=False,
        outputSummaryDir="testLogs", **kwargs):
        """Runs a suite of system tests, and prints results.
        The suite may contain sub-suites, which will also be run by default.

        :returns: a list of all results of the suite, and its sub-suites

        .. note:: Currently, just returns a flat list of results, containing
           results of all tests and all sub-suites. Won't change this into
           a hierarchy of results by sub-suite, unless really necessary.

        .. note:: all keywords appopriate to
           :meth:`credo.systest.api.SysTest.runTest()` are passed
           through directly in the kwargs parameter.
        """

        results = []
        testTotal = len(suite.sysTests)
        subSuitesTotal = len(suite.subSuites)
        subText = "Sub-" if subSuiteMode else ""
        print "Running System Test %sSuite for Project '%s', named '%s',"\
            " containing %d direct tests and %d sub-suites:"\
            % (subText, suite.projectName, suite.suiteName, testTotal,
             subSuitesTotal)

        suiteNode = self._createSuiteNode(suite)
        suiteXMLDoc = etree.ElementTree(suiteNode)
        if testTotal > 0:
            results += self.runTests(suite.sysTests,
                projName=suite.projectName,
                suiteName=suite.suiteName, **kwargs)
        # Even if no results, call func below so we get at least empty totals.
        self._addTestResultsInfo(suiteNode, suite, results)

        if not os.path.exists(outputSummaryDir):
            os.makedirs(outputSummaryDir)
        outFile = self.getSuiteResultsFilename(suite)
        self._writeXMLDocToFile(suiteXMLDoc, outputSummaryDir, outFile)
        self._printXMLFileInfo(os.path.join(outputSummaryDir, outFile))

        if runSubSuites and subSuitesTotal > 0:
            subSuiteResults = []
            for subSuite in suite.subSuites:
                subResults = self.runSuite(subSuite,
                    subSuiteMode=True,
                    outputSummaryDir=outputSummaryDir,
                    **kwargs)
                subSuiteResults.append(subResults)
            for subResults in subSuiteResults:
                results += subResults
            self.printSuiteTotalsShortSummary(results, suite.projectName,
                suite.suiteName)
        return results

    def runSuites(self, testSuites, outputSummaryDir="testLogs", **kwargs):
        """Runs a list of suites, and prints a big summary at the end.

        :param testSuites: list of test suites to run.
        :keyword outputSummaryDir: name of directory to save a summary of
          tests to.

        :returns: a list containing lists of results for each suite (results
          list in the same order as testSuites input argument).

        .. note:: all keywords appopriate to
           :meth:`credo.systest.api.SysTest.runTest()` are passed
           through directly in the kwargs parameter.
        """

        print "Running the following system test suites:"
        for suite in testSuites:
            print " Project '%s', suite '%s'" % (suite.projectName,
                suite.suiteName)
        print "-"*80
        resultsLists = []
        for suite in testSuites:
            suiteResults = self.runSuite(suite,
                outputSummaryDir=outputSummaryDir,
                **kwargs)
            resultsLists.append(suiteResults)
        print "-"*80
        self.printSuiteResultsByProject(testSuites, resultsLists)
        self._printXMLDirInfo(outputSummaryDir)
        print "-"*80
        return resultsLists

    def getSuiteResultsFilename(self, suite):
        """Get a standard name for a suite record file, from given suite
        and its attributes."""
        return "%s-%s.xml" % (suite.projectName, suite.suiteName)

    def _writeXMLDocToFile(self, xmlDoc, outputPath, filename,
            prettyPrint=True):
        """Write the information in xmlDoc (in xml.etree format) to the filename
        given by outputPath and filename."""
        if not os.path.exists(outputPath):
            os.makedirs(outputPath)
        outFilePath = os.path.join(outputPath, filename)
        outFile = open(outFilePath, 'w')
        credo.io.stgxml.writeXMLDoc(xmlDoc, outFile, prettyPrint)
        outFile.close()
        return outFilePath

    def _createSuiteNode(self, suite):
        suiteNode = etree.Element(XML_RESULT_TAG_SUITE)
        suiteNode.attrib[XML_SUITE_ATTR_NAME] = suite.suiteName
        suiteNode.attrib[XML_SUITE_ATTR_PROJECT] = suite.projectName
        #comment = etree.Comment("System tests run by CREDO System.")
        #suiteNode.append( comment )
        return suiteNode

    def _addTestResultsInfo(self, suiteNode, suite, suiteResults):
        sumsDict, failIs, errorIs = self.getResultsTotals(suiteResults)
        totalResults = sum(sumsDict.values())
        suiteNode.attrib[XML_SUITE_ATTR_TESTS] = str(totalResults)
        suiteNode.attrib[XML_SUITE_ATTR_FAILURES] = str(sumsDict['Fail'])
        suiteNode.attrib[XML_SUITE_ATTR_ERRORS] = str(sumsDict['Error'])

        for testI, sysTest in enumerate(suite.sysTests):
            self._addSysTestInfo(suiteNode, sysTest, suiteResults[testI])
        # Currently expect sub-suite results to be written to a separate
        #  file, that'll be called separately.

    def _addSysTestInfo(self, parentNode, sysTest, sysTestResult):
        sysTestNode = etree.SubElement(parentNode, XML_RESULT_TAG_TESTCASE)
        sysTestNode.attrib[XML_TESTCASE_ATTR_NAME] = sysTest.testName
        sysTestNode.attrib[XML_TESTCASE_ATTR_TYPE] = sysTest.testType
        sysTestNode.attrib[XML_TESTCASE_ATTR_STATUS] = sysTestResult.statusStr
        sysTestNode.attrib[XML_TESTCASE_ATTR_RECORDFILE] = sysTestResult.getRecordFile()

    def printSuiteResultsByProject(self, testSuites, resultsLists):
        """Utility function to print a set of suite results out,
        categorised by project, in the order that the projects first
        appear in the results."""
        projOrder, projIndices = self._buildResultsProjectIndex(testSuites)
        suitesResults = zip(testSuites, resultsLists)
        print "CREDO System Tests summary for all project suites ran:"
        print "------"
        totalSumsDict = {"Pass":0, "Fail":0, "Error":0}
        for projName in projOrder:
            print "Project '%s':" % projName
            projSumsDict = {"Pass":0, "Fail":0, "Error":0}
            for suiteI in projIndices[projName]:
                suite = testSuites[suiteI]
                print " Suite '%s':" % suite.suiteName,
                suiteResults = resultsLists[suiteI]
                sumsDict = self.getResultsTotals(suiteResults)[0]
                self._printResultsLineShort(sumsDict)
                for kw, sumVal in sumsDict.iteritems():
                    projSumsDict[kw] += sumVal
            self._printResultsLineShort(projSumsDict)
            print "------"
            for kw, sumVal in projSumsDict.iteritems():
                totalSumsDict[kw] += sumVal
        print "ALL Projects Total: ",
        self._printResultsLineShort(totalSumsDict)
        print "------"

    def printSuiteResultsOrderFound(self, testSuites, resultsLists):
        """Utility function to print a set of results in the order they
        were entered (not sub-categorised by project)."""
        print "-"*80
        print "CREDO System Tests summary for all project suites ran:"
        totalSumsDict = {"Pass":0, "Fail":0, "Error":0}
        for ii, suite in enumerate(testSuites):
            print "'%s', '%s': " % (suite.projectName, suite.suiteName),
            suiteResults = resultsLists[ii]
            sumsDict = self.getResultsTotals(suiteResults)[0]
            totalResults = sum(sumsDict.values())
            self._printResultsLineShort(sumsDict)
            for kw, sumVal in sumsDict.iteritems():
                totalSumsDict[kw] += sumVal
        print "------"
        print "TOTAL: ",
        self._printResultsLineShort(totalSumsDict)
        print "-"*80

    def _buildResultsProjectIndex(self, testSuites):
        """Build index of projects and their indices into testSuites.
       :returns: dictionary where keys are project names, values are lists
       of indices into the testSuites list of results of that project."""
        projectsOrder = []
        projectIndices = {}
        for suiteI, suite in enumerate(testSuites):
            projName = suite.projectName
            if projName not in projectsOrder: projectsOrder.append(projName)

            if projName not in projectIndices:
                projectIndices[projName] = [suiteI]
            else:
                projectIndices[projName].append(suiteI)

        return projectsOrder, projectIndices

    def printSuiteTotalsShortSummary(self, results, projName, suiteName):
        """Prints a short summary, useful for suites with sub-suites."""
        print "-"*80
        print "CREDO System Tests total for '%s' suite '%s' and sub-suites:"\
            % (projName, suiteName)
        sumsDict, failIndices, errorIndices = self.getResultsTotals(results)
        self._printResultsLine(sumsDict)
        print "-"*80

    def printResultsSummary(self, sysTests, results,
            projName=None, suiteName=None):
        """Print a textual summary of the results of running a set of sys
        tests."""
        self._checkResultsSysTestsLength(sysTests, results)
        print "-"*80
        headerDetail = ""
        if projName is not None:
            headerDetail += ", project '%s'" % projName
        if suiteName is not None:
            headerDetail += ", suite '%s'" % suiteName
        print "CREDO System Tests results summary%s:" % headerDetail
        self.printResultsDetails(sysTests, results)
        print "-"*80

    def printResultsDetails(self, sysTests, results):
        """Prints details of which tests failed in a sub-suite."""
        sumsDict, failIndices, errorIndices = self.getResultsTotals(results)
        self._printResultsLine(sumsDict)

        if len(failIndices) > 0:
            print "Failures were:"
            for fI in failIndices:
                print " %s: %s" % (sysTests[fI].testName,
                    results[fI].detailMsg)

        if len(errorIndices) > 0:
            print "Errors were:"
            for eI in errorIndices:
                print " %s: %s" % (sysTests[eI].testName,
                    results[eI].detailMsg)

    def getResultsTotals(self, results):
        """Gets the totals of a set of results, and returns, including
        indices of which results failed, and which were errors."""
        sums = {"Pass":0, "Fail":0, "Error":0}
        failIndices = []
        errorIndices = []
        for resI, result in enumerate(results):
            sums[result.statusStr] += 1
            if isinstance(result, CREDO_FAIL): failIndices.append(resI)
            if isinstance(result, CREDO_ERROR): errorIndices.append(resI)
        return sums, failIndices, errorIndices

    def _printResultsLine(self, sumsDict):
        totalResults = sum(sumsDict.values())
        print "Ran %d system tests," % (totalResults),
        print "with %d passes, %d fails, and %d errors" \
            % (sumsDict["Pass"], sumsDict["Fail"], sumsDict["Error"])

    def _printResultsLineShort(self, sumsDict):
        totalResults = sum(sumsDict.values())
        print "%d tests, %d/%d/%d passes/fails/errors" \
            % (totalResults, sumsDict["Pass"], sumsDict["Fail"],
                sumsDict["Error"])

    def _checkResultsSysTestsLength(self, sysTests, results):
        if len(sysTests) != len(results):
            raise ValueError("The sysTests and results args must be"\
                " same length, but sysTests of len %d vs results of"\
                " len %d" % (len(sysTests), len(results)))

    def _printXMLFileInfo(self, outputSummaryXML):
        print "XML summary file saved to '%s'." % outputSummaryXML

    def _printXMLDirInfo(self, outputSummaryDir):
        print "All XML summary files saved to dir '%s'." % outputSummaryDir


def getSuitesFromModules(suiteModNames):
    """Gets a list of suites from the list of suites to import given in
    suiteModNames."""
    suites = []
    for modName in suiteModNames:
        print "Importing suite for %s:" % modName
        # 2-stage process is needed, see Python docs on imp module
        try:
            imp = __import__(modName)
            mod = sys.modules[modName]
        except:
            print "Warning: failed to import module '%s' - not adding to set"\
                " of suites." % (modName)
            continue
        try:
            suite = mod.suite()
        except AttributeError:
            print "Warning: module %s doesn't define a 'suite()' interface"\
                " function, thus isn't usable as a CREDO suite - skipping."\
                % (modName)
            continue
        suites.append(suite)
    return suites

def runSuitesFromModules(suiteModNames, **kwargs):
    """Runs a set of System test suites, where suiteModNames is a list of
    suites to import and run.

    .. note:: all keywords appopriate to
       :meth:`credo.systest.api.SysTest.runTest()` are passed
       through directly in the kwargs parameter.
    """
    suites = getSuitesFromModules(suiteModNames)
    testRunner = SysTestRunner()
    testRunner.runSuites(suites, **kwargs)
