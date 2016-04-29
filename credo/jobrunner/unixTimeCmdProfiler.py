import os, sys
import subprocess, shlex
from credo.jobrunner.api import PerformanceProfiler

"""A module for saving basic profiling info about ModelRuns using the Unix
time command.

Is split into basic functions (for use in simple procedural scripts) and the
relevant CREDO declarative :class:`credo.jobrunner.api.PerformanceProfiler`
class for using with :class:`credo.jobrunner.api.JobRunner` s.

.. note:: as the module name implies, only works on Unix systems."""

TIME_FMT_SPEC = ", "
TIME_FMT_SEP = "\n"

STD_NAMES = {
    "walltime": "E",
    "pageFaults": "F",
    "avgMem_KB": "K",
    "maxMem_KB": "M"}

#This could be customised to a sub-set if desired
DEFAULT_FMT_ELS = [(kw, val) for (kw, val) in STD_NAMES.items()]

class UnixTimeCmdHandle:
    def __init__(self, resFName):
        self.resFName = resFName

class UnixTimeCmdProfiler(PerformanceProfiler):
    """A performance profiler that uses the Unix 'time' command.

    .. attribute:: fmtEls

       Format elements to be used in determining what gets profiled.
    """
    def __init__(self, fmtEls=None):
        PerformanceProfiler.__init__(self, "UnixTimeCmd")
        if fmtEls == None:
            self.fmtEls = DEFAULT_FMT_ELS
        else:
            self.fmtEls = fmtEls

    def setup(self, modelName, modelBasePath, modelOutputPath, jobMetaInfo):
        if os.name != 'posix':
            raise OsError("This class can only do profiles on Unix OSs.")
        resFName = os.path.join(modelBasePath, modelOutputPath, "timeInfo.txt")
        if os.path.exists(resFName):
            os.unlink(resFName)
        h = UnixTimeCmdHandle(resFName)
        jobMetaInfo.profilerHandles[self.typeStr] = h

    def modifyRun(self, modelRun, oldModelRunCommand, jobMetaInfo):
        if os.name != 'posix':
            raise OsError("This class can only do profiles on Unix OSs.")
        fmtStr = getFmtString(self.fmtEls)
        h = jobMetaInfo.profilerHandles[self.typeStr]
        newModelRunCmd = "%s %s" % (getRunPrefix(h.resFName, fmtStr),
            oldModelRunCommand)
        return newModelRunCmd

    def attachPerformanceInfo(self, jobMetaInfo, modelResult):
        h = jobMetaInfo.profilerHandles[self.typeStr]
        #TODO: either here, or in the subfunction:
        # we have h.fmtEls - need to extend that so we can be smarter in parsing
        #  e.g. units of memory, or time units.
        resDict = getResDict(h.resFName)
        jobMetaInfo.performance[self.typeStr] = dict(resDict)

def getFmtString(fmtEls, fmtSpec=TIME_FMT_SPEC, fmtSep=TIME_FMT_SEP):
    """Return the format string to use, given a list of format elements,
    using standard separators, so it can be parsed later on.

    :arg fmtEls: a list of Tuples, of form (nameStr, fmtItem) - where
       nameStr is the name of the entry to return, and fmtItem is the
       'resource specifier' character as specified in 'man time'.

       e.g. [("runTime", "E")] - where "E" is the specifier for Elapsed time"""
    fmtEntries = []
    for fmtEl in fmtEls:
        fmtEntries.append("%s%s%%%s" % (fmtEl[0], fmtSpec, fmtEl[1]))
    fmtStr = fmtSep.join(fmtEntries)
    return fmtStr

def getResDict(resFName, fmtSpec=TIME_FMT_SPEC, fmtSep=TIME_FMT_SEP):
    """Get a dictionary of results, contained in the given resFName,
    formatted in the standard way as done by getFmtString."""
    resFile = open(resFName, "r")
    results = resFile.read()
    perfInfos = results.split(fmtSep)
    resDict = {}
    for infoSpec in perfInfos:
        if infoSpec.strip() == '': continue
        try:
            name, val = infoSpec.split(fmtSpec)
        except ValueError:
            print "Bad performance info spec '%s' - splits into too many"\
                " entries" % (infoSpec)
            pass
        else:
            #NB: assuming all values here are floats.
            #resDict[name] = float(val)
            #TODO: temporary hack, need a system
            if name == "walltime":
                val = parseUnixTimeElapsed(val)
            else:
                val = float(val)
            resDict[name] = val
    return resDict

def parseUnixTimeElapsed(timeElapsedStr):
    secStrs = timeElapsedStr.split(":")
    if len(secStrs) == 2:
        hours = 0
        mins = int(secStrs[0])
        secs = float(secStrs[1])
    elif len(secStrs) == 3:
        hours = int(secStrs[0])
        mins = int(secStrs[1])
        secs = float(secStrs[2])
    else:
        raise ValueError("Error, time elapsed string given, '%s',"\
            "doesn't conform to Unix time command's elapsed string format."\
            % timeElapsedStr)
    return hours * (60*60) + mins * 60 + secs

def getRunPrefix(resFName, fmtStr):
    """Get the prefix for a run that will apply the time command.

    Do "man time" for more info.

    :arg resFName: filename that 'time' profiling results should be saved to.
    :arg fmtStr: format string to use."""

    return '/usr/bin/env time -o %s -f "%s" ' % (resFName, fmtStr)


if __name__ == "__main__":
    # A basic procedural function
    #runJobCmd = "./Underworld RayleighTaylorBenchmark.xml --maxTimeSteps=1"
    runJobCmd = " ".join(sys.argv[1:])
    if runJobCmd.strip() == "":
        print "You need to supply a command to time as an argument."
        sys.exit()

    print "*" * 60
    print "for command '%s'" % runJobCmd

    fmtEls = [("real", "E"), ("pageFaults", "F"), ("avgMem(KB)", "K"),
        ("maxMem(KB)", "M")]
    fmt = getFmtString(fmtEls)
    #print "fmtString is", fmt

    resFName = "timeInfo.txt"
    if os.path.exists(resFName):
        os.unlink(resFName)
    runCmd = "%s %s" % (getRunPrefix(resFName, fmt), runJobCmd)
    #print "About to run:", runCmd

    stdOutFile = open("stdOut.txt", "w")
    stdErrFile = open("stdErr.txt", "w")
    subprocess.call(shlex.split(runCmd), stdout=stdOutFile, stderr=stdErrFile)

    # Now parse resulting perf info into a dict
    resDict = getResDict(resFName)
    print "performance info is %s" % resDict
