import reportlab.platypus as platypus
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch
from reportlab.lib import colors
import PIL
from .reportGenerator import ReportGenerator

PAGE_WIDTH=defaultPageSize[0]
PAGE_HEIGHT=defaultPageSize[1]
# Save ReportLab header styles for convenience.
styles = getSampleStyleSheet()
ParaStyle = styles["Normal"]
PreStyle = styles["Code"]
BulletStyle = styles["Bullet"]
HeaderStyleList = [
    styles["Heading1"],
    styles["Heading2"],
    styles["Heading3"],
    styles["Heading4"],
    styles["Heading5"],
    styles["Heading6"]]

def header(txt, style=HeaderStyleList[0], klass=platypus.Paragraph, sep=0.3):
    """Low-level interface func to ReportLab headers."""
    s = platypus.Spacer(0.2*inch, sep*inch)
    para = klass(txt, style)
    sect = [s, para]
    result = platypus.KeepTogether(sect)
    return result

class ReportLabGenerator(ReportGenerator):
    """A report generator to create PDF documents using the Python
    ReportLab toolkit."""
    def __init__(self, basePath):
        ReportGenerator.__init__(self, "ReportLab")
        self.PAGE_WIDTH = PAGE_WIDTH
        self.basePath = basePath
        self.stdExt = "pdf"

    def getHeaderEl(self, txt, level):
        return header(txt, style=HeaderStyleList[level-1], sep=0.05)

    def getParaEl(self, txt, level):
        return header(txt, style=ParaStyle, sep=0.1)

    def getPreEl(self, txt):
        s = platypus.Spacer(0.1*inch, 0.1*inch)
        p = platypus.Preformatted(txt, PreStyle)
        precomps = [s,p]
        result = platypus.KeepTogether(precomps)
        return result

    def getDefListEls(self, listDict):
        # The Table in ReportLab tends to look better than a list for defining
        #  this stuff.
        data = []
        for spec, value in listDict.iteritems():
            data.append([spec, value])
        t = platypus.Table(data)
        ts = platypus.TableStyle([('FONT', (0, 0), (-1, -1), 'Helvetica', 8)])
        t.setStyle(ts)
        t.hAlign = 'LEFT'
        return [t]

    def getList(self, listTextLines):
        bulletParas = []
        for txt in listTextLines:
            bulletParas.append(platypus.Paragraph(txt, style=BulletStyle,
                bulletText=u"\N{BULLET} "))
        return bulletParas

    def getSimpleDataTableEl(self, headerEntries, dataEntries):
        data = []
        data.append(headerEntries)
        for tableRowData in dataEntries:
            data.append(tableRowData)
        t = platypus.Table(data)
        tStyle = platypus.TableStyle(
            [('BOX', (0,0), (-1,-1), 1, colors.black),
            ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
            ('FONT', (0,0), (-1,0), 'Helvetica-Bold')])
        t.setStyle(tStyle)
        return t

    def getTableEl(self, tableRowEntriesList):
        data = []
        for tableRowData in tableRowEntriesList:
            data.append(tableRowData)
        t = platypus.Table(data)
        ts = platypus.TableStyle([('FONT', (0, 0), (-1, -1), 'Helvetica', 8)])
        t.setStyle(ts)
        return t

    def getPageBreak(self):
        return platypus.PageBreak()

    def getImageEls(self, imgFilename, hdrText=None, width=None, height=None,
            scale=None, tScale=None):
        resultEls = []

        if hdrText is not None:
            resultEls.append(platypus.Paragraph(hdrText,
                style=HeaderStyleList[3]))

        img = PIL.Image.open(imgFilename)
        initWidth, initHeight = img.size
        ratio = initHeight / float(initWidth)
        #imdraw = svg2rlg(imgFilename)
        if tScale is not None:
            tWidth = int(initWidth * tScale/100.0)
            tHeight = int(initHeight * tScale/100.0)
            img.thumbnail((tWidth, tHeight), PIL.Image.ANTIALIAS)
            img.save(imgFilename + ".thumbnail", "PNG")
            imgEl = platypus.Image(imgFilename + ".thumbnail")
        else:
            imgEl = platypus.Image(imgFilename)
        resultEls.append(imgEl)

        if width is not None:
            imgEl.drawWidth = width
            if height is None:
                imgEl.drawHeight = int(width * ratio)
        if height is not None: imgEl.drawHeight = height
        if scale is not None:
            img = PIL.Image.open(imgFilename)
            initWidth, initHeight = img.size
            imgEl.drawWidth = int(initWidth * scale/100.0)
            imgEl.drawHeight = int(initHeight * scale/100.0)
        imgEl.hAlign = 'CENTER'
        return resultEls

    def makeDoc(self, docElements, title, outFilename):
        doc = platypus.SimpleDocTemplate(outFilename, title=title)
        doc.build(docElements)

    def getColorTextStr(self, textStr, colorName):
        return '<font color="%s">%s</font>' % (colorName, textStr)

def generator(basePath):
    """Factory method."""
    return ReportLabGenerator(basePath)
