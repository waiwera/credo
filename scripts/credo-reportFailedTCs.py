#!/usr/bin/env python
from __future__ import print_function
import os, operator, textwrap, glob
from xml.etree import ElementTree as etree

"""A small utility script to allow you to list all the failed system test
  components in your output directory."""

def getFailedTCsInNode(xmlNode):
    failedTCs = []
    runTCs = list(xmlNode)
    runTCs.sort(key=operator.attrgetter('attrib'))
    for srTCNode in runTCs:
        if srTCNode.attrib['status'] != 'Pass':
            failedTCs.append(srTCNode)
    return failedTCs

def printFailedTCs(sysTestFile, printMsgs=False):
    parser = etree.XMLParser()
    xmlDoc = etree.parse(sysTestFile, parser)
    baseNode = xmlDoc.getroot()
    tcsNode = baseNode.find('testComponents')
    srTCsNode = tcsNode.find('singleRunTestComponents')

    runFailedTCs = [getFailedTCsInNode(runNode) for runNode in srTCsNode]

    for runI in range(len(srTCsNode)):
        failedTCs = runFailedTCs[runI]
        if len(failedTCs) == 0: continue
        print("For run %d, %d failed components:" % (runI, len(failedTCs)))
        for failedTC in failedTCs:
            print("%s" % failedTC.attrib['name'])
        if printMsgs == True:
            print("Messages were:")
            for failedTC in failedTCs:
                msgText = failedTC.find('result').find('statusMsg').text
                print("'%s':%s\n[[%s]]" % (failedTC.attrib['name'],
                    failedTC.attrib['status'],
                    textwrap.fill(msgText)))

    mrTCsNode = tcsNode.find('multiRunTestComponents')
    mrFailedTCs = getFailedTCsInNode(mrTCsNode)
    if len(mrFailedTCs) > 0:
        print("Multi-run failed components (%d):" % len(mrFailedTCs))
        for failedTC in mrFailedTCs:
            print("%s" % failedTC.attrib['name'])

if __name__ == "__main__":
    for sysTestFile in sorted(glob.glob("output/*/SysTest-*.xml")):
        print("sysTestFile = %s" % sysTestFile)
        printFailedTCs(sysTestFile, printMsgs=False)
