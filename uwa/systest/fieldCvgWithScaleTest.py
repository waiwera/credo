from xml.etree import ElementTree as etree

from uwa.systest.api import TestComponent, UWA_PASS, UWA_FAIL
from uwa.io import stgcvg
import uwa.analysis.fields as fields

# The criteria of convergence: first is cvg rate, second is correlation
defFieldScaleCvgCriterions = {
    'VelocityField':(1.6,0.99),
    'PressureField':(0.9,0.99),
    'StrainRateField':(0.85,0.99),
    'recoveredSigmaField':(1.6,0.99),
    'recoveredPressureField':(1.6,0.99),
    'recoveredTauField':(1.6,0.99),
    'recoveredEpsDotField':(1.6,0.99) }

def testAllCvgWithScale(lenScales, fieldErrorData, fieldCvgCriterions):    
    """Given a lists of length scales, field error data (a dictionary 
    mapping field names to dofError lists for that field), and field
    convergence criterions, returns a Bool specifying whether all
    the fields met their required convergence criterions.
    
    The first two arguments can be created by running
    :func:`~uwa.analysis.fields.getFieldScaleCvgData_SingleCvgFile`
    on a path containing a single cvg file."""
    overallResult = True
    for fieldName, dofErrors in fieldErrorData.iteritems():
        convResult = fields.calcFieldCvgWithScale(fieldName, lenScales,
            dofErrors)
        meetsReq = testCvgWithScale(fieldName, convResult,
            fieldCvgCriterions[fieldName])
        if meetsReq == False:
            overallResult = False
    return overallResult    

def testCvgWithScale(fieldName, fieldConvResults, fieldCvgCriterion):
    '''Tests that for a given field, given a list of fieldConvResults 
    (See :func:`uwa.analysis.fields.calcFieldCvgWithScale`)
    - that they converge according to the given fieldCvgCriterion.
    
    :returns: result of test (Bool)'''

    reqCvgRate, reqCorr = fieldCvgCriterion
    dofStatuses = []

    for dofI, dofConv in enumerate(fieldConvResults):
        cvgRate, corr = dofConv
        print "Field %s, dof %d - cvg rate %6g, corr %6f" \
            % (fieldName, dofI, cvgRate, corr)
        #plt.plot(resLogs, errLogs)
        #plt.show()

        dofTestStatus = True
        if cvgRate < reqCvgRate: 
            dofTestStatus = False
            print "  -Bad! - cvg %6g less than req'd %6g for this field."\
                % (cvgRate, reqCvgRate)
        if corr < reqCorr:
            dofTestStatus = False
            print "  -Bad! - corr %6g less than req'd %6g for this field."\
                % (corr, reqCorr)
        if dofTestStatus: print "  -Good"
        dofStatuses.append(dofTestStatus)
    
    if False in dofStatuses:
        return False
    else: 
        return True

def getNumDofs(fComp, mResult):
    '''Hacky utility function to get the number of dofs of an fComp, by
    checking the result. Need to do this smarter/neater.'''
    fCompRes = fComp.getResult(mResult)
    return len(fCompRes.dofErrors)

def getDofErrorsByRun(fComp, resultsSet):
    '''For a given field comparison op, get all the dof errors from a set of
    runs, indexed primarily by run index.'''

    # A bit of a hack: need to store # of dofs per field better somewhere
    numDofs = getNumDofs(fComp, resultsSet[0])
    dofErrorsByRun = [[] for ii in range(numDofs)]

    # We need to index the dofErrors by run, then dofI, for cvg check
    for runI, mResult in enumerate(resultsSet):
        fCompRes = fComp.getResult(mResult)

        for dofI, dofError in enumerate(fCompRes.dofErrors):
            dofErrorsByRun[dofI].append(dofError)

    return dofErrorsByRun


