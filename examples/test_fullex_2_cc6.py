"""
A full example testing with AUT2 and Waiwera, CC6, from Adrian/Mike

NOTE:
1. Make sure credo2 is in the PYTHONPATH, eg.
    export PYTHONPATH=$PYTHONPATH:/cygdrive/d/_Geothermal/Apps/credo/credo2/
2. Make sure Waiwera is in the path
    export PATH=$PATH:/home/cyeh015/Waiweras-test/dist/

TODO: check and revive CREDO's ability to do dry run (use results kept on disk)
TODO: check ModelRun.jobParams, which allows options for jobrunner
TODO: create new ModelResult class for loading existing results (or maybe just
use WaiweraResult and T2ModelResult)
"""
from __future__ import print_function

import os

from credo.systest import SciBenchmarkTest
from credo.systest import FieldWithinTolTC

from credo.jobrunner import SimpleJobRunner
from credo.t2model import T2ModelRun, T2ModelResult
from credo.waiwera import WaiweraModelRun

import credo.reporting.standardReports as sReps
from credo.reporting import getGenerators

from mulgrids import mulgrid
import matplotlib.pyplot as plt
import numpy as np

AUT2_FIELDMAP = {
    'Pressure': 'Pressure',
    'Temperature': 'Temperature',
    'Vapour saturation': 'Vapour saturation',
}
WAIWERA_FIELDMAP = {
    'Pressure': 'fluid_pressure',
    'Temperature': 'fluid_temperature',
    'Vapour saturation': 'fluid_vapour_saturation',
}

def t2_to_waiwera(geofilename, datfilename, basepath=None):
    """ convert tough2 model into Waiwera, saves input files and return the
    name of main input file

    TODO: maybe this should be external, and formalised more as utility
    TODO: maybe this should return ordering map, to be used in testing, eg. use
    standard geo.num_atmosphere_blocks to generate a normal one?  but this is
    not always true.
    """
    from mulgrids import mulgrid
    from t2data import t2data
    from os import getcwd, chdir
    from os.path import splitext, basename
    import json

    if basepath is None:
        basepath = getcwd()
    startpath = getcwd()
    if basepath != startpath:
        print("Changing to specified base path '%s'" % (basepath))
        os.chdir(basepath)

    geo = mulgrid(geofilename)
    dat = t2data(datfilename)

    geobase, ext = splitext(basename(geofilename))
    datbase, ext = splitext(basename(datfilename))
    mesh_filename = geobase+'.exo'
    input_filename = datbase + '.json'

    geo.write_exodusii(mesh_filename)
    print('  Mesh file %s created.' % mesh_filename)
    jsondata = dat.json(geo, mesh_filename)
    with open(input_filename, 'w') as jf:
        json.dump(jsondata, jf, indent=2)
        print('  Input file %s created.' % input_filename)

    if basepath != startpath:
        print("Restoring initial path '%s'" % (startpath))
        os.chdir(startpath)

    return input_filename


# ---------------------------------------------------------------------------
# setup models, load files etc.
MODELDIR = 'cc6'
t2geo_fn = "3DCoarsegrid.dat"
t2dat_fn = "CC6C001.DAT"

waiwera_fn = None
# cheated by running in windows and get the files
# waiwera_fn = 'CC6C001.json'  # AY_CYGWIN
if waiwera_fn is None:
    # this does not work in cygwin at the moment (no python vtk)
    waiwera_fn = t2_to_waiwera(t2geo_fn,
                           t2dat_fn,
                           basepath=MODELDIR
                           )
# AUT2 uses dummy block for boundary condition, (atmospheric blocks here)
# get rid of them to be identical to Waiwera
geo = mulgrid(os.path.join(MODELDIR, t2geo_fn))
map_out_atm = range(geo.num_atmosphere_blocks, geo.num_blocks)


# ---------------------------------------------------------------------------
# use AUT2 to work out expected/reference results
mrun_t = T2ModelRun("aut2", t2dat_fn,
                    geo_filename=t2geo_fn,
                    ordering_map=map_out_atm,
                    fieldname_map=AUT2_FIELDMAP,
                    # simulator='AUTOUGH2_5Dbeta',  # AY_CYGWIN
                    basePath=os.path.realpath(MODELDIR)
                    )
jrunner = SimpleJobRunner()
jmeta = jrunner.submitRun(mrun_t)
mres_t = jrunner.blockResult(mrun_t, jmeta)
# can directly load ModelResult instead
# mres_t = T2ModelResult("aut2",
#                        "CC6/CC6C001.LISTING",
#                        geo_filename="CC6/"+t2geo_fn,
#                        ordering_map=map_out_atm,
#                        fieldname_map=AUT2_FIELDMAP)


# ---------------------------------------------------------------------------
# construct Waiwera run and benchamrk test
mrun_s = WaiweraModelRun("waiwera", waiwera_fn,
                       fieldname_map=WAIWERA_FIELDMAP,
                       # simulator='Waiwera.exe',  # AY_CYGWIN
                       basePath=os.path.realpath(MODELDIR)
                       )
mrun_s.jobParams['nproc'] = 6

# TODO: specifying nproc in SciBenchmarkTest does not seem to work, model runs'
# jobParams not updated, so a.t.m. this is only for report
sciBTest = SciBenchmarkTest("CC6", nproc=mrun_s.jobParams['nproc'])
sciBTest.description = """Mike's test problem 6, CC6"""
sciBTest.mSuite.addRun(mrun_s, "Waiwera")

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
# generate plots
atmvals = np.zeros(geo.num_atmosphere_blocks)
y = 125.
slc = [np.array([0., y]), np.array([5000., y])]
names = {
    "pressu": ("Pressure", "Pressure relative error", "bar"),
    "temp": ("Temperature", "Temperature relative error", "$^\circ$C"),
    "vapsat": ("Vapour saturation", "Vapour saturation relative error", ""),
}
for i, tc_name in enumerate(names.keys()):
    field_name, title, unit = names[tc_name]
    var = np.array(sciBTest.testComps[0][tc_name].fieldErrors[field_name])
    var = np.hstack([atmvals, var])
    geo.slice_plot(slc,
                   var,
                   title,
                   unit,
                   plt=plt)
    img_filename = os.path.join(sciBTest.mSuite.runs[0].basePath,
                                sciBTest.mSuite.outputPathBase,
                                ("%i.png" % i))
    plt.savefig(img_filename,
                dpi=None, facecolor='w', edgecolor='w',
                orientation='portrait', papertype=None, format=None,
                transparent=False)
    plt.clf()
    sciBTest.mSuite.analysisImages.append(img_filename)


# ---------------------------------------------------------------------------
# report generation
for rGen in getGenerators(["RST"], sciBTest.outputPathBase):
    sReps.makeSciBenchReport(sciBTest, mResults, rGen,
        os.path.join(sciBTest.outputPathBase,
                     "%s-report.%s" % (sciBTest.testName, rGen.stdExt)))

print("NOTE: use 'rst2html xxx-report.rst > xxx-report.html' to generate html")
