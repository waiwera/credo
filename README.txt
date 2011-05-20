CREDO Readme  
============ 

CREDO is a toolkit for running, analysing and benchmarking computational models:
currently those based on the StGermain framework such as Underworld.

The current CREDO website with links to documentation, release info etc is:
https://www.mcc.monash.edu.au/trac/AuScopeEngineering/wiki/CREDO

(For more info on StGermain and Underworld, see http://www.stgermainproject.org,
and http://www.underworldproject.org).

For more details about the design of CREDO and how to run it, see the
documentation in the "doc" sub-directory.

The CREDO docs are re-generated daily from the repository and placed online at
https://www.mcc.monash.edu.au/credo-doc/ - for a downloadable PDF version, go to
https://www.mcc.monash.edu.au/credo-doc/CREDO.pdf.

License and authors
-------------------

CREDO is licensed under the LGPLv2.1, see COPYING.txt.

The main contributors to CREDO's coding, design and development thus far are:
 * Patrick Sunter (patdevelop@gmail.com)
 * Wendy Sharples (wendy.sharples@monash.edu)
 * Jerico Revote (jerico.revote@monash.edu)
 * Julian Giordani (julian.giordani@monash.edu)
 * Owen Kaluza (owen.kaluza@monash.edu)
 * Louis Moresi (louis.moresi@monash.edu)
 * Steve Quenette (steve.quenette@monash.edu)

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

(For more detailed installation instructions, see the "Installation & setup
quickstart instructions" section of the CREDO documentation.)

Currently, CREDO is designed to be distributed with a StGermain-based
application collection such as stgUnderworld. If you just want to run
system tests via SCons of these applications, you shouldn't need to
perform any additional setup.

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
