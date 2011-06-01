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

"""Core API of the :mod:`credo.systest` module.

This defines the two key classes of the model, :class:`.SysTest` and 
:class:`.TestComponent`, from which actual examples of System tests
or Test components need to inherit.
"""

import os
import copy
import types
from datetime import timedelta
from xml.etree import ElementTree as etree
import credo.modelrun as mrun
import credo.modelresult as mresult
import credo.modelsuite as msuite
import credo.io.stgxml
import credo.io.stgpath as stgpath
import credo.utils
import credo.jobrunner

class SysTestSetupError(Exception):
    """An exception for when a System test fails to set up correctly."""

class SysTestResult:
    """Class to represent an CREDO system test result.

    .. attribute:: detailMsg

       detailed message of what happened during the test.

    .. attribute:: statusStr

       One-word status string summarising test result (eg 'Pass').
    
    .. attribute:: _absRecordFile

       The absolute path of where the system test was saved to.
    """   

    detailMsg = None
    statusStr = None
    _absRecordFile = None

    def __str__(self):
        return self.statusStr
    
    def printDetailMsg(self):
        if self.detailMsg:
            print self.detailMsg

    def setRecordFile(self, recordFile):
        """Save the record file: as an absolute path."""
        self._absRecordFile = os.path.abspath(recordFile)
    
    def getRecordFile(self):
        return self._absRecordFile


class CREDO_PASS(SysTestResult):
    '''Simple class to represent an CREDO pass'''
    statusStr = 'Pass'
    def __init__(self, passMsg):
        assert type(passMsg) == str
        self.detailMsg = passMsg

class CREDO_FAIL(SysTestResult):
    '''Simple class to represent an CREDO failure'''
    statusStr = 'Fail'
    def __init__(self, failMsg):
        assert type(failMsg) == str
        self.detailMsg = failMsg
        
class CREDO_ERROR(SysTestResult):
    '''Simple class to represent an CREDO error'''
    statusStr = 'Error'
    def __init__(self, errorMsg):
        assert type(errorMsg) == str
        self.detailMsg = errorMsg

def getStdTestNameBasic(testTypeStr, inputFiles):
    """Basic part of the test name. Useful for restart runs etc."""
    if type(inputFiles) != list:
        raise TypeError("Function requires the inputFiles argument to be "
            " a list of strings - not a %s." % type(inputFiles))

    testNameBasic, ext = os.path.splitext(os.path.basename(inputFiles[0]))
    testNameBasic += "-%s" % (testTypeStr[0].lower()+testTypeStr[1:])
    return testNameBasic

def getStdTestName(testTypeStr, inputFiles, nproc, paramOverrides,
        solverOpts, nameSuffix):
    """Utility function, to get a standard name for system tests given
    key parameters of the tests. If nameSuffix is given a string, it will
    be used as the suffix after processor number, instead of one based on
    any parameter over-rides used."""
    testName = getStdTestNameBasic(testTypeStr, inputFiles)
    testName += "-np%s" % nproc
    if nameSuffix is not None:
        testName += "-%s" % (nameSuffix)
    elif paramOverrides is not None:
        # Otherwise, if no specific suffix to use set, then create one
        #  based on paramOverrides, to avoid collisions where possible
        #  between custom runs and default ones.
        # TODO: move this stuff into a library for managing Stg Command
        # line dict format.
        paramOs = paramOverrides
        paramOsStr = ""
        paramKeys = paramOverrides.keys()
        paramKeys.sort()
        for paramName in paramKeys:
            paramVal = paramOverrides[paramName]
            paramNameLast = paramName.split('.')[-1]
            paramValCanon = str(paramVal).replace(".","_")
            paramOsStr += "-%s-%s" % (paramNameLast, paramValCanon)
        testName += paramOsStr

    return testName

def getStdOutputPath(testClass, inputFiles, testOpts):
    """Get the standard name for the test's output path. Attempts to
    avoid naming collisions where reasonable."""

    classStr = str(testClass).split('.')[-1]
    # Grab any custom options we need
    nproc = testOpts['nproc']
    nameSuffix = testOpts['nameSuffix'] if 'nameSuffix' in testOpts\
        else None
    paramOverrides = testOpts['paramOverrides']\
        if 'paramOverrides' in testOpts else None
    solverOpts = testOpts['solverOpts'] if 'solverOpts' in testOpts\
        else None

    testName = getStdTestName(classStr, inputFiles, nproc, 
        paramOverrides, solverOpts, nameSuffix)
    outputPath = os.path.join('output', testName)
    return outputPath

