#! /usr/bin/env python

"""Some useful scripts related to plotting CPU time for each timestep of
a series of ModelRuns.

If run from the command line, 1st argument should be the output path of
a ModelResult."""
from __future__ import print_function

import sys, math
from credo.modelresult import ModelResult

def getPerStepCPU_Times(freqOutput):
    """Given a freqOutput object, returns the array of per-step CPU times."""
    freqOutput.populateFromFile()
    assert 'CPU_Time' in freqOutput.headers
    cpuIncTimes = freqOutput.getValuesArray('CPU_Time')
    cpuTimes = [0] * len(cpuIncTimes)
    cpuTimes[0] = cpuIncTimes[0]
    for ii, t in enumerate(cpuIncTimes[1:]):
        cpuTimes[ii+1] = t - cpuIncTimes[ii]
    return cpuTimes

def plot(cpuTimes, modelDir):
    """Given array of cpu times per timestep, and a model dir, draws an
    on-screen plot."""
    import matplotlib.pyplot as plt
    plt.plot(cpuTimes)
    plt.xlabel("timestep")
    plt.ylim(0, math.ceil(max(cpuTimes)*10)/10.0)
    plt.ylabel("Time (sec)")
    plt.title("CPU Time per timestep\n(%s)" % modelDir)
    plt.show()

if __name__ == "__main__":
    try:
        outputPath = sys.argv[1]
    except:
        print("Bad input arguments - pass output path to model result.")
        raise
    mRes = ModelResult("plotModel", outputPath)
    mRes.readFrequentOutput()
    fo = mRes.freqOutput
    cpuTimes = getPerStepCPU_Times(fo)
    plot(cpuTimes, outputPath)
