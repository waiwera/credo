#! /usr/bin/env python
import os, copy
import csv
from credo.modelrun import ModelRun, SimParams
from credo.modelsuite import ModelSuite
import credo.jobrunner

jobRunner = credo.jobrunner.defaultRunner()

outPathBase = os.path.join('output','PPC_Compare')
if not os.path.exists(outPathBase):
    os.makedirs(outPathBase)

defParams = SimParams(nsteps=2)
stdRun = ModelRun("Arrhenius-normal",
    os.path.join('..','..', 'Underworld', 'InputFiles', 'Arrhenius.xml'),
    simParams=defParams)
ppcRun = ModelRun("Arrhenius-ppc", "Arrhenius.xml",
    basePath=os.path.join("Ppc_Testing","udw_inputfiles"),
    simParams=defParams)

stdSuite = ModelSuite(os.path.join(outPathBase, "arrBasic"))
ppcSuite = ModelSuite(os.path.join(os.getcwd(), outPathBase, "arrPIC"))

for ii in range(10):
    stdRun.outputPath = os.path.join(stdSuite.outputPathBase, "%.5d" % ii)
    ppcRun.outputPath = os.path.join(ppcSuite.outputPathBase, "%.5d" % ii)
    stdSuite.addRun(copy.deepcopy(stdRun))
    ppcSuite.addRun(copy.deepcopy(ppcRun))

stdResults = jobRunner.runSuite(stdSuite)
ppcResults = jobRunner.runSuite(ppcSuite)

#-----------------------------

cpuRegs = []
cpuPPCs = []
for stdRes, ppcRes in zip(stdResults, ppcResults):
    stdRes.readFrequentOutput()
    ppcRes.readFrequentOutput()
    fStep = stdRes.freqOutput.finalStep()
    cpuReg = stdRes.freqOutput.getValueAtStep('CPU_Time', fStep)
    cpuPPC = ppcRes.freqOutput.getValueAtStep('CPU_Time', fStep)
    print "CPU time regular was %g, PPC was %g" % (cpuReg, cpuPPC)
    cpuRegs.append(cpuReg)
    cpuPPCs.append(cpuPPC)

avgReg = sum(cpuRegs) / len(cpuRegs)
avgPPC = sum(cpuPPCs) / len(cpuPPCs)

print "Avg over 10 runs: regular=%f, PPC=%f" % (avgReg, avgPPC)
sName = os.path.join(outPathBase, "comparePPC.txt")
csvName = os.path.join(outPathBase, "comparePPC-runs.csv")
avgInfo = open(sName, "w")
avgInfo.write("Avg regular = %f\n" % avgReg)
avgInfo.write("Avg PPC = %f\n" % avgPPC)
avgInfo.close()
csvFile = open(csvName, "wb")
wtr = csv.writer(csvFile)
wtr.writerow(["Run", "Reg t(sec)", "PPC t(sec)"])
for runI, (cpuReg, cpuPPC) in enumerate(zip(cpuRegs, cpuPPCs)):
    wtr.writerow([runI, cpuReg, cpuPPC])
csvFile.close()

print "Wrote summary to %s, run results to %s" % (sName, csvName)
