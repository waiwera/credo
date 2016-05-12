Refactor
========

Notes
-----

### Target classes hierarchy

`ModelRun`, `ModelResult`, `JobRunner`, these can be inherited to form a new set for each simulator.

`TestComponent` forms basic, used by user to add into a `SysTest` (eg. `SciBenchmarkTest`).

`SingleRunTestComponent` and `MultiRunTestComponent` still needed.  Differece is for when a pass/fail criteria needs to know one or multiple results.

I may need new classes to manage the expected values such as `ReferenceResult` and `HighResReferenceResult`.  Along with user defined analytic function, they can be passed into TCs (field or history) as expected values.

### TestComponents

SingleRunTestComponent.attachOps() and MultiRunTestComponent.attachOps() are really just pre-run process applied to ModelRun(s)?  Most of these are not necessary for AUT2/supermodel.

### ModelResult

ModelResult should be responsible for extracting values for comparison.  Some standard ways of geting values should be designed as common interface, as TCs that uses ModelResult does not know/care what kind of Model it is using.

I think I will start with a few methods:
.getFieldAtOutputIndex(field, outputIndex)
.getPositions()

some attributes used by other parts of the CREDO code:
.jobMetaInfo .modelName .outputPath

.writeRecordXML() .readModelResultFromPath()


Refactor TC
-----------

At the moment several TCs (TestComponents) tries to use StGermain-specific FieldComparisonList to operate.  I want to refactor this out, so that these TCs (eg. fieldWithinTolTC etc) can be re-used by different simulators.

Here is the steps that I will be taking:

1. (Cleaning up interfaces) add TODO comments and mark methods to be removed or modified.  Use `# TODO: [Refactor] ...`.
2. Strat with `FieldWithinTolTC` (a sub-class of SingleRunTestComponent).
3. Make a mock ModelRun/ModelResult that can be used with the TC.
4. Maybe write a unit test to drive this and make sure it works.
--- done above ---
5. Copy AUT2 hack codes into places
6. Code up for supermodel

If these works, then remove some dead codes not used by new structure, eg. AnalysisOperations, FieldComparisonList, FieldComparisonOp etc.


Refactor ModelRun/ModelResult/JobRunner
---------------------------------------

As noted in CREDO doc, JobRunner is an abstract base class, user code will need to choose a concrete implementation. It is designed to allow both serial, and parallel non-blocking job submission and reporting.  For example MPI JobRunner can run both TOUGH2MP and Supermodel?

- Should I create a serial JobRunner along with MPI JobRunner?  It seems they are really similar apart from organising the mpiexec -np etc.
- MPIJobRunner gets the command from `ModelRun.getModelRunCommand()`, it's the ModelRun object knows what command to run itself.  MPIJobRunner deals with other things like number of processors etc.
- SysTest uses JobRunner.runSuite().  .runSuite() calls self.submirSuite(), then self.blockSuite() then returns ModelResults.  JobRunner.runModel() is a single ModelRun version of .runSuite(), in term uses .submitRun() and .blockResult() which need to be implemented.

Currently CREDO only has one ModelRun and one ModelResult, both concrete implementations directly.  I want to change this so that both are abstract, which can be inherited by concrete classes such as AUT2ModelRun AUT2ModelResult.  Then add more like for supermodels etc.

This requires to modify the way ModelResult is created.  CREDO creates a ModelResult object directly within JobRunners, which only needs a name and output path.  To make it work for multiple simulators etc, ModelResult should be generated directly by ModelRun, with the help of JobRunner.

*NOTE* I haven't looked at what CREDO does with "dry-runs".  Do they use DRY runs to load previously saved results back in?

- ??? Should I let ModelRun generate ModelResult directly? eg. mResult = mRun.makeResult() ???

*???* I am still not 100% sure if it's best to let ModelRun object to create ModelResult.  This almost implies that it's not JobRunner that generates modelresult.  In a way, a modelresult depends on the modelrun object, BUT it's generated as an product of JobRunner.

### ModelRun

A ModelRun should have the following interfaces:

.basePath .name .outputPath .jobParams .logPath

.getModelRunCommand()
.getStdOutFilename() .getStdErrFilename()

.checkValidRunConfig()
.preRunPreparation()
.postRunCleanup()

### JobRunner

JobRunner is used by SysTest in runTest() etc which requires jrunner to be passed in as an argument.  There are many ways of running tests (multi/single etc) that basically use the same mechanism: 

1. call .submitRun(mrun, ...), which returns jobMI
2. then call .blockResult(mrun, jobMI), which returns mresult

Basically need to implement .submirRun() and .blockResult().  CREDO have two implementations already: MPIJobRunner (for running mpiexec etc directly) and PBSJobRunner (some kind of HPC scheduler).

- These two JobRunners seems to have some repetition codes.  Maybe can refactor out in the future?
- MPIJobRunner seems to be just about what we need as a simple serial runner.

I think I will try refactor the MPI-related parts out from MPIJobRunner:

1. add comments to mark refactoring parts, starting with MPI-related winthin MPIJobRunner.
2. Create test case, use mock ModelRun, ensure the new simple jobrunner works.  This will help clearify the interface of ModelRun.
3. Implement MPI back from new JobRunner class.
4. Finalise ModelRun base class, refactor CREDO's original ModelRun to create abstract ModelRun and concrete AUT2ModelRun.
5. Refactor CREDO's original ModelResult to abstract ModelResult base class and concrete AUT2ModelResult.
6. Create a SciBenchmarkTest example to see if everything fits together, with just one TC (FieldWithinTolTC).
7. See if supercode ModelRun and ModelResult easy to create.
