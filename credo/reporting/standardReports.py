import os, math
import PIL
import credo.modelsuite as msuite

def getColorStatusStr(tcStatus, rGen):
    if tcStatus.statusStr == 'Pass':
        color = 'green'
    else:
        color = 'red'
    colorStr = rGen.getColorTextStr(tcStatus, color)
    ':%s:`%s`' % (color, tcStatus)
    return colorStr

def addTestCompElements(sciBTest, rGen, level):
    elements = []
    elements.append(rGen.getHeaderEl("Single Run Test Components", level))
    for runI, srTCs in enumerate(sciBTest.testComps):
        elements.append(rGen.getHeaderEl("Run %d" % runI, level+1))
        for srName, srTC in srTCs.iteritems():
            elements.extend(testCompElement(srName, srTC, level+2, rGen))
    return elements

def testCompElement(tcName, srTC, level, rGen):
    elements = []
    resultStr = getColorStatusStr(srTC.tcStatus, rGen)
    elements.append(rGen.getHeaderEl("'%s' (%s): %s" % \
            (tcName, srTC.tcType, resultStr), level))
    elements.append(rGen.getParaEl(srTC.tcStatus.detailMsg, level))
    result = elements
    return result

def modelVariantsTable(mSuite, rGen, level):
    elements = []
    elements.append(rGen.getHeaderEl("Model Variants", level))
    headers = ["Run"]
    for mVarName in mSuite.modelVariants.iterkeys():
        headers.append(mVarName)
    data = [[] for runI in range(len(mSuite.runs))]
    valIter = msuite.getParamValuesIter(mSuite.modelVariants, mSuite.iterGen)
    for ii, values in enumerate(valIter):
        data[ii].append(ii)
        data[ii].extend(list(values))
    table = rGen.getSimpleDataTableEl(headers, data)
    elements.append(table)
    return elements

def modelImagesDisplay(mSuite, rGen, level, imgPerRow=1):
    imageInfos = mSuite.modelImagesToDisplay
    elements = []
    if mSuite.iterGen is not None:
        inIter = msuite.getVariantIndicesIter(mSuite.modelVariants,
            mSuite.iterGen)
        varNameDicts = msuite.getVariantNameDicts(mSuite.modelVariants, inIter)
    for runI, imagesPerRun in enumerate(imageInfos):
        #Allow runs with no images (may not be interesting).
        if len(imagesPerRun) == 0:
            continue
        mRun = mSuite.runs[runI]
        elements.append(rGen.getHeaderEl("Run %d: %s" % (runI,
            mSuite.runs[runI].name), level))
        # TODO: optional info to provide with each run.
        #if mSuite.iterGen is not None:
        #    elements.append(rGen.getHeaderEl("%s" % varNameDicts[runI],
        #        style=ParaStyle))
        # Put the images in a table
        nRows = int(math.ceil(len(imagesPerRun)/float(imgPerRow)))
        data = [[] for rowI in range(nRows)]
        rowI = 0
        for ii, imgInfo in enumerate(imagesPerRun):
            hdrText = "Timestep %d:" % (imgInfo[0])
            if imgInfo[1] != "": hdrText += " (%s)" % imgInfo[1]
            imgFName = os.path.join(mRun.basePath, mRun.outputPath,
                'window.%.5d.png' % imgInfo[0])
            # Set possible thumbnail size - can reduce file size if many
            #  images are being used.
            tScale = 1/float(imgPerRow) * 100
            # Set display size on page
            img = PIL.Image.open(imgFName)
            initWidth, initHeight = img.size
            ratio = initHeight / float(initWidth)
            newWidth = int(math.floor((rGen.PAGE_WIDTH*.9) / float(imgPerRow)))
            newHeight = int(math.floor(newWidth * ratio))
            data[rowI].append(rGen.getImageEls(imgFName, width=newWidth,
                height=newHeight, tScale=tScale, hdrText=hdrText))
            if (ii+1) % imgPerRow == 0: rowI += 1
        table = rGen.getTableEl(data)
        elements.append(table)
    result = elements
    return result

