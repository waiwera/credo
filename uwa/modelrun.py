from lxml import etree
import uwa.modelresult
from uwa.io import stgxml
from uwa.analysis import fields

class ModelRun:
    '''A class to keep records about a StgDomain/Underworld Model Run,
    including access to the underlying XML of the actual model'''
    def __init__(self, name, modelInputFiles, outputPath, logPath="./log",\
     cpReadPath=None, nproc=1):
        self.name = name
        self.modelInputFiles = modelInputFiles
        self.outputPath = outputPath
        self.cpReadPath = cpReadPath
        self.logPath = logPath
        self.jobParams = JobParams(nproc) 
        # TODO: should the below actually be compulsory?
        self.simParams = None
        self.analysis = {}
        self.analysis['fieldTests'] = fields.FieldTestsInfo()
        self.cpFields = []
        self.analysisXML = None

class JobParams:
    def __init__(self, nproc):
        self.nproc = int(nproc)

    def writeInfoXML(self, parentNode):
        '''Writes information about this class into an existing, open XML
         doc node, in a child list'''
        jpNode = etree.SubElement(parentNode, 'jobParams')
        etree.SubElement(jpNode, 'nproc').text = str(self.nproc)

class StgParamInfo:
    '''A simple Class that keeps track of the type of a StgParam, and it's full
    name'''
    def __init__( self, stgName, pType, defVal ):
        self.stgName = str(stgName)
        assert isinstance(pType, type)
        assert pType in [int,float,str,bool]
        self.pType = pType
        # Allow None as a special value, else the default value should be of
        # correct type during construction
        if defVal is not None:
            assert isinstance(defVal, self.pType)
        self.defVal = defVal

    def checkType( self, value ):
        if (value is not None) and (not isinstance(value, self.pType)):
            raise ValueError("Tried to set StgParam \"%s\" to %s, of type %s,"\
                "but this param is of type %s" % \
                (self.stgName, str(value), str(type(value)), str(self.pType)))


class SimParams:
    '''A class to keep records about the simulation parameters used for a
     StgDomain/Underworld Model Run, such as number of timesteps to run for'''

    stgParamInfos = { \
        'nsteps':StgParamInfo("maxTimeSteps", int, None), \
        'stoptime':StgParamInfo("stopTime",float, None), \
        'cpevery':StgParamInfo("checkpointEvery",int, 1), \
        'dumpevery':StgParamInfo("dumpEvery",int, 1), \
        'restartstep':StgParamInfo("restartTimestep",int, None) }

    def __init__(self, **kwargs):

        for paramName, stgParamInfo in self.stgParamInfos.iteritems():
            self.setParam(paramName, stgParamInfo.defVal)

        # Set all parameters provided to init function
        for param, val in kwargs.iteritems():
            paramFound = False
            # Allow the user to set by param name on this class, or actual name
            if param in self.stgParamInfos.keys():
                paramFound = True
                self.setParam(param, val)
            else:    
                for paramName, stgParamInfo in self.stgParamInfos.iteritems():
                    if param == stgParamInfo.stgName:
                        paramFound = True
                        self.setParam(param, val)
                        break
                    
            if paramFound == False:        
                valueErrorStr = "provided Sim Parameter %s not in allowed"\
                    " list of parameters to set" % param
                raise ValueError(valueErrorStr)

    def setParam(self, paramName, val):    
        assert paramName in self.stgParamInfos.keys()
        self.__dict__[paramName] = val
        self.stgParamInfos[paramName].checkType(val)

    def getParam(self, paramName):    
        return self.__dict__[paramName]

    def checkValidParams(self):
        if (self.nsteps is None) and (self.stoptime is None):
            raise ValueError("neither nsteps nor stoptime set")

    def writeInfoXML(self, parentNode):
        '''Writes information about this class into an existing, open XML doc
         node, in a child list'''
        spNode = etree.SubElement(parentNode, 'simParams')
        for param in self.stgParamInfos:
            assert(param in self.__dict__)
            etree.SubElement(spNode, param).text = str(self.__dict__[param])
    
    def writeStgDataXML(self, xmlNode):
        '''Writes the parameters of this class as parameters in a StGermain
         XML file'''
        for paramName, stgParam in self.stgParamInfos.iteritems():
            val = self.getParam(paramName)
            if val is not None:
                stgxml.writeParam(xmlNode, stgParam.stgName, val,\
                    mt='replace')

    def readFromStgXML(self, inputFilesList):
        '''Reads all the parameters of this class from a given StGermain 
        set of input files'''
        ffile=stgxml.createFlattenedXML(inputFilesList)
        xmlDoc = etree.parse(ffile)
        stgRoot = xmlDoc.getroot()
        for param, stgParam in self.stgParamInfos.iteritems():
            # some of these may be none, but is ok since will check below
            val = stgxml.getParamValue(stgRoot, stgParam.stgName,\
                stgParam.pType)
            self.setParam(param, val)

        self.checkValidParams()
        os.remove(ffile)


