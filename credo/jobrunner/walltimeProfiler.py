import time
from credo.jobrunner.api import PerformanceProfiler

"""A module for saving basic profiling info (just wall time) about ModelRuns
using Python builtin functions.

Is split into basic functions (for use in simple procedural scripts) and the
relevant CREDO declarative :class:`credo.jobrunner.api.PerformanceProfiler`
class for using with :class:`credo.jobrunner.api.JobRunner` s.
"""

class WalltimeProfiler(PerformanceProfiler):
    """
    """
    def __init__(self):
        PerformanceProfiler.__init__(self, "Walltime")

    def setup(self, modelName, modelBasePath, modelOutputPath, jobMetaInfo):
        pass

    def modifyRun(self, modelRun, oldModelRunCommand, jobMetaInfo):
        """ minimum implementation should at least return the original command
        """
        return oldModelRunCommand

    def startTimer(self):
        self._ts = time.time()

    def stopTimer(self):
        self._te = time.time()

    def attachPerformanceInfo(self, jobMetaInfo, modelResult):
        self._elasped_time = self._te - self._ts
        resDict = {
            'walltime': self._elasped_time,
            }
        jobMetaInfo.performance[self.typeStr] = dict(resDict)

