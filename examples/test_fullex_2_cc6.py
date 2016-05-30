"""
A full example testing with AUT2 and Supermodel, CC6, from Adrian/Mike

NOTE:
1. Make sure credo2 is in the PYTHONPATH, eg.
    export PYTHONPATH=$PYTHONPATH:/cygdrive/d/_Geothermal/Apps/credo/credo2/
2. Make sure supermodel is in the path
    export PATH=$PATH:/home/cyeh015/supermodels-test/dist/
"""

import os

from credo.systest import SciBenchmarkTest
from credo.systest import FieldWithinTolTC

from credo.jobrunner import SimpleJobRunner
from credo.t2model import T2ModelRun
from credo.supermodel import SuperModelRun

MODELDIR = 'cc6'

AUT2_FIELDMAP = {
    'Pressure': 'Pressure',
    'Temperature': 'Temperature',
    'Vapour saturation': 'Vapour saturation',
}
SUPER_FIELDMAP = {
    'Pressure': 'fluid_pressure',
    'Temperature': 'fluid_temperature',
    'Vapour saturation': 'fluid_vapour_saturation',
}

def t2_to_super(geofilename, datfilename, basepath=None):
    """ convert tough2 model into supermodel, saves input files and return the
    name of main input file

    TODO: maybe this should be external, and formalised more as utility
    TODO: maybe this should return ordering map, to be used in testing
    """
    from mulgrids import mulgrid
    from t2data_json import t2data_export_json
    from os import getcwd, chdir
    from os.path import splitext, basename
    import json

    if basepath is None:
        basepath = getcwd()
    startpath = getcwd()
    if basepath != startpath:
        print "Changing to specified base path '%s'" % (basepath)
        os.chdir(basepath)

    geo = mulgrid(geofilename)
    dat = t2data_export_json(datfilename)

    geobase, ext = splitext(basename(geofilename))
    datbase, ext = splitext(basename(datfilename))
    mesh_filename = geobase+'.exo'
    input_filename = datbase + '.json'

    geo.write_exodusii(mesh_filename)
    print '  Mesh file %s created.' % mesh_filename
    jsondata = dat.json(geo, mesh_filename)
    with open(input_filename, 'w') as jf:
        json.dump(jsondata, jf, indent=2)
        print '  Input file %s created.' % input_filename

    if basepath != startpath:
        print "Restoring initial path '%s'" % (startpath)
        os.chdir(startpath)

    return input_filename


t2geo_fn = "3DCoarsegrid.dat"
t2dat_fn = "CC6C001.DAT"

# this does not work in cygwin at the moment (no python vtk)
# super_fn = t2_to_super(t2geo_fn,
#                        t2dat_fn,
#                        basepath=MODELDIR
#                        )
# cheated by running in windows and get the files
super_fn = 'CC6C001.json'

# AUT2 uses dummy block for boundary condition, (atmospheric blocks here)
# get rid of them to be identical to supermodel
map_out_atm = range(80,1680)


# ---------------------------------------------------------------------------
# use AUT2 to work out expected/reference results
mrun_t = T2ModelRun("aut2", t2dat_fn,
                    geo_filename=t2geo_fn,
                    ordering_map=map_out_atm,
                    fieldname_map=AUT2_FIELDMAP,
                    simulator='AUTOUGH2_5Dbeta',
                    basePath=os.path.realpath(MODELDIR)
                    )
jrunner = SimpleJobRunner()
jmeta = jrunner.submitRun(mrun_t)
mres_t = jrunner.blockResult(mrun_t, jmeta)


# ---------------------------------------------------------------------------
# construct supermodel run and benchamrk test
mrun_s = SuperModelRun("super", super_fn,
                       fieldname_map=SUPER_FIELDMAP,
                       simulator='supermodel.exe',
                       basePath=os.path.realpath(MODELDIR)
                       )

sciBTest = SciBenchmarkTest("CC6")
sciBTest.description = """Mike's test problem 6, CC6"""
sciBTest.mSuite.addRun(mrun_s, "SuperModel")

sciBTest.setupEmptyTestCompsList()
for runI, mRun in enumerate(sciBTest.mSuite.runs):
    sciBTest.addTestComp(runI, "pressu",
        FieldWithinTolTC(fieldsToTest=["Pressure"],
                         defFieldTol=1.0e-5,
                         expected=mres_t,
                         testOutputIndex=-1))
    sciBTest.addTestComp(runI, "temp",
        FieldWithinTolTC(fieldsToTest=["Temperature"],
                         defFieldTol=1.0e-5,
                         expected=mres_t,
                         testOutputIndex=-1))
    sciBTest.addTestComp(runI, "vapsat",
        FieldWithinTolTC(fieldsToTest=["Vapour saturation"],
                         defFieldTol=1.0e-5,
                         expected=mres_t,
                         testOutputIndex=-1))

jrunner = SimpleJobRunner(mpi=True)
testResult, mResults = sciBTest.runTest(jrunner,
    # postProcFromExisting=True,
    createReports=True)


# ---------------------------------------------------------------------------
# report generation
