
import os
import uwa
from uwa import modelrun as mrun
from uwa import modelresult as mres

class ModelSuite:
    '''A class for running a suite of Models (e.g. a group for profiling,
    or a System Test that requires multiple runs)'''

    def __init__(self, outputPathBase):
        self.runs = []
        self.runDescrips = []
        self.outputPathBase = outputPathBase

    def addRun(self, modelRun, runDescrip=None):
        if not isinstance( modelRun, mrun.ModelRun ):
            raise TypeError("Error, given run not an instance of a"\
                " ModelRun" % runI)
        self.runs.append(modelRun)
        self.runDescrips.append(runDescrip)

    def runAll(self):
        '''Run each modelRun in the suite'''
        # NB: may want to pass in a jobRunner argument, to do the run

        resultsList=[]

        print "Running the %d modelRuns specified in the suite" % len(self.runs)
        for runI, modelRun in enumerate(self.runs):
            if not isinstance(modelRun, mrun.ModelRun):
                raise TypeError("Error, stored run %d not an instance of a"\
                    " ModelRun" % runI)
            print "Doing run %d, of name '%s', with description '%s'"\
                % (runI, modelRun.name, self.runDescrips[runI])
            print "Generating analysis XML:"
            modelRun.analysisXMLGen()
            print "Running the Model:"
            result = mrun.runModel(modelRun)
            assert isinstance( result, mres.ModelResult )
            # TODO: does this step need to be refactored/generalised?
            # I.E. into a "post-run cleanup" for all analysis ?
            print "Doing post-run tidyup:"
            uwa.moveConvergenceResults(os.getcwd(), modelRun.outputPath)
            resultsList.append(result)

        return resultsList    
    
    # TODO: here would be where we have tools to generate stats/plots
    # of various properties of the suite, e.g. memory usage