class SysTest:
    """A class for managing SysTests in CREDO. This is an abstract base
    class: you must sub-class it to create actual system test types.

    The SysTest is designed to interact with the 
    :class:`~credo.systest.systestrunner.SysTestRunner` class, primarily by
    creating a :class:`~credo.modelsuite.ModelSuite` on demand to run a set
    of ModelRuns required to do the test. It will then do a check that
    the results pass an expected metric:- generally by applying one or more
    :class:`~credo.systest.api.TestComponent` classes.
    
    .. attribute:: testType

       records the "type" of the system test, as a string (e.g. "Analytic",
       or "SciBenchmark") - for printing purposes.
    
    .. attribute:: testName

       The name of this test, generally auto-generated from other properties.
       
    .. attribute:: basePath

       The base path of the System test, that runs will be done relative to.

    .. attribute:: outputPathBase

       The "base" output path to store results of the test in. Results from
       individual Model Runs performed as part of running the test may also
       be stored in that directory, or in subdirectories of it.
    
    .. attribute:: mSuite

       The suite of Models that will be run as part of the test. Initially
       None, must be filled in as part of calling :attr:`.genSuite`.

    .. attribute:: nproc

       Number of processors to be used for the test. See 
       :attr:`credo.modelrun.ModelRun.nproc`.

    .. attribute:: timeout

       if set to a positive integer, this will be used as a maximum time
       (in seconds) the test is allowed to run for - if it runs over this
       the result of the test will be set to an Error.
       If timeout is None, 0 or negative, no timeout will be applied.

    .. attribute:: testStatus

       Status of the test. Initially `None`, once the test has been run
       the :class:`.SysTestResult` generated will be saved here.

    .. attribute:: testComps

       A list of dictionaries of :class:`.TestComponent` (Single run) classes
       used as part of
       performing this system test. The primary list is indexed by run number of
       the model run in the systest's :attr:`.mSuite`.

    .. attribute:: multiRunTestComps

       A dictionaries of :class:`.MultiRunTestComponent` classes used as
       part of performing this system test.
    
    .. attribute:: generatedReports

       A list of the file-names of all generated reports created based on
       this benchmark.
    """
    def __init__(self, testType, testName, basePath, outputPathBase, 
            nproc=1, timeout=None):
        self.testType = testType
        self.testName = testName
        self.basePath = basePath
        self.basePath = os.path.abspath(self.basePath) 
        self.outputPathBase = outputPathBase
        self.nproc = nproc 
        self.timeout = timeout
        ##  The modelSuite used for system testing.
        self.mSuite = None
        ## - attributes created in process of testing.
        self.testComps = []
        self.tcResults = []
        self.allsrPassed = None
        self.multiRunTestComps = {}
        self.mrtcResults = {}
        self.allmrPassed = None
        self.testStatus = None
        self.customReporting = None
        self.generatedReports = []

    def regenerateFixture(self, jobRunner):
        '''Function to do any setup of tests for the first time they're run,
        or e.g. when updating to a new Underworld version.
        Since not all tests need this functionality, the default behaviour
        is to do nothing.'''
        pass

    def setupTest(self):
        self.configureSuite()
        self.configureTestComps()
    
    def runTest(self, jobRunner, postProcFromExisting=False,
            createReports=True):
        """Run this sysTest, and return the 
        :class:`~credo.systest.api.SysTestResult` it produces.
        Will also write an XML record of the System test, and each ModelRun
        and ModelResult in the suite that made up the test.

        :keyword postProcFromExisting: if True, will not actually run the test,
            but will read the result from existing modelResults.
        :keyword createReports: if True, will create external reports
            (additional to the XML record) this test specifies.
        :returns: SysTestResult, and list of ModelResults
           (since latter may be useful for further post-processing)"""

        print "Running '%s' system test (%s):" % (self.testName, self.testType)
        startDir = os.getcwd()
        os.chdir(self.basePath)
        print "Attaching test component analysis ops to suite ModelRuns"
        self.attachAllTestCompOps()
        print "Writing pre-test info to XML"
        self.writePreRunXML()
        if postProcFromExisting == False:
            if len(self.mSuite.runs) < 1:
                raise AttributeError("Error: test's ModelSuite has zero runs"\
                    " when about to run - please resolve.")
            # This is to avoid deleting the entire directory that we just
            #  wrote a pre-run XML into.
            for mRun in self.mSuite.runs:
                assert mRun.outputPath != self.outputPathBase
            self.mSuite.preRunCleanup()
            try:
                suiteResults = jobRunner.runSuite(self.mSuite, 
                    maxRunTime=self.timeout, writeRecords=True)
            except Exception, mre:
                suiteResults = None
                sysTestResult = self.setErrorStatus(str(mre))
            else:
                print "Processing sys test result:"
                sysTestResult = self.getStatus(suiteResults)
        else:
            print "(Reading existing results from %s)" % \
                (os.path.join(self.basePath, self.outputPathBase))
            try:
                suiteResults = self.mSuite.readResultsFromPath(self.basePath,
                    overrideOutputPath=self.outputPathBase)
            except msuite.ModelResultNotExistError, e:
                raise ValueError("%s (Do you need to generate"\
                    " results first by running this method with" \
                    " postProcFromExisting=False?)" \
                      % (e))
            print "Processing sys test result:"
            sysTestResult = self.getStatus(suiteResults)
        
        # TODO: Do we need to allow any custom post-proc here?
        # Including custom getStatus?
        print "%s '%s' result: **%s**" % \
            (self.testType, self.testName, sysTestResult)
        if isinstance(sysTestResult, CREDO_ERROR):
            print "Error msg: %s" % (sysTestResult.detailMsg)
        outFilePath = self.updateXMLWithResult(suiteResults)
        print "Saved test result to %s" % (outFilePath)
        # Don't assume reporting functions know how to handle error runs.
        if createReports and not isinstance(sysTestResult, CREDO_ERROR):
            self.createReports(suiteResults)
        sysTestResult.setRecordFile(outFilePath)
        os.chdir(startDir)
        return sysTestResult, suiteResults

    def configureSuite(self):
        """Function for configuring the :class:`credo.modelsuite.ModelSuite`
        to be used for testing on. Must be saved to :attr:`.mSuite` by the
        end of this function. By Default, calls method :meth:`.genSuite`
        which the user should override."""
        self.mSuite = msuite.ModelSuite(outputPathBase=self.outputPathBase)
        self.genSuite()

    def genSuite(self):
        """Must update the :attr:`.mSuite` attribute so it
        contains all models that need to be run to perform the test."""
        raise NotImplementedError("Error, base class abstract method.")

    def setupEmptyTestCompsList(self):    
        assert len(self.mSuite.runs) > 0
        # Zero test components here, now we know number of runs
        self.testComps = [{} for mRun in self.mSuite.runs]
        self.multiRunTestComps = {}

    def configureTestComps(self):
        raise NotImplementedError("Error, abstract base method - "\
            "please implement.")
        
    def attachAllTestCompOps(self):
        """Useful in :meth:`.configureTestComps`.
        but default is to call 'attachOps' method of all testComps
        (requires all testComps to have been already set up and declared in
        :meth:`.configureTestComps`)"""
        assert (len(self.testComps) > 0) or (len(self.multiRunTestComps) > 0)
        assert len(self.mSuite.runs) > 0
        assert len(self.mSuite.runs) == len(self.testComps)
        for runI, testCompsForRun in enumerate(self.testComps):
            for tcName, testComp in testCompsForRun.iteritems():
                testComp.attachOps(self.mSuite.runs[runI])
        for tcName, mrTestComp in self.multiRunTestComps.iteritems():
            mrTestComp.attachOps(self.mSuite.runs)

    def checkModelResultsValid(self, resultsSet):
        """Check that the given result set is "valid", i.e. exists, has 
        the right number of model results, and model results have necessary
        analysis ops associated with them to allow aspects of test to
        evaluate properly."""
        pass

    def getStatus(self, resultsSet):
        """After a suite of runs created by :meth:".genSuite"
        has been run, when this method is passed the results of the suite
        (as a list of :class:`credo.modelresult.ModelResult`), it must decide
        and return the status of the test (as a :class:`.SysTestResult`).

        It also needs to save this status to :attr:`.testStatus`.

        By default, this simply gets each :class:`~.TestComponent` registered
        for the system test do check its status, all must pass for a total
        pass.

        .. note:: if using this default method, then sub-classes need to
           have defined `failMsg` and `passMsg` attributes to use.
        """
        # If using this defaul
        if not (hasattr(self, 'passMsg') and hasattr(self, 'failMsg')):
            raise AttributeError("Please define 'passMsg' and 'failMsg'"\
                " attributes of your SysTest class to use the defualt"\
                " getStatus method.")
        if len(resultsSet) != len(self.testComps):
            raise ValueError("Model results passed in to getStatus must"\
                " be same length array as number of testComponents specified"\
                " (lens are %d and %d, respectively)" %\
                (len(resultsSet), len(self.testComps)))
        self.checkModelResultsValid(resultsSet)
        runPassed = [None for res in resultsSet]
        self.tcResults = [{} for res in resultsSet]
        #TODO: cleanup in future when iterator/generator interface improved
        if self.mSuite.iterGen is not None:
            inIter = msuite.getVariantIndicesIter(self.mSuite.modelVariants,
                self.mSuite.iterGen)
            varDicts = msuite.getVariantNameDicts(self.mSuite.modelVariants,
                inIter)
        for runI, modelResult in enumerate(resultsSet):
            if len(self.testComps[runI]) > 0:
                print "Testing single-run T.C.s for model result %d" % (runI)
                if self.mSuite.iterGen is not None:
                    print "(var-generated, with variants applied of:\n%s)"\
                        % varDicts[runI]
            for tcName, tComp in self.testComps[runI].iteritems():
                tcResult = tComp.check(modelResult)
                self.tcResults[runI][tcName] = tcResult
            runPassed[runI] = all(self.tcResults[runI].itervalues())
            if len(self.testComps[runI]) > 0:
                if runPassed[runI]:
                    print "All single run test components for"\
                        " run %d passed." % runI
                else:
                    #Do not break - we want to do all checks for sys tests
                    print "at least one single run test component for"\
                       " run %d failed." % runI
        self.allsrPassed = all(runPassed)
        #Now do the Multi-run test components
        if len(self.multiRunTestComps) > 0:
            print "Testing multi-run test components:"
        self.mrtcResults = {}
        for tcName, mrtComp in self.multiRunTestComps.iteritems():
            tcResult = mrtComp.check(resultsSet)
            self.mrtcResults[tcName] = tcResult
        self.allmrPassed = all(self.mrtcResults.itervalues())
        if len(self.multiRunTestComps) > 0:
            if self.allmrPassed:
                print "All multi-run test components passed."
            else:
                print "at least one multi-run test component failed."
        if self.allsrPassed and self.allmrPassed:
            self.testStatus = CREDO_PASS(self.passMsg)
        else:
            self.testStatus = CREDO_FAIL(self.failMsg)
        return self.testStatus
    
    def getTCRes(self, tcName, allowMissing=True): 
        """Utility function for single run test components to get lists of 
        test components, and tc results, for each run of a given testComp
        (This can be done by list manipulation in Python, this function
        just makes it easier).
        
        :keyword allowMissing: if True, runs that don't have a TC of givne
          name applied to them will have `None` placed in output array.
          if False, KeyError exception will be propagated.

        :returns: a tuple of 2 lists: all test components of a given name
          ordered by model run in the test, and a list of corresponding
          test component results.
        """
        nRuns = len(self.testComps)
        tcByRun = [None] * nRuns
        tcRes = [None] * nRuns
        for runI in range(nRuns):
            try:
                tcByRun[runI] = self.testComps[runI][tcName]
                tcRes[runI] = self.tcResults[runI][tcName]
            except KeyError, e:
                if allowMissing:
                    tcByRun[runI] = None
                    tcRes[runI] = None
                else:
                    raise e
        return tcByRun, tcRes

    def setErrorStatus(self, errorMsg):
        """Utility function for if a model run fails as part of the test,
        this function can be called to automatically set the test status."""
        testStatus = CREDO_ERROR(errorMsg)
        self.testStatus = testStatus
        return testStatus

    def setTimeout(self, seconds=0, minutes=0, hours=0, days=0):
        """Sets the :attr:`~.timeout` parameter, used to determine how long
        the test is allowed to run for."""
        assert seconds >= 0 and minutes >=0 and days >= 0
        self.timeout = seconds + minutes*60 + hours*60*60 + days*60*60*24

    def defaultSysTestFilename(self):
        """Return the default system test XML record filename, based on
        properties of the systest (such as :attr:`.testName`)."""
        return 'SysTest-'+self.testName+'.xml'

    def writeRecordXML(self, mResults, outputPath="", filename="",
            prettyPrint=True):
        """Convenience function to call all other XML writing funcs
        (pre-run and post-run) in one go."""
        self.writePreRunXML(outputPath, filename, prettyPrint)
        self.updateXMLWithResult(mResults, outputPath, filename, prettyPrint)

    def writePreRunXML(self, outputPath="", filename="", prettyPrint=True):
        """Write the SysTest XML with as much information before the run as
        is possible. This includes general info about the test, and detailed
        specificiation of appropriate parameters and test components.
        
        :param outputPath: (opt) path the XML should be saved to.
        :param filename: (opt) filename within that path that should be used.
        :param prettyPrint: whether to indent the XML for better
          human-readability (pretty-printing).
        :returns: the name of the file written to.
        """
        baseNode = self._createXMLBaseNode()
        self._writeXMLDescription(baseNode)
        self._writeXMLSpecification(baseNode)
        self._writeXMLTestComponentPreRuns(baseNode)
        xmlDoc = etree.ElementTree(baseNode)
        outFileName = self._writeXMLDocToFile(xmlDoc, outputPath, filename)
        return outFileName
        
    def updateXMLWithResult(self, resultsSet, outputPath="", filename="",
            prettyPrint=True):
        """Given resultsSet, a set of model results (list of 
        :class:`~credo.modelresult.ModelResult`), updates a Sys Test XML with
        the results of the test.
        If the XML file has the standard name, as defined by
        :meth:`.defaultSysTestFilename`, then it should be found automatically.

        Other arguments and return value same as for 
        :meth:`.writePreRunXML`."""
        baseNode, xmlDoc = self._getXMLBaseNodeFromFile(outputPath, filename)
        baseNode.attrib['status'] = str(self.testStatus)
        self._writeXMLResult(baseNode)
        if resultsSet is not None:
            # We only do the below if there are actual results to write - for
            # an error run there may not be.
            self._updateXMLTestComponentResults(baseNode, resultsSet)
        outFileName = self._writeXMLDocToFile(xmlDoc, outputPath, filename)
        return outFileName

    def updateXMLWithReports(self, outputPath="", filename="",
            prettyPrint=True):
        """Updates a Sys Test XML with record of any report files generated
        as a result of the test.
        If the XML file has the standard name, as defined by
        :meth:`.defaultSysTestFilename`, then it should be found automatically.

        Other arguments and return value same as for 
        :meth:`.writePreRunXML`."""
        baseNode, xmlDoc = self._getXMLBaseNodeFromFile(outputPath, filename)
        repsNode = etree.SubElement(baseNode, 'generatedReports')
        for grFilename in self.generatedReports:
            repNode = etree.SubElement(repsNode, 'report')
            repNode.attrib['filename'] = grFilename
        outFileName = self._writeXMLDocToFile(xmlDoc, outputPath, filename)
        return outFileName

    def _createXMLBaseNode(self):
        """Create the base XML node for a Sys Test XML, in xml.etree format,
        and return it."""
        baseNode = etree.Element('StgSysTest')
        baseNode.attrib['type'] = self.testType
        baseNode.attrib['name'] = self.testName
        return baseNode

    def _resolveXMLOutputPathFilename(self, outputPath="", filename=""):   
        if filename == "":
            filename = self.defaultSysTestFilename()
        if outputPath == "":
            outputPath = os.path.join(self.basePath, self.outputPathBase)
        outputPath+=os.sep
        return outputPath, filename

    def _writeXMLDocToFile(self, xmlDoc, outputPath, filename, prettyPrint=True):
        """Write the information in xmlDoc (in xml.etree format) to the filename
        given by outputPath and filename."""
        outputPath, filename = self._resolveXMLOutputPathFilename(
            outputPath, filename)
        if not os.path.exists(outputPath):
            os.makedirs(outputPath)
        outFilePath = os.path.join(outputPath, filename)
        outFile = open(outFilePath, 'w')
        credo.io.stgxml.writeXMLDoc(xmlDoc, outFile, prettyPrint)
        outFile.close()
        return outFilePath

    def _getXMLBaseNodeFromFile(self, outputPath="", filename=""):
        """Open the XML file in outputPath and given by filename (if these
        are empty strings, defaults are used), and return the base node
        from this file (in xml.etree format)."""
        outputPath, filename = self._resolveXMLOutputPathFilename(
            outputPath, filename)
        outFile = open(os.path.join(outputPath, filename), 'r+')
        parser = etree.XMLParser()
        # Note: we haven't removed blank spaces from the output
        # (xml.etree doesn't have an automatic option for this),
        # but that shouldn't pose a problem as no whitespace should
        # interfere with meaningful element text.
        xmlDoc = etree.parse(outFile, parser)
        baseNode = xmlDoc.getroot()
        return baseNode, xmlDoc

    def _writeXMLDescription(self, baseNode):
        """Writes the description of a test into an XML sub-node."""
        descNode = etree.SubElement(baseNode, 'description')
        descNode.text = self.description

    def _writeXMLSpecification(self, baseNode):
        """Function to write the test specification to baseNode (xml.etree).
        
        .. note: any "infrastructure" sub-classes should over-ride this method
           appropriately. For user-level sub-classes, use the 
           _writeXMLCustomSpec function.
        """
        specNode = self._createXMLSpecNode(baseNode)
        self._writeXMLSysTestBasicSpecification(specNode)
        try:
            self._writeXMLCustomSpec(specNode)
        except AttributeError, ae:
            raise NotImplementedError("Please implement a "\
                " _writeXMLCustomSpec()"\
                " method for your SysTest subclass: %s" % ae )
            raise ae
    
    def _createXMLSpecNode(self, baseNode):
        """Utility function to create a specification XML node with
         standard name."""
        return etree.SubElement(baseNode, 'testSpecification')

    def _writeXMLSysTestBasicSpecification(self, specNode):
        """Function to write the test specification to baseNode (xml.etree)."""
        etree.SubElement(specNode, 'basePath').text = self.basePath
        etree.SubElement(specNode, 'outputPathBase').text = self.outputPathBase
        nProcNode = etree.SubElement(specNode, "nproc")
        nProcNode.text = str(self.nproc)
        if self.timeout is not None:
            timeOutStr = str(timedelta(seconds=self.timeout))
        else:
            timeOutStr = "None"
        etree.SubElement(specNode, "timeout").text = timeOutStr
    
    def _writeXMLCustomSpec(self, specNode):
        """Function to write the custom specification for a particular test
        type. Virtual method, to be implemented by sub-classes."""
        raise NotImplementedError("Abstract base class.")

    def _writeXMLTestComponentPreRuns(self, baseNode):
        """Write necessary info for all test components used by this 
        system test before a run (eg their specification info."""
        tcBaseNode = etree.SubElement(baseNode, 'testComponents')
        runsNode = etree.SubElement(tcBaseNode, 'singleRunTestComponents')
        for runI, tcForRun in enumerate(self.testComps):
            runNode = etree.SubElement(runsNode, 'run')
            runNode.attrib['num'] = "%d" % runI
            for tcName, testComp in tcForRun.iteritems():
                testComp.writePreRunXML(runNode, tcName)
        mrtcsNode = etree.SubElement(tcBaseNode, 'multiRunTestComponents')
        for tcName, mrtComp in self.multiRunTestComps.iteritems():
            mrtComp.writePreRunXML(mrtcsNode, tcName)

    def _updateXMLTestComponentResults(self, baseNode, resultsSet):
        """Update the XML info about each test component after a run
        (ie result info.)"""
        tcListNode = baseNode.find('testComponents')
        #First MultiRunTestComponents
        runsNode = tcListNode.find('singleRunTestComponents')
        runsNode.attrib['allPassed'] = str(self.allsrPassed)
        runsNodes = runsNode.getchildren()
        for runI, tcForRun in enumerate(self.testComps):
            runNode = runsNodes[runI]
            assert int(runNode.attrib['num']) == runI
            if len(self.tcResults[runI]) > 0:
                runResult = str(all(self.tcResults[runI].itervalues()))
            else:
                runResult = "NA"
            runNode.attrib['runPassed'] = runResult
            tCompsAndXMLs = zip(tcForRun.iterkeys(),
                tcForRun.itervalues(),
                runNode.getchildren())
            for tcName, testComp, testCompXMLNode in tCompsAndXMLs:
                assert tcName == testCompXMLNode.attrib['name']
                assert testComp.tcType == testCompXMLNode.attrib['type']
                testComp.updateXMLWithResult(testCompXMLNode, resultsSet[runI])
        #Now MultiRunTestComponents
        mrtcsNode = tcListNode.find('multiRunTestComponents')
        mrtcsNode.attrib['allPassed'] = str(self.allmrPassed)
        for mrtCompXMLNode in list(mrtcsNode):
            tcName = mrtCompXMLNode.attrib['name']
            mrtComp = self.multiRunTestComps[tcName]
            assert mrtComp.tcType == mrtCompXMLNode.attrib['type']
            mrtComp.updateXMLWithResult(mrtCompXMLNode, resultsSet)

    def _writeXMLResult(self, baseNode):
        """Write the status of a test to the XML doc."""
        resNode = etree.SubElement(baseNode, 'testResult')
        resNode.attrib['status'] = str(self.testStatus)
        statusMsgNode = etree.SubElement(resNode, 'statusMsg')
        statusMsgNode.text = self.testStatus.detailMsg
    
    def createReports(self, mResults):
        """Create any custom reports, then update record XML"""
        if self.customReporting is not None:
            try:
                # Remember customReports is an attribute function, not a 
                # bound method currently - see comment in setCustomReporting()
                self.customReporting(self, mResults)
            except Exception, e:
                print "Failed to create report for SysTest %s, exception msg"\
                    " was: %s" % (self.testName, e)

        self.updateXMLWithReports()

    def setCustomReporting(self, customReportingFunc):
        """Method to use to set the value of the customReporting method."""
        self.customReporting = customReportingFunc
        # Didn't use the below approach to create an actual method, since
        #  it threw out deepcopy for 2.5/2.6
        #self.customReporting = types.MethodType(customReportingFunc,
        #    self, self.__class__)


