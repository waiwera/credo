CREDO
=====

CREDO is a toolkit for running, analysing and benchmarking computational models.

CREDO was originally developed to support better benchmarking and profiling
of the Underworld Geophysics modelling application, based on the StGermain
framework. For more on Underworld (and StGermain), see
http://www.underworldcode.org.

For more details about the design of CREDO and how to run it, see the
documentation in the doc sub-directory.

This fork of CREDO was developed at the University of Auckland for
benchmarking the `Waiwera <https://waiwera.github.io/>`_ geothermal
flow simulator.

License and authors
-------------------

CREDO is licensed under the LGPLv2.1, see COPYING.txt.

The main contributors to CREDO's coding, design and development thus far are:

 * Patrick Sunter (patdevelop AT gmail.com)
 * Wendy Sharples
 * Jerico Revote
 * Julian Giordani
 * Owen Kaluza 
 * Louis Moresi
 * Steve Quenette

The Waiwera fork of CREDO was developed by:

 * Angus Yeh
 * Adrian Croucher

Acknowledgements
----------------

We kindly acknowledge the funding support of the Monash University 
Simulation And Modelling (SAM) node by AuScope Limited in facilitating the
development of CREDO.

AuScope is part of the Australian Federal Government's National
Collaborative Research Infrastructure Strategy (NCRIS) program.

Change logs
-----------

For a list of changes that occurred in each release, see the files in the
"changelogs" subdirectory.

Basic Installation instructions
-------------------------------

The Waiwera fork of CREDO can be installed from `PyPI
<https://pypi.org/project/waiwera-credo>`_ using ``pip``, e.g. ``pip
install waiwera-credo`` (or ``pip install --user waiwera-credo`` to
install locally, e.g. if you don't have permissions to install
system-wide Python packages).

The installation instructions for the original CREDO toolkit are below.

(For more detailed
installation instructions, see the "Installation & setup quickstart
instructions" section of the CREDO documentation.)

To run CREDO scripts directly from the command line, you need to set up several
environment variables. These are:

* STG_BASEDIR: the path where your StGermain-based app has been checked out
  and installed to.
* PYTHONPATH: You'll need to update your Python Path to include a reference
  to the directory you installed CREDO into.

In the application bundle CREDO was distributed as part of, there should be
a script you can edit to easily update these variables and then source, such
as "updatePathsCREDO.sh".

After that, you should be good to go!

If you wish to build a local copy of the CREDO documentation, you will need
to first install the 'Sphinx' documentation tool, and the 'Graphviz' plotting
library (for more on these see the doc appendix). Then:
1. cd doc
2. make html
3. make latex; pushd _build/latex; make all-pdf; popd

The documentation will then have been built in the `_build` subdirectory
of `doc`.
