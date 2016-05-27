"""
A full example testing with AUT2 and Supermodel, CC6, from Adrian/Mike

NOTE:
1. Make sure credo2 is in the PYTHONPATH, eg.
    export PYTHONPATH=$PYTHONPATH:/cygdrive/d/_Geothermal/Apps/credo/credo2/
2. Make sure supermodel is in the path
    export PATH=$PATH:/home/cyeh015/supermodels-test/dist/
"""

import os

from credo.jobrunner import SimpleJobRunner
from credo.t2model import T2ModelRun
from credo.supermodel import SuperModelRun

MODELDIR = 'cc6'

def t2_to_super(geofilename, datfilename, basepath=None):
    """ convert tough2 model into supermodel, saves input files and return the
    name of main input file

    TODO: add basepath, for specifying where to write input files
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


mrun_t = T2ModelRun("aut2", t2dat_fn,
                    geo_filename=t2geo_fn,
                    simulator='AUTOUGH2_5Dbeta',
                    basePath=os.path.realpath(MODELDIR)
                    )
jrunner = SimpleJobRunner()
jmeta = jrunner.submitRun(mrun_t)
mres_t = jrunner.blockResult(mrun_t, jmeta)

mrun_s = SuperModelRun("super", super_fn,
                       simulator='supermodel.exe',
                       basePath=os.path.realpath(MODELDIR)
                       )
jrunner = SimpleJobRunner(mpi=True)
jmeta = jrunner.submitRun(mrun_s)
mres_s = jrunner.blockResult(mrun_s, jmeta)

