#!/usr/bin/env python
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

import sys, getopt
import credo

import pdb

def main(argv):

    if len(argv) == 0:
        usage()
        sys.exit(2)

    try:
        opts, args = getopt.getopt(argv, "v", ["verbose"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    modelName=args[0]

    inputFiles=[]
    outputPath=""
    nproc=0
    #TODO: would be good to get these provided from a static function
    # of credo.modelRun ...
    assigned={'inputFile':False,'outputPath':False,'nproc':False}
    optional=[]

    for arg in args[1:]:
        try:
            param, val = arg.split('=')
        except ValueError:
            print "CREDO ModelRun XML Writer: Error with provided" \
                " argument '%s', should be in the form param=value\n" % arg
            sys.exit(2)

        if val == "":
            print "CREDO ModelRun XML Writer: Error with provided"\
                " argument '%s', needs a value provided for the"
                " parameter to be written\n" % param
            sys.exit(2)

        if param in assigned:
            assigned[param]=True
            #TODO: could make this bit more maintainable by filling in
            # dictionary directly...
            if param == 'inputFile':
                inputFiles.append(val)
            if param == 'outputPath':
                outputPath=val
            if param == 'nproc':
                nproc=val
        elif param in optional:
            # None currently
            pass
        else:
            print "CREDO ModelRun XML Writer: Error with provided argument '%s',"\
                " param '%s' is not in known list of model result parameters"\
                % (arg,param)
            print "Parameters that need to be assigned are:"
            print assigned.keys()
            print "Optional parameters are:"
            print optional
            sys.exit(2)

    for kw, val in assigned.iteritems():
        if val != True:
            print "CREDO ModelRun XML Writer: Error, necessary parameter"\
                " '%s' not specified.\n" % kw
            print "Parameters that need to be assigned are:"
            print assigned.keys()
            sys.exit(2)

    mRun = credo.ModelRun(modelName, inputFiles, outputPath, nproc)
    mRun.writeModelRunXML()

def usage():
    print "Error in command line options passed to the XML writer script\n"

if __name__ == "__main__":
    main(sys.argv[1:])
