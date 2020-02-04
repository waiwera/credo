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

"""
This module is for accessing and working with StGermain-related paths.
"""

import os
import glob
import shutil
import inspect
from credo.io import stgcmdline

STG_BASEDIRKEY = 'STG_BASEDIR'
STG_BINDIRKEY = 'STG_BINDIR'
STG_XMLDIRKEY = 'STG_XMLDIR'
STG_BLD_SUBDIR = "build"
STG_BIN_SUBDIR = os.path.join(STG_BLD_SUBDIR, "bin")
STG_LIB_SUBDIR = os.path.join(STG_BLD_SUBDIR, "lib")
STG_XML_SUBDIR = os.path.join(STG_LIB_SUBDIR, "StGermain")

def getVerifyStgExePath(exeName):
    """For a given executable name (eg "StGermain"), return the full path
    name of that executable (in the path given by the STG_BINDIR env variable).
    """
    stgPath = getStgBinPath()
    fullExePath = os.path.join(stgPath, exeName)
    if not os.path.exists(fullExePath):
        raise IOError("Error, in %s(): executable requested %s doesn't" \
            " exist/not valid in StGermain binary path (%s)." % \
            (inspect.stack()[0][3], exeName, stgPath))

    return fullExePath

def getVerifyStgMainExecutablePath():
    """return the full path to the main StGermain executable (in the path
    given by the STG_BINDIR env variable)"""
    return getVerifyStgExePath(stgcmdline.STGERMAIN_EXE_NAME)

def _getStgPath(pathDescription, pathEnviroVarKey, keySubDir=None,
        testFile=None):
    """Utility function: given a particular path environment variable key,
    and description, checks to see if that path exists and is valid.
    Will use :const:`STG_BASEDIRKEY` as a fallback if keySubDir is given."""
    fromKey = None
    if pathEnviroVarKey in os.environ:
        foundPath=os.environ[pathEnviroVarKey]
        fromKey = pathEnviroVarKey
    elif keySubDir is not None and STG_BASEDIRKEY in os.environ:
        stgBasePath = os.environ[STG_BASEDIRKEY]
        foundPath = os.path.join(stgBasePath, keySubDir)
        fromKey = STG_BASEDIRKEY
    else:
        if keySubDir:
            varsToUse = "either the %s or %s environment variable"\
                    % (pathEnviroVarKey, STG_BASEDIRKEY)
        else:
            varsToUse = "the %s environment variable"\
                    % (pathEnviroVarKey)

        errorMsg = "Error in %s(): since this script needs to"\
            " use %s, please set %s for use within CREDO.\n" \
            % (inspect.stack()[0][3], pathDescription, varsToUse)
        raise EnvironmentError(errorMsg)

    if not os.path.exists(foundPath):
        raise EnvironmentError("Error, in %s(): needed env variable %s is"\
            " set, but path it's" \
            " set to (%s) doesn't exist/not valid.\n" \
            % (inspect.stack()[0][3], fromKey, foundPath))
    if testFile is not None:
        if not os.path.exists(os.path.join(foundPath, testFile)):
            raise EnvironmentError("Error, in %s(): needed env variable %s is"\
                " set, path it's set" \
                " to (%s) is valid, but doesn't contain the '%s' file.\n"\
                % (inspect.stack()[0][3], fromKey, foundPath, testFile))
    return foundPath

def getStgBinPath():
    """Get the path of StGermain binaries (given by env variable STG_BINDIR)."""
    return _getStgPath("StGermain executables", STG_BINDIRKEY,
        keySubDir=STG_BIN_SUBDIR, testFile="StGermain")

def getStgStandardXMLPath():
    """Returns the path that StGermain standard XML files are stored in
    once installed (and is automatically searched within by StGermain
    when input files are specified on either the command line, or in
    include statements)."""
    return _getStgPath("StGermain standard XMLs", STG_XMLDIRKEY,
        keySubDir=STG_XML_SUBDIR)

def convertLocalXMLFilesToAbsPaths(inputFilesList, callingPath):
    """Check through the given input file list, and for any that aren't found
    relative to either the local directory or the StGermain standard path,
    convert them to be relative to the given `callingPath`

    :returns: new list of adjusted XML files
    """
    newInputFilesList = []
    for ii, iFile in enumerate(inputFilesList[:]):
        if os.path.exists(iFile) or xmlExistsInStdXMLPath(iFile):
            newInputFilesList.append(iFile)
        else:
            newInputFilesList.append(os.path.join(callingPath, iFile))

    return newInputFilesList

def checkAllXMLInputFilesExist(inputFilesList):
    """Checks a whole set of XML input files exist, and raises an IOError if
    one of them doesn't. See :func:`.checkXMLInputFileExists`."""
    for iFile in inputFilesList:
        checkXMLInputFileExists(iFile)
    return

def checkXMLInputFileExists(inputFile):
    """Check if an XML input file exists in either the standard
    XML path, or relative to the current directory. Raises an IOError
    if not."""
    if not os.path.exists(inputFile):
        if not xmlExistsInStdXMLPath(inputFile):
            stgStdXMLPath = getStgStandardXMLPath()
            raise IOError("One of the given input files, '%s',"\
                " doesn't exist in either the local directory,"\
                " or the StGermain standard path %s"\
                % (inputFile, stgStdXMLPath))
    return

def xmlExistsInStdXMLPath(inputFile):
    stgStdXMLPath = getStgStandardXMLPath()
    fileInStgPath = os.path.join(stgStdXMLPath, inputFile)
    return os.path.exists(fileInStgPath)

def moveAllToTargetPath(startPath, targetPath, fileExt):
    """Move all files with extension `fileExt` from `startPath` to
    `targetPath` - automatically over-writing any existing files with
    identical names."""
    if not os.path.exists(targetPath):
        os.makedirs(targetPath)
    for fname in glob.glob(os.path.join(startPath, "*."+fileExt)):
        target = os.path.join(targetPath, os.path.basename(fname))
        if (os.path.exists(target)): os.remove(target)
        shutil.move(fname, targetPath)
