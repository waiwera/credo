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

"""A module for general utility functions in CREDO, that don't clearly fit
into other modules."""

import os
import inspect

def getCallingPath(stackNum):
    """Get the path of the calling stack at stackNum levels higher."""
    # We need to add +1 to the stackNum calculation below because
    #  of the getCallingPath() function call itself.
    callingFile = inspect.stack()[stackNum+1][1]
    if callingFile == '<stdin>':
        callingPath = os.getcwd()
    else:
        callingPath = os.path.dirname(callingFile)
    return callingPath

def productCalc(*args, **kwds):
    """Basic implementation of itertools.product from Python 2.6:
    For Python 2.5 backward compatibility.
    productCalc('ABCD', 'xy') --> Ax Ay Bx By Cx Cy Dx Dy
    productCalc(range(2), repeat=3) --> 000 001 010 011 100 101 110 111
    """
    pools = map(tuple, args) * kwds.get('repeat', 1)
    result = [[]]
    for pool in pools:
        result = [x+[y] for x in result for y in pool]
    for prod in result:
        yield tuple(prod)

def dictAsPrettyStr(inDict):
    """A small function to create a string representation of a dictionary,
    by getting the str() of each item in a dict, not
    the repr(). Useful for floating points for example to be 'prettier'
    (less zeros after the number).

    .. note:: No effort has been made to ensure this is super-efficient for
       large dictionaries, it's suited to small lists of parameters"""
    strings = []
    for kw, val in inDict.iteritems():
        strings.append("'%s': %s" % (str(kw), str(val)))
    return "{%s}" % (", ".join(strings))