class SingleModelSysTest(SysTest):
    """
    A subclass of :class:`.SysTest` for common system test types that are
    based on variations on a single Model (defined by a group of XML model
    files, see :attr:`.inputFiles`. Includes utility functions for easily
    creating new model runs based on these standard parameters.

    Constructor keywords not in member attribute list:
    
    * nameSuffix: if specified, this defines the suffix that
      will be added to the test's name, output path, 
      and log path (where the test's result and stderr/out will be saved
      respectively) - Overriding the default one based on params used.

    .. attribute:: inputFiles

       StGermain XML files that define the Model to be tested.

    .. attribute:: paramOverrides

       Any model parameter overrides to be passed to ModelRuns performed
       as part of running the test - see
       :attr:`credo.modelrun.ModelRun.paramOverrides`. Thus allow 
       customisation of the test properties.

    .. attribute:: solverOpts

       Solver options to be used for any models making up this test.
       See :attr:`credo.modelrun.ModelRun.solverOpts`
    """
    def __init__(self, testType, inputFiles, outputPathBase,
            basePath=None, nproc=1, timeout=None,
            paramOverrides=None, solverOpts=None, nameSuffix=None):
        if isinstance(inputFiles, str):
            inputFiles = [inputFiles]
        testName = getStdTestName(testType+"Test", inputFiles,
            nproc, paramOverrides, solverOpts, nameSuffix)
        if basePath is None:
            # Since this is a virtual class, get calling path 2 levels up
            basePath = credo.utils.getCallingPath(2)
        SysTest.__init__(self, testType, testName, basePath, outputPathBase,
            nproc, timeout)
        self.inputFiles = inputFiles
        self.paramOverrides = paramOverrides
        if self.paramOverrides == None:
            self.paramOverrides = {}
        absInputFiles = stgpath.convertLocalXMLFilesToAbsPaths(self.inputFiles,
            self.basePath)
        stgpath.checkAllXMLInputFilesExist(absInputFiles)
        self.solverOpts = solverOpts

    def updateOutputPaths(self, newOutputPathBase):
        """Function useful for when modifying suites, and you wish to 
        change the output Path the suite reports are saved in. Necessary
        because suites with multiple runs will use different sub-dirs 
        for each run.
        
        .. note:: in current design, _don't_ also update expected/reference
           soln paths, just output-related paths."""
        if self.mSuite is not None:
            raise AttributeError("Can't call setSubPaths() after the suite"\
                " has already been generated.")
        self.outputPathBase = newOutputPathBase

    def _createDefaultModelRun(self, modelName, outputPath=None):
        """Create and return a :class:`credo.modelrun.ModelRun` with the
        default options as specified for this System Test.
        (Thus is a useful helper function for sub-classes, so they can
        use this and not keep up to date with changes in
        the ModelRun interface.)"""
        return mrun.ModelRun(modelName,
            self.inputFiles, outputPath, basePath=self.basePath,
            nproc=self.nproc, paramOverrides=copy.copy(self.paramOverrides),
            solverOpts=copy.copy(self.solverOpts))
    
    def _writeXMLSpecification(self, baseNode):
        specNode = self._createXMLSpecNode(baseNode)
        self._writeXMLSysTestBasicSpecification(specNode)
        # Now write stuff appropriate to SingleModelSysTest
        ipListNode = etree.SubElement(specNode, 'inputFiles')
        for xmlFilename in self.inputFiles:
            fileNode = etree.SubElement(ipListNode, 'inputFile')
            fileNode.text = xmlFilename
        mrun.writeParamOverridesInfoXML(self.paramOverrides, specNode)
        mrun.writeSolverOptsInfoXML(self.solverOpts, specNode)
        try:
            self._writeXMLCustomSpec(specNode)
        except AttributeError, ae:
            raise NotImplementedError("Please implement a "\
                " _writeXMLCustomSpec()"\
                " method for your SysTest subclass: %s" % ae )
            raise ae        

