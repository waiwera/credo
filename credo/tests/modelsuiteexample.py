from builtins import zip
from builtins import range
import itertools
import operator
from credo import modelsuite as msuite
from credo.modelrun import ModelRun
import credo.modelsuite as msuite

l1 = list(range(-3000, 3001, 1000))
l2 = [0.4, 0.5, 0.7]

print "Input lists of ranges to vary are"
print l1
print l2
print ""

v1 = msuite.StgXMLVariant("components.surfShape.minX", l1)
v2 = msuite.StgXMLVariant("gravity", l2)
varDict = {"surfShape":v1, "gravity":v2}

def testVarGenFuncs(iterGen):
    valuesIter = msuite.getParamValuesIter(varDict, iterGen)
    print "Value tuples:\n%s" % list(valuesIter)
    indicesIter = msuite.getVariantIndicesIter(varDict, iterGen)
    print "Indices into vars list:\n%s" % list(indicesIter)
    indicesIter = msuite.getVariantIndicesIter(varDict, iterGen)
    varNameDicts = msuite.getVariantNameDicts(varDict, indicesIter)
    print "Dictionary of var names:values :\n%s" % varNameDicts
    indicesIter = msuite.getVariantIndicesIter(varDict, iterGen)
    varPathDicts = msuite.getVariantParamPathDicts(varDict, indicesIter)
    print "Dictionary of var paths:values :\n%s" % varPathDicts
    indicesIter = msuite.getVariantIndicesIter(varDict, iterGen)
    subPaths = msuite.getTextParamValsSubdirs(varDict, indicesIter)
    print "Sub-paths (textual):\n%s" % subPaths
    indicesIter = msuite.getVariantIndicesIter(varDict, iterGen)
    cmdLineOvers = msuite.getVariantCmdLineOverrides(varDict, indicesIter)
    print "Cmd-line strings:\n%s" % cmdLineOvers
    print "subDirs, strs:"
    subDirsAndCmdLines = list(zip(subPaths, cmdLineOvers))
    for subDir, cmdLineStr in subDirsAndCmdLines:
        print "  %s: '%s'" % (subDir, cmdLineStr)
    print "Indexes and results of a certain parameter"
    gravRunIs = msuite.getVarRunIs('gravity', varDict, varNameDicts)
    print "Run Indices of variant 'gravity':\n%s" % gravRunIs
    surfValsMap = msuite.getOtherParamValsByVarRunIs(gravRunIs, varNameDicts,
        'surfShape')
    print "Run Indices of variant 'surfShape' sorted by 'gravity':\n%s" \
        % (surfValsMap)


print "Generating with a Zip iteration strategy"
testVarGenFuncs(itertools.izip)

print "\nNow Generating with a Product iteration strategy"
testVarGenFuncs(msuite.product)
