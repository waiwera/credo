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

"""A library of useful stats functions for analysis operations.

The aim is for simple functions to be able to run without further dependencies
... with more advanced stats libraries from the likes of SciPy being able to be
loaded at the user's discretion."""
from __future__ import division
from builtins import zip
from builtins import map
from past.utils import old_div

from math import sqrt

def linreg(X, Y):
    """
    Summary
        Linear regression of y = ax + b

    Usage
        real, real, real = linreg(list, list)

    Returns coefficients to the regression line "y=ax+b" from x[] and y[], and R^2 Value

    (Obtained from From
    http://www.answermysearches.com/how-to-do-a-simple-linear-regression-in-python/124/)
    Useful for field analysis, e.g. when applied to a list of length scales
    & field errors, to calculate convergence info, such as
    :func:`credo.analysis.fields.calcFieldCvgWithScale`.
    """
    if len(X) != len(Y):  raise ValueError('unequal length')
    N = len(X)
    Sx = Sy = Sxx = Syy = Sxy = 0.0
    for x, y in zip(X, Y):
        Sx = Sx + x
        Sy = Sy + y
        Sxx = Sxx + x*x
        Syy = Syy + y*y
        Sxy = Sxy + x*y
    det = Sxx * N - Sx * Sx
    a, b = old_div((Sxy * N - Sy * Sx),det), old_div((Sxx * Sy - Sx * Sxy),det)
    meanerror = residual = 0.0
    for x, y in zip(X, Y):
        meanerror = meanerror + (y - old_div(Sy,N))**2
        residual = residual + (y - a * x - b)**2
    RR = 1 - old_div(residual,meanerror)
    #ss = residual / (N-2)
    #Var_a, Var_b = ss * N / det, ss * Sxx / det
    #print "y=ax+b"
    #print "N= %d" % N
    #print "a= %g \\pm t_{%d;\\alpha/2} %g" % (a, N-2, sqrt(Var_a))
    #print "b= %g \\pm t_{%d;\\alpha/2} %g" % (b, N-2, sqrt(Var_b))
    #print "R^2= %g" % RR
    #print "s^2= %g" % ss
    return a, b, RR