class TestComponent:
    '''A class for TestComponents that make up an CREDO System test/benchmark.
    Generally they will form part a list contained by a 
    :class:`.SysTest`.

    This is an abstract base class, individual test components must subclass
    from this interface.
    
    .. attribute:: tcStatus
    
       Status of this test component. Initially None, will be updated after
       the test component is evaluated to a :class:`.SysTestResult`.
       
    .. attribute:: tcType
    
       Type of the test component, as a (single world descriptive) string.'''

    def __init__(self, tcType):
        self.tcStatus = None
        self.tcType = tcType

    def _setStatus(self, result, statusMsg):
        """Utility function for setting the :attr:`.tcStatus` correctly.
        Useful to use at the end of the check() function by child classes."""
        if result == False:
            self.tcStatus = CREDO_FAIL(statusMsg)
        else:
            self.tcStatus = CREDO_PASS(statusMsg)
    
    def writePreRunXML(self, parentNode, name):
        '''Function to write out info about the test component to an XML file,
        as a sub-tree of parentNode.'''
        tcNode = self._createBaseXMLNode(parentNode, name)
        self._writeXMLSpecification(tcNode)
    
    def _createBaseXMLNode(self, parentNode, name):
        '''Utility function when writing out info, should be called by 
        sub-classes at start of writeInfoXML definitions to follow
        convention of naming of XML node.'''
        tcNode = etree.SubElement(parentNode, 'testComponent')
        tcNode.attrib['name'] = name
        tcNode.attrib['type'] = self.tcType
        return tcNode
    
    def _writeXMLSpecification(self, tcNode):
        specNode = etree.SubElement(tcNode, 'specification')
        #Not currently any specification for all testComponents ... though may
        # be a fromXML param in future for example.
        self._writeXMLCustomSpec(specNode)
    
    def _writeXMLCustomSpec(self, specNode):
        raise NotImplementedError("Abstract base class.")

    def updateXMLWithResult(self, tcNode, resultInfo):
        """Updates a given XML node with the result of the test component.
        the 'resultInfo' will be passed through to sub-functions, and varies
        according to the type of test being performed."""
        tcNode.attrib['status'] = str(self.tcStatus)
        self._writeXMLResult(tcNode, resultInfo)