def writeModelRunXML(modelRun, outputPath="", filename="", update=False, \
        prettyPrint=True):
    assert isinstance(modelRun, ModelRun)
    if filename == "":
        filename = defaultModelRunFilename(modelRun.name)
    if outputPath == "":
        outputPath=modelRun.outputPath
    outputPath+=os.sep    

    # create XML document
    root = etree.Element('StgModelRun')
    xmlDoc = etree.ElementTree(root)
    # Write key entries:
    # Model description (grab from XML file perhaps)
    name = etree.SubElement(root, 'name')
    name.text = modelRun.name
    filesList = etree.SubElement(root, 'modelInputFiles')
    for xmlFilename in modelRun.modelInputFiles:
        modFile = etree.SubElement(filesList, 'inputFile')
        modFile.text = xmlFilename
    etree.SubElement(root, 'outputPath').text = modelRun.outputPath
    if modelRun.cpReadPath:
        etree.SubElement(root, 'cpReadPath').text = modelRun.cpReadPath
    modelRun.jobParams.writeInfoXML(root)
    if not modelRun.simParams:
        simParams = SimParams()
        simParams.readFromStgXML(modelRun.modelInputFiles)
        simParams.writeInfoXML(root)
    else:    
        modelRun.simParams.writeInfoXML(root)

    analysisNode = etree.SubElement(root, 'analysis')
    for toolName, analysisTool in modelRun.analysis.iteritems():
        analysisTool.writeInfoXML(analysisNode)

    # TODO : write info on cpFields?

    # Write the file
    if not os.path.exists(outputPath):
        os.makedirs(outputPath)
    outFile = open(outputPath+filename, 'w')
    xmlDoc.write(outFile, pretty_print=prettyPrint)
    outFile.close()
    return outputPath+filename

def defaultModelRunFilename(modelName):    
    return 'ModelRun-'+modelName+'.xml'

def analysisXMLGen(modelRun, filename="analysis.xml"):
    # create XML document
    nsMap = { None: "http://www.vpac.org/StGermain/XML_IO_Handler/Jun2003" }
    root = etree.Element(stgxml.stgRootTag, nsmap=nsMap)
    xmlDoc = etree.ElementTree(root)
    # Write key entries:
    stgxml.writeParam(root, 'outputPath', modelRun.outputPath, mt='replace')
    if modelRun.cpReadPath:
        stgxml.writeParam(root, 'checkpointReadPath', modelRun.cpReadPath, mt='replace')
    if modelRun.simParams:
        modelRun.simParams.writeStgDataXML(root)
    for analysisName, analysisTool in modelRun.analysis.iteritems():
        if not analysisTool.fromXML:
            analysisTool.writeStgDataXML(root)

    # This is so we can checkpoint fields list: defined in FieldVariable.c
    if len(modelRun.cpFields):
        stgxml.writeParamList(root, 'FieldVariablesToCheckpoint', \
            modelRun.cpFields, mt='replace')

    # Write the file
    outFile = open(filename, 'w')
    xmlDoc.write(outFile, pretty_print=True)
    outFile.close()
    return filename

##################

import sys
import os

# Assume user has updated their path correctly.
mpiCommand="mpirun"

# First some helper functions to help set up the run
# Should probably go into io sub-package
def stgCmdLineParam(paramName, val):
    '''Format a given parameter and it's value correctly for passing to
     StGermain on the command line, to over-ride something in a model XML'''
    return "--%s=%s" % (paramName, str(val))

def strRes(resTuple):
    '''Turn a given tuple of resolutions into a string, suitable for using
     as an output dir'''
    assert len(resTuple) in range(2,4)
    resStr = ""
    for res in resTuple[:-1]: resStr += str(res)+"x"
    resStr += str(resTuple[-1])
    return resStr

def generateResOpts(resTuple):
    '''Given a tuple of desired resolutions for a model, convert this to
    options to pass to StG on the command line'''
    # ResParams should probably be part of a useful struct/dict stored in
    # standard place.
    resParams=["elementResI","elementResJ","elementResK"]
    assert len(resTuple) in range(2,4)
    resOptsStr=""
    for ii in range(len(resTuple)):
        resOptsStr+=stgCmdLineParam(resParams[ii],resTuple[ii])+" "

    # This is to ensure, since we're overriding, if only 2D model is being
    # run, it ignores any 3rd dimension spec set in the original model file
    resOptsStr+=stgCmdLineParam("dim",len(resTuple))
    return resOptsStr


# TODO: some of this functionality could be handled via strategy pattern - 
# JobRunner (the MPI stuff)
def runModel(modelRun, extraCmdLineOpts=None):

    # Check runExe found in path

    # Pre-run checks for validity - e.g. at least one input file,
    # nproc is sensible value
    if (modelRun.simParams):
        modelRun.simParams.checkValidParams()

    # Construct run line
    mpiPart = "%s -np %d " % (mpiCommand, modelRun.jobParams.nproc)
    runExe=uwa.getVerifyStgExePath("StGermain")
    stgPart = "%s " % (runExe)
    for inputFile in modelRun.modelInputFiles:    
        stgPart += inputFile+" "
    if modelRun.analysisXML:
        stgPart += modelRun.analysisXML+" "

    # TODO: How to best handle custom command line options
    # Perhaps these should be passed through, either by script or as part of
    # model definition
    # Possibly a list would be better than a straight string, to help user
    # avoid spacing stuff-ups
    if extraCmdLineOpts:
        stgPart += " "+extraCmdLineOpts

    runCommand = mpiPart + stgPart + " > logFile.txt"

    # Run the run command, sending stdout and stderr to defined log paths
    print runCommand
    # TODO: the mpirunner should check things like mpd are set up properly,
    # in case of mpich2
    os.system(runCommand)

    # Check status of run (eg error status)

    # Construct a modelResult
    # Get necessary stuff from FrequentOutput.dat
    # TODO: this should be in a sub-module - is currently quite hacky
    freqFile = open(modelRun.outputPath + "/FrequentOutput.dat", 'r')

    # Parse out the headings
    headerLine = freqFile.readline()
    cols = headerLine.split()

    # Obtain time and memory at time-stamp specified by problem.steps
    lines = freqFile.readlines()
    lastLine = lines[-1]
    cols = lastLine.split()
    tSteps = float(cols[0])
    simTime = float(cols[1])

    result = uwa.modelresult.ModelResult(modelRun.name, simTime)
    
    return result
