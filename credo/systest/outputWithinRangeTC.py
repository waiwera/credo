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

import inspect
from xml.etree import ElementTree as etree

from .api import SingleRunTestComponent, CREDO_PASS, CREDO_FAIL
from credo.utils import dictAsPrettyStr

class OutputWithinRangeTC(SingleRunTestComponent):
    '''Test component to check that a given output parameter
    (found in the frequent output) is within a given range, and
    optionally also that this occurs within a given set of model times.

    .. seealso:: :mod:`credo.io.stgfreq`.

    .. attribute:: outputName

       The name of the model observable to check, as it's recorded in the
       Frequent Output file. E.g. "Vrms".

    .. attribute:: reductionOp

       The reduction operation to perform in choosing where the value should
       be checked.
       Simple examples using Python built-ins could be:

       * `max() <http://docs.python.org/library/functions.html#max>`_
         - the Maximum value
       * `min() <http://docs.python.org/library/functions.html#min>`_
         - the Minimum value

       .. seealso:: :func:`credo.io.stgfreq.FreqOutput.getReductionOp`

    .. attribute:: allowedRange

       The allowed range for the paramter to fall into for the test to pass.
       A tuple of (min,max) form.

    .. attribute:: tRange

       (Optional) determines if a secondary check should be performed, that
       the parameters value checked (eg max) also fell within a given range
       of model simulation times as a (min,max) tuple. If `None`, this
       secondary check won't be performed.

    .. attribute:: actualVal

       After the check is performed, the actual value of the parameter is
       recorded here.

    .. attribute:: actualTime

       After the check is performed, records the model sim time at which the
       parameters chosen property (eg max or min) occurred.

    .. attribute:: withinRange

       After the check is performed, records a Bool saying whether
       the test component passed.

    .. attribute:: opDict

       (Optional) - will be later passed as keyword arguments to the
       :attr:`.reductionOp` function - so use if the reduction op
       function requires these.
    '''

    def __init__(self, outputName, reductionOp, allowedRange,
            tRange=None, opDict=None):
        SingleRunTestComponent.__init__(self, "outputWithinRange")
        self.outputName = outputName
        self.reductionOp = reductionOp
        self.allowedRange = tuple(allowedRange)
        self.tRange = None if tRange == None else tuple(tRange)
        self.opDict = {} if opDict == None else dict(opDict)
        self.actualVal = None
        self.actualTime = None
        self.withinRange = None

    def _writeXMLCustomSpec(self, specNode):
        etree.SubElement(specNode, 'outputName', value=self.outputName)
        etree.SubElement(specNode, 'reductionOp',
            funcName=str(self.reductionOp.func_name),
            modName=str(inspect.getmodule(self.reductionOp).__name__),
            module=str(inspect.getmodule(self.reductionOp)))
        etree.SubElement(specNode, 'allowedRange-min',
            value=str(self.allowedRange[0]))
        etree.SubElement(specNode, 'allowedRange-max',
            value=str(self.allowedRange[1]))
        if self.tRange is not None:
            etree.SubElement(specNode, 'tRange-min',
                value=str(self.tRange[0]))
            etree.SubElement(specNode, 'tRange-max',
                value=str(self.tRange[1]))
        opDictNode = etree.SubElement(specNode, 'opDict')
        for kw, val in self.opDict.iteritems():
            opItemNode = etree.SubElement(opDictNode, 'opItem')
            opItemNode.attrib['name'] = kw
            opItemNode.text = str(val)

    def attachOps(self, modelRun):
        """Implements base class
        :meth:`credo.systest.api.SingleRunTestComponent.attachOps`.

        .. note:: Currently does nothing. Intend to make it ensure the
           correct plugin is set to be loaded (to make sure observable
           is generated in FrequentOutput.dat)."""
        # TODO: here we have to make sure the correct plugin is set to be
        # loaded .
        # Maybe with the aid of a lookup table of param->plugins?
        #  Or maybe user passes this in when creating the test?
        pass

    def check(self, mResult):
        """Implements base class
        :meth:`credo.systest.api.SingleRunTestComponent.check`."""
        self.actualVal = None
        self.withinRange = None
        statusMsg = ""
        mResult.readFrequentOutput()
        self.actualVal, actualTimeStep = mResult.freqOutput.getReductionOp(
            self.outputName, self.reductionOp, **self.opDict)
        self.actualTime = mResult.freqOutput.getValueAtStep('Time',
            actualTimeStep)
        self.withinRange = (self.allowedRange[0] <= self.actualVal \
            <= self.allowedRange[1])

        statusMsg += "Model output '%s', at reduction op '%s'" % \
            (self.outputName, self.reductionOp.func_name)
        if len(self.opDict) > 0:
            statusMsg += " (%s)" % (dictAsPrettyStr(self.opDict))
        statusMsg += ":\n"
        statusMsg += "\tvalue %g (at time %g)" % \
            (self.actualVal, self.actualTime)
        if not self.withinRange:
            statusMsg += " not within required range (%g,%g)." % \
                self.allowedRange
            overallResult = False
        else:
            statusMsg += " within required range (%g,%g)" % \
                self.allowedRange
            if self.tRange is None:
                statusMsg += "."
                overallResult = True
            else:
                tMin, tMax = self.tRange
                withinTRange = (tMin <= self.actualTime <= tMax)
                if not withinTRange:
                    statusMsg += ", but time at which this"\
                        " occurred (%s) not within req'd range (%g,%g)."\
                        % ((self.actualTime,) + self.tRange)
                    overallResult = False
                else:
                    statusMsg += ", and time at which this"\
                        " occurred (%s) within req'd range (%g,%g)."\
                        % ((self.actualTime,) + self.tRange)
                    overallResult = True
        print statusMsg
        self._setStatus(overallResult, statusMsg)
        return overallResult

    def _writeXMLCustomResult(self, resNode, resultsSet):
        avNode = etree.SubElement(resNode, 'actualValue')
        avNode.text = "%6e" % self.actualVal
        atNode = etree.SubElement(resNode, 'actualTime')
        atNode.text = "%6g" % self.actualTime
        wrNode = etree.SubElement(resNode, 'withinRange')
        wrNode.text = str(self.withinRange)

