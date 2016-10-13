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

"""
This module contains the System Testing functionality of CREDO.

Working at a higher-level than the :mod:`credo.modelrun` and
:mod:`credo.analysis` modules, it is able to use their
capabilities to run system tests of scientific applications,
and communicate and record the results.

From a user perspective, doing an::

  from credo.systest import *

Should allow key functionality to be accessed: e.g. the
:class:`credo.systest.systestrunner.SysTestRunner` class, and standard system
tests such as Analytic, Restart and Reference.

Examples of how to use this module are provided in the CREDO documentation,
see :ref:`credo-examples-systesting`.

.. note:: in early CREDO versions, importing credo.systest would have imported
   into it the entire namespace of the credo.systest.api module. But Python 2.5
   disallows this for relative imports (although the feature was added
   back in in Python 2.6) ... so the import of the credo.systest.api namespace
   into credo.systest was removed, and we only import the 'public interface'
   of implementations designed to be used from the API in testing.

   As a result, if you want to define new :class:`.api.SysTest` or
   :class:`.api.TestComponent` implementations, you should `import
   credo.systest.api` to access the base classes of these.
"""

# NB: Python 2.5 doesn't allow "from .X import *" (import * with relative
#  import syntax). So removed the previous "from .api import *" that was here
#  ... and explicitly importing useful implementation variables
from .api import CREDO_PASS, CREDO_FAIL, CREDO_ERROR

from .systestsuite import SysTestSuite
from .systestrunner import SysTestRunner

# Import all the standard tests so they're available
from .restartTest import RestartTest
from .analyticTest import AnalyticTest
from .analyticMultiResTest import AnalyticMultiResTest
from .referenceTest import ReferenceTest
from .highResReferenceTest import HighResReferenceTest
# Import the benchmark test
from .sciBenchmarkTest import SciBenchmarkTest

# import all test components here too so available for benchmark tests
from .fieldCvgWithScaleTC import FieldCvgWithScaleTC
from .fieldWithinTolTC import FieldWithinTolTC
from .historyWithinTolTC import HistoryWithinTolTC
from .outputWithinRangeTC import OutputWithinRangeTC

# Now import tests/tcs dependent on specific libraries such as PIL
try:
    from .imageReferenceTest import ImageReferenceTest
    from .imageCompTC import ImageCompTC
except ImportError:
    print "Warning, cannot import the ImageReferenceTest for"\
        " use since you don't have required libraries (PIL) installed."