class FieldCvgWithScaleTest(TestComponent):
    """Checks whether, for a particular set of fields, the error
    between each field and an (analytic or reference) solution
    reduces with increasing resolution at a required rate. 
    Thus similar to :class:`~uwa.systest.fieldWithinTolTest.FieldWithinTolTest`,
    except tests accuracy of solution with increasing resolution.

    This relies largely on functionality of:

    * :mod:`uwa.analysis.fields` to specify the comparison operations
    * :mod:`uwa.io.stgcvg` to analyse the "convergence" files containing
      comparison information produced by these operations.
    
    .. attribute:: fieldsToTest 

       A list of strings containing the names of fields that should be tested-
       i.e. those that will be compared with an expected solution. If left
       as `None` in constructor, this means the fieldsToTest list will be 
       expected to be defined in the StGermain model XML files themselves.
    
    .. attribute:: fieldCvgCrits

       List of Convergence criterions to be used when checking the fields.
       Currently required to be in the form used by the convernce checking 
       :func:`uwa.analysis.fields.calcFieldCvgWithScale`, which requires 
       tuples of the form (cvg_rate, correlation).

       .. note:: if this list doesn't contain a cvg criterion for a field
          that's tested, the behaviour is to skip the formal test of 
          this field, but print a warning (based on previous SYS test
          behaviour).

    .. attribute:: calcCvgFunc

       Function to use to calculate convergence of errors of a group
       of runs - currently uses 
       :func:`uwa.analysis.fields.calcFieldCvgWithScale` by default.
    
    .. attribute:: fComps

        A :class:`uwa.analysis.fields.FieldComparisonList` used as an
        operator to attach to ModelRuns to be tested, and do the actual
        comparison between fields.
    
    .. attribute:: fErrorsByRun

       Initially {}, after the test is completed will store a dictionary
       mapping each field name to a list of floats representing the global
       normalised error in the comparison, for each ModelRun, indexed by
       ModelRun.

    .. attribute:: fCvgMeetsReq

       Initially {}, after the test is completed will store a dictionary
       mapping each field name to a Bool recording whether the field error
       converged acceptably as resolution increased, according to the 
       convergence algorithm used.

    .. attribute:: fCvgResults

       Initially {}, after the test is completed will store a dictionary
       mapping each field name to a tuple containing information on
       actual convergence rate. See the return value of 
       :func:`uwa.analysis.fields.calcFieldCvgWithScale` for more.

    """  

    def __init__(self, fieldsToTest = None,
            calcCvgFunc = fields.calcFieldCvgWithScale,
            fieldCvgCrits = defFieldScaleCvgCriterions):
        TestComponent.__init__(self, "fieldCvgWithScaleTest")
        self.calcCvgFunc = calcCvgFunc
        self.fieldCvgCrits = fieldCvgCrits
        self.fieldsToTest = fieldsToTest
        # TODO: would be good to check here that the fieldsToTest have
        # cvg info provided in the  fieldCvgCrits dict. However becuase we
        # allow fieldsToTest=None to mean "read from XML", can't always
        # do this just yet.
        self.fComps = None
        self.fErrorsByRun = {}
        self.fCvgMeetsReq = {}
        self.fCvgResults = {}

    def attachOps(self, modelRun):
        """Implements base class
        :meth:`uwa.systest.api.TestComponent.attachOps`."""
        self.fComps = fields.FieldComparisonList()
        if self.fieldsToTest == None:
            self.fComps.readFromStgXML(modelRun.modelInputFiles)
        else:
            for fieldName in self.fieldsToTest:
                self.fComps.add(fields.FieldComparisonOp(fieldName))
        modelRun.analysisOps['fieldComparisons'] = self.fComps

    def check(self, resultsSet):
        """Implements base class
        :meth:`uwa.systest.api.TestComponent.check`.
        
        As well as performing check, will save relevant into to attributes
        :attr:`.fErrorsByRun`, :attr:`.fCvgMeetsReq`, :attr:`.fCvgResults`."""
        # NB: could store this another way in model info?
        lenScales = self._getLenScales(resultsSet)    
        self.fErrorsByRun = {}
        self.fCvgMeetsReq = {}
        self.fCvgResults = {}

        for fName, fCompOp in self.fComps.fields.iteritems():
            self.fErrorsByRun[fName] = getDofErrorsByRun(fCompOp, resultsSet)
            fieldConv = self.calcCvgFunc(fName, lenScales,
                self.fErrorsByRun[fName])
            self.fCvgResults[fName] = fieldConv
            if fName in self.fieldCvgCrits:
                fResult = testCvgWithScale(fName, fieldConv,
                    self.fieldCvgCrits[fName])
                self.fCvgMeetsReq[fName] = fResult
            else:
                print "Warning: Field specified for comparison, '%s',"\
                    " doesn't have convergence criteria provided - thus"\
                    " not checking." % fName
                self.fCvgMeetsReq[fName] = None

        if False in self.fCvgResults.itervalues():
            # TODO: be more specific in statusMsg
            statusMsg = "The solution compared to the %s result didn't cvg"\
                " as expected with increasing resolution for all fields."\
                % (self.fComps.getCmpSrcString())
            self.tcStatus = UWA_FAIL(statusMsg)
            return False
        else:
            statusMsg = "The solution compared to the %s result converged"\
                " as expected with increasing resolution for all fields."\
                % (self.fComps.getCmpSrcString())
            self.tcStatus = UWA_PASS(statusMsg)
            return True

    def _writeXMLCustomSpec(self, specNode):
        if self.fComps == None:
            raise AttributeError("Unable to write XML for this TestComponent"\
                " until attachOps() has been called, and have been able to"\
                " read the model XML to find out name of fields to test.")
        etree.SubElement(specNode, 'fromXML', value=str(self.fComps.fromXML))
        fListNode = etree.SubElement(specNode, 'fields')
        for fName in self.fComps.fields.keys():
            fNode = etree.SubElement(fListNode, 'field')
            fNode.attrib['name'] = fName
            try:
                fieldCvgCrit = self.fieldCvgCrits[fName]
            except KeyError:
                # If the user hasn't specified cvg crit, just write N/A here.
                fNode.attrib['cvgRate'] = "N/A"
                fNode.attrib['corr'] = "N/A"
            else:
                fNode.attrib['cvgRate'] = str(fieldCvgCrit[0])
                fNode.attrib['corr'] = str(fieldCvgCrit[1])

    def _writeXMLCustomResult(self, resNode, resultsSet):
        frNode = etree.SubElement(resNode, 'fieldResultDetails')
        lenScales = self._getLenScales(resultsSet)    
        for fName, fComp in self.fComps.fields.iteritems():
            fieldNode = etree.SubElement(frNode, "field", name=fName)
            meetsReq = self.fCvgMeetsReq[fName]
            if meetsReq == None:
                fieldNode.attrib['cvgMeetsReq'] = "N/A"
            else:    
                fieldNode.attrib['cvgMeetsReq'] = str(meetsReq)

            for dofI, dofErrorsByRun in enumerate(self.fErrorsByRun[fName]):
                dofNode = etree.SubElement(fieldNode, "dof")
                dofNode.attrib["num"] = str(dofI)
                fieldCvgResult = self.fCvgResults[fName]
                assert(fieldCvgResult)
                dofCvgResult = fieldCvgResult[dofI]
                dofNode.attrib['cvgrate'] = "%8.6f" % dofCvgResult[0]
                dofNode.attrib['correlation'] = "%8.6f" % dofCvgResult[1]
                #TODO run name? and overall result?
                runEsNode = etree.SubElement(dofNode, "runErrors")
                for runI, dofError in enumerate(dofErrorsByRun):
                    dofErrorNode = etree.SubElement(runEsNode, "dofError")
                    dofErrorNode.attrib['run_number'] = str(runI+1)
                    dofErrorNode.attrib['lenScale'] = "%8.6e"\
                        % (lenScales[runI])
                    dofErrorNode.attrib["error"] = "%6e" % dofError

    def _getLenScales(self, resultsSet):
        lenScales = []
        for runI, mResult in enumerate(resultsSet):
            cvgIndex = stgcvg.genConvergenceFileIndex(mResult.outputPath)
            # a bit hacky, need to redesign cvg stuff, esp len scales??
            try:
                cvgInfo = cvgIndex[self.fComps.fields.keys()[0]]
            except KeyError:
                if len(cvgIndex) == 0:
                    raise IOError("No field comparison check results"\
                        " were found in output path '%s'." % mResult.outputPath)
                else:
                    raise IOError("Comparison info for field '%s' not found."\
                        " Fields that had comparison info found for them"\
                        " in results were %s."\
                        % (self.fComps.fields.keys()[0], str(cvgIndex.keys())))
 
            lenScales.append(stgcvg.getRes(cvgInfo.filename))        
        return lenScales    