class SingleRunTestComponent(TestComponent):
    def __init__(self, tcType):
        TestComponent.__init__(self, tcType)

    def attachOps(self, modelRun):
        '''Provided a modelRun (:class:`credo.modelrun.ModelRun`)
        attaches any necessary analysis operations
        to that run in order to produce the results needed for the test.
        (see :attr:`credo.modelrun.ModelRun.analysis`).'''
        raise NotImplementedError("Abstract sub-class.")

    def check(self, mResult):
        '''A function to check a set of results - returns True if the Test
        passes, False if not. Also updates the :attr:`.tcStatus` attribute.'''
        raise NotImplementedError("Abstract sub-class.")

    def _writeXMLResult(self, tcNode, mResult):
        assert isinstance(mResult, mresult.ModelResult)
        resNode = etree.SubElement(tcNode, 'result')
        resNode.attrib['status'] = str(self.tcStatus)
        statusMsgNode = etree.SubElement(resNode, 'statusMsg')
        statusMsgNode.text = self.tcStatus.detailMsg
        self._writeXMLCustomResult(resNode, mResult)
    
    def _writeXMLCustomResult(self, resNode, mResult):
        raise NotImplementedError("Abstract method.")


class MultiRunTestComponent(TestComponent):
    """A type of component designed to operate and report on multiple 
    modelRuns (e.g., analysing they converge or overall meet some
    requirement.
    
    Unlike the SingleRunTestComponent, this class's :meth:`attachOps` and
    :meth:`check` methods operate on a list of modelRuns and modelResults,
    not just a single one."""

    def __init__(self, tcType):
        TestComponent.__init__(self, tcType)
        
    def attachOps(self, modelRuns):
        '''Provided a list of modelRuns (:class:`credo.modelrun.ModelRun`)
        attaches any necessary analysis operations
        to each run needed for the test.
        (see :attr:`credo.modelrun.ModelRun.analysis`).'''
        raise NotImplementedError("Abstract sub-class.")

    def check(self, mResults):
        '''A function to check a set of results - returns True if the Test
        passes, False if not. Also updates the :attr:`.tcStatus` attribute.'''
        raise NotImplementedError("Abstract sub-class.")

    def _writeXMLResult(self, tcNode, mResults):
        assert isinstance(mResults, list)
        for mResult in mResults:
            assert isinstance(mResult, mresult.ModelResult)
        resNode = etree.SubElement(tcNode, 'result')
        resNode.attrib['status'] = str(self.tcStatus)
        statusMsgNode = etree.SubElement(resNode, 'statusMsg')
        statusMsgNode.text = self.tcStatus.detailMsg
        self._writeXMLCustomResult(resNode, mResults)
    
    def _writeXMLCustomResult(self, resNode, mResults):
        raise NotImplementedError("Abstract method.")

