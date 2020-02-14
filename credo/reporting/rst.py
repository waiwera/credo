"""Utils/primitives useful in constructing an RST report doc."""
from builtins import str
from builtins import map
from builtins import range
import os
import textwrap
from .reportGenerator import ReportGenerator

#Multiple header lines
# in Sphinx: ['#', '*', '=', '-', '^', '"']
rstHeaderChars = ['*', '=', '-', '^', '"', '+']

#Arbitrary preferred width of page view
PAGE_WIDTH = 800

rolesList = ['green', 'red']

def getRolesStr():
    #Currently just for custom colours.
    rolesStr = ""
    for role in rolesList:
        rolesStr += ".. role:: %s\n\n" % role
    return rolesStr

def dedentAll(s):
    sList = [line.lstrip() for line in s.split('\n')]
    return '\n'.join(sList)

def reIndent(s, numSpaces, keepInitSpaces = True):
    """Re-Indent a string with given number of numSpaces preceding each line.
    if keepInitSpaces is true, whitespace at start of initial lines is kept
    in output and added to numSpaces."""
    s2 = s.split('\n')
    sList = []
    for line in s2:
        if line == '':
            sList.append('')
        else:
            if not keepInitSpaces:
                line = line.lstrip()
            sList.append(' ' * numSpaces + line)
    s3 = '\n'.join(sList)
    return s3

class RstGenerator(ReportGenerator):
    """An RST (ReStructured Text) implementation of the ReportGenerator
    class."""
    def __init__(self, basePath):
        ReportGenerator.__init__(self, "RST")
        self.PAGE_WIDTH = PAGE_WIDTH
        self.basePath = basePath
        self.stdExt = "rst"

    def getHeaderEl(self, txt, level):
        """Get a string suitable for an RST header."""
        uLine = rstHeaderChars[level-1] * len(txt)
        headerStr = "%s\n%s\n\n" % (txt, uLine)
        return headerStr

    def getParaEl(self, txt, level):
        #TODO: handle level
        paraStr = dedentAll(txt)
        paraStr = textwrap.fill(paraStr, 75)
        return paraStr + "\n\n"

    def getDefListEls(self, listDict):
        resStr = ""
        for key, val in list(listDict.items()):
            resStr += " * %s: %s\n" % (key, val)
        resStr += "\n"
        return [resStr]

    def getSimpleDataTableEl(self, headers, data):
        # TODO: Use a proper abbreviated RST table syntax
        newHeaders = ["*%s*" % hdr for hdr in headers]
        newData = data[:]
        for rowI in range(len(newData)):
            for entryI in range(len(newData[rowI])):
                newData[rowI][entryI] = str(newData[rowI][entryI])
        newTableData = [newHeaders] + newData
        return self.getTableEl(newTableData)

    def getTableEl(self, tableData):
        """Note: we chose the RST list-table syntax, since this allows
        arbitrarily long/complex table entries."""
        resultStr = ".. list-table::\n\n"
        nEntriesMax = max(list(map(len, tableData)))
        for dataLine in tableData:
            for elI, dataEl in enumerate(dataLine):
                if elI == 0:
                    prefix1stStr = ' ' * 3 + '* - '
                else:
                    prefix1stStr = ' ' * 3 + '  - '
                if isinstance(dataEl, list):
                    elementStr = "\n".join(dataEl)
                else:
                    elementStr = dataEl
                if elementStr[-1] != '\n':
                    elementStr += '\n'
                elementStr = reIndent(elementStr, len(prefix1stStr))
                #Now correct for special precursors
                elementStr = prefix1stStr + elementStr[len(prefix1stStr):]
                resultStr += elementStr
            # The list-table syntax requires equal-length rows - so buffer
            # out if needed.
            if len(dataLine) < nEntriesMax:
                elI += 1
                while elI < nEntriesMax:
                    prefix1stStr = ' ' * 3 + '  - '
                    resultStr += prefix1stStr + "\n\n"
                    elI += 1
        resultStr += '\n'
        return resultStr

    def getPageBreak(self):
        #This doesn't really make sense for RST, just print a comment here
        return ".. %s\n\n" % ('*' * 75)

    def getImageEls(self, imgFile, hdrText=None, width=None, height=None,
            scale=None, tScale=None):
        """
        .. note:: we ignore the `tScale` param for RST reports, since the
           images aren't embedded in the final report anyway."""
        resultEls = []
        if hdrText is not None:
            resultEls.append("**%s**\n" % hdrText)
        relImgFile = os.path.relpath(imgFile, self.basePath)
        resStr = ".. image:: %s\n" % relImgFile
        if scale is not None:
            resStr += "   :scale: %d %%\n" % scale
        if width is not None:
            resStr += "   :width: %d px\n" % width
        if height is not None:
            resStr += "   :height: %d px\n" % height
        resStr += "\n"
        resultEls.append(resStr)
        return resultEls

    def makeDoc(self, docElements, title, outFilename):
        outDoc = open(outFilename, "w")
        rolesStr = getRolesStr()
        outDoc.write(rolesStr)
        for lineStr in docElements:
            outDoc.write(lineStr)
        outDoc.close()

    def getColorTextStr(self, textStr, colorName):
        #Note: this relies on the roles function above.
        return ':%s:`%s`' % (colorName, textStr)

def generator(basePath):
    """Factory method."""
    return RstGenerator(basePath)