def defaultAnalysisImgEls(mSuite, rGen, level):
    elements = []
    elements.append(rGen.getHeaderEl("Analysis Images", level))
    if mSuite.analysisImages is not None:
        for imgFile in mSuite.analysisImages:
            elements.extend(rGen.getImageEls(os.path.join(
                mSuite.runs[0].basePath, mSuite.outputPathBase, imgFile),
                width=rGen.PAGE_WIDTH * .6))
    return elements

def makeSuiteReport(mSuite, mResults, rGen, outName, imgPerRow=3):
    #content
    # TODO: would be good is suite had a name here .. use output path for now.
    title = "Suite Report: %s" % mSuite.outputPathBase
    specDict = {
        "outputPathBase" : mSuite.outputPathBase}
    #Build doc la
    elements = []
    level = 1
    elements.append(rGen.getHeaderEl(title, level))
    level += 1
    elements.append(rGen.getHeaderEl("Specification", level))
    elements.extend(rGen.getDefListEls(specDict))
    if mSuite.iterGen is not None:
        elements.extend(modelVariantsTable(mSuite, rGen, level))
    elements.extend(defaultAnalysisImgEls(mSuite, rGen, level))
    if mSuite.modelImagesToDisplay is not None:
        elements.append(rGen.getHeaderEl("Model Run Images", level))
        elements.extend(modelImagesDisplay(mSuite, rGen, level+1,
            imgPerRow=imgPerRow))
    rGen.makeDoc(elements, title, outName)
    print "Saved report at %s (%s type)." % (outName, rGen.rType)


def makeSciBenchReport(sciBTest, mResults, rGen, outName, imgPerRow=3):
    """Make a science benchmark report.
    :param sciBTest: a science benchmark test to create report of.
    :param rGen: a report generator instatiation.
    :param outName: name of file to save generated report as.
    :param imgPerRow: how many images to use per row."""
    #content
    title = "%s Report" % sciBTest.testName
    description = sciBTest.description
    resultStr = getColorStatusStr(sciBTest.testStatus, rGen)
    specDict = {
        "outputPathBase" : sciBTest.outputPathBase,
        "nproc" : sciBTest.nproc}
    #Assume for now all results gathered from same machine.
    initRes = mResults[0]
    if initRes.jobMetaInfo is not None:
        provDict = {
            "node" : initRes.jobMetaInfo.platform['node'],
            "platform" : initRes.jobMetaInfo.verbPlatformString(),
            "basePath" : sciBTest.basePath,
            "start time" : initRes.jobMetaInfo.submitTime,
            "run type" : initRes.jobMetaInfo.runType}
        #TODO: info on model app version used.
    else:
        provDict = {"": ""}
    #TODO: performance
    perfDict = {}
    for runI, mRes in enumerate(mResults):
        jmeta = mRes.jobMetaInfo
        if jmeta is not None:
            perfDict["Run %i" % runI] = jmeta.performance

    #Build doc layout
    elements = []
    level = 1
    elements.append(rGen.getHeaderEl(title, level))
    level += 1
    elements.append(rGen.getHeaderEl("Overall Result: %s" % resultStr, level))
    elements.append(rGen.getHeaderEl("Description", level))
    elements.append(rGen.getParaEl(description, level))
    elements.append(rGen.getHeaderEl("Specification", level))
    elements.extend(rGen.getDefListEls(specDict))
    elements.append(rGen.getHeaderEl("Provenance", level))
    elements.extend(rGen.getDefListEls(provDict))
    elements.append(rGen.getHeaderEl("Performance Info", level))
    elements.extend(rGen.getDefListEls(perfDict))
    # Force a page break here in Document output
    #elements.append(rGen.getPageBreak())
    tcElements = addTestCompElements(sciBTest, rGen, level)
    elements.extend(tcElements)
    # Display requested images
    elements.extend(defaultAnalysisImgEls(sciBTest.mSuite, rGen, level))
    if sciBTest.mSuite.modelImagesToDisplay is not None:
        elements.append(rGen.getHeaderEl("Model Run Images", level))
        elements.extend(modelImagesDisplay(sciBTest.mSuite, rGen, level+1,
            imgPerRow=imgPerRow))
    rGen.makeDoc(elements, title, outName)
    print "Saved report at %s (%s type)." % (outName, rGen.rType)
    # Update the list of generated reports
    sciBTest.generatedReports.append(outName)
