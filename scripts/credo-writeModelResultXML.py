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

from __future__ import print_function
import sys, getopt
import credo

def main(argv):

    if len(argv) == 0:
        usage()
        sys.exit(2)

    try:
        opts, args = getopt.getopt(argv, "vu", ["verbose", "update"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    modelName=args[0]

    updateMode=False
    for opt, arg in opts:
        if opt in ('-u', '--update'):
            updateMode=True

    walltime=0
    fResults=[]
    #TODO: would be good to get these provided from a static function
    # of credo.modelRun ...
    assigned={'walltime':False}
    optional=['FR']

    for arg in args[1:]:
        try:
            param, val = arg.split('=')
        except ValueError:
            print("CREDO ModelResults XML Writer: Error with provided argument"\
                " '%s', should be in the form param=value\n" % arg)
            sys.exit(2)

        if val == "":
            print("CREDO ModelResults XML Writer: Error with provided argument"\
                " '%s', needs a value provided for the parameter to be"\
                " written\n" % param)
            sys.exit(2)

        if param in assigned:
            assigned[param]=True
            #TODO: could make this bit more maintainable by filling in
            # dictionary directly...
            if param == 'walltime':
                walltime=val
        elif param in optional:
            if param == 'FR':
                fieldName, tol, error = val.split(',')
                fResult = credo.FieldResult(fieldName, float(tol), float(error))
                if updateMode:
                    #Write the value straight away
                    mrFile = credo.defaultModelResultFilename(modelName)
                    credo.updateModelResultsXMLFieldInfo(mrFile, fResult)
                else:
                    fResults.append(fResult)
        else:
            print("CREDO ModelResults XML Writer: Error with provided argument"\
                " '%s', param '%s' is not in known list of model result "\
                " parameters" % (arg,param))
            print("Parameters that need to be assigned are:")
            print(assigned.keys())
            print("Optional parameters are:")
            print(optional)
            sys.exit(2)

    if not updateMode:
        for kw, val in assigned.iteritems():
            if val != True:
                print("CREDO ModelResults XML Writer: Error, necessary"\
                    " parameter '%s' not specified.\n" % kw)
                print("Parameters that need to be assigned are:")
                print(assigned.keys())
                sys.exit(2)

        mRes = credo.ModelResult(modelName, walltime)
        mRes.fieldResults = fResults
        credo.writeModelResultsXML(mRes)

def usage():
    print("Error in command line options passed to the XML writer script\n")

if __name__ == "__main__":
    main(sys.argv[1:])
