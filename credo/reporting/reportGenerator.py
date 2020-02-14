from builtins import object

class ReportGenerator(object):
    def __init__(self, rType):
        #nothing to do for base class
        self.rType = rType

    def getHeaderEl(self, txt, level):
        raise NotImplementedError("Abstract base class.")

    def getParaEl(self, txt, level):
        raise NotImplementedError("Abstract base class.")

    def getDefListEls(self, listDict):
        raise NotImplementedError("Abstract base class.")

    def getSimpleTableEl(self, headerEntries, dataEntries):
        raise NotImplementedError("Abstract base class.")

    def getTableEl(self, tableRowEntriesList):
        raise NotImplementedError("Abstract base class.")

    def getImageEls(self, imgFilename, hdrText=None, width=None, height=None,
            scale=None, tScale=None):
        raise NotImplementedError("Abstract base class.")

    def getPageBreak(self):
        raise NotImplementedError("Abstract base class.")

    def makeDoc(self, docElements, title, outFilename):
        raise NotImplementedError("Abstract base class.")

    def getColorTextStr(self, textStr, colorName):
        raise NotImplementedError("Abstract base class.")



