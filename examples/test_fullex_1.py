"""
An full example using SciBenchmarkTest, ModelRun, JobRunner etc together.
"""
import os

from credo.systest import SciBenchmarkTest
from credo.systest import FieldWithinTolTC
from credo.jobrunner import SimpleJobRunner
from credo.t2model import T2ModelRun
# import credo.reporting.standardReports as sReps
# from credo.reporting import getGenerators

import mulgrids

def make_g_dummy(num_blocks, fname):
    bsize = 1000.0 / float(num_blocks - 1)
    geo = mulgrids.mulgrid().rectangular([bsize]*num_blocks, [1.0], [100.0],
        convention=2, atmos_type=2, origin=[0,0,0], justify='l',
        chars=mulgrids.ascii_uppercase)
    geo.rename_layer('A ', 'AA')
    # print geo.block_name_list
    geo.write(fname)

make_g_dummy(41, 'gcoarse_dummy.dat')
# make_g_dummy(201, 'gfine_dummy.dat')

# Avdonin solution
def avdonin_at_radius(pos):
    """ """
    # cheating by using Mike's table, for now
    r = pos[0]
    from avdonin import solution_by_radius
    return solution_by_radius(r)

### use SysTest
sciBTest = SciBenchmarkTest("Avdonin solution")
sciBTest.description = """Mike's test problem 1, Avdonin solution.
Run 0 is coarse model with 25m radial spacing.
"""

sciBTest.mSuite.addRun(
    T2ModelRun("coarse", "coarse.dat",
               geo_filename="gcoarse_dummy.dat",
               basePath=os.path.dirname(os.path.realpath(__file__))),
    "Test problem 1, Avdonin solution, coarse grid")

sciBTest.setupEmptyTestCompsList()
for runI, mRun in enumerate(sciBTest.mSuite.runs):
    sciBTest.addTestComp(runI, "temperature",
        FieldWithinTolTC(fieldsToTest=["Temperature"],
                         defFieldTol=1.0e-5,
                         expected=avdonin_at_radius,
                         testOutputIndex=-1))

jrunner = SimpleJobRunner()
testResult, mResults = sciBTest.runTest(jrunner,
    # postProcFromExisting=True,
    createReports=True)

# for rGen in getGenerators(["RST", "ReportLab"], sciBTest.outputPathBase):
#     sReps.makeSciBenchReport(sciBTest, mResults, rGen,
#         os.path.join(sciBTest.outputPathBase, "%s-report.%s" %\
#             (sciBTest.testName, rGen.stdExt)))
