Understanding CREDO
===================

Structure from highest level
----------------------------

### `SysTest`

Highest level object, manages the tests that we want to do, user creates/designs a SysTest and tell it to run tests.  It mainly contains/manages a bunch of `TestComponents` and a single `ModelSuite`.

The general idea is that a SysTest runs models and then applies TCs onto Models.  Overall result of pass/fail will be given, but individual results can be inspected too.

`SciBenchmarkTest` is a empty/openended `SysTest`.  There are also other existing SysTests that are easier to use: `AnalyticMultiResTest`, `AnalyticTest`, `HighResReferenceTest`, `ImageReferenceTest`, `ReferenceTest`, `RestartTest`.

TODO: I want to reuse most of these SysTests, so may need to refactor a lot of StGermain things out.

### `TestComponents`

There are two main (quite different) TCs: `SingleRunTestComponent` and `MultiRunTestComponent`.

SingleRunTC runs on a single model, and gives a pass/fail for the model run.  MultiRunTC need results from a series of model runs, and gives a single pass/fail, eg. convergence test.

There are several existing TCs such as: `fieldCvgWithScaleTC`, `fieldWithinTolTC`, `imageCompTC`, `outputWithinRangeTC`.  I also added a `FieldValWithinRangeTC` while hacking for AUT2.

At the moment these TCs are often reused by the higher level SysTests, so to make these SysTests reusable, these TCs will have to be working for all simulators.  Unfortunately many of these TCs use the `fields.FieldComparisonList` which is designed for StgFEM, along with other related classes `FieldComparisonOp` and `FieldComparisonResult`.

### `ModelSuite`

ModelSuite Runs a suite of `ModelRun`.  It can be used in two ways: Creating `ModelRun` one by one and then add into `ModelSuite`.  And use a single `ModelRun` as template and then add variants to create a suite.

### `ModelRun`

ModelRun is run by `JobRunner` and will produce a `ModelResult` after run.

### `FieldComparisonList`

This is an object of the `AnalysisOperation` which is the core part of CREDO to get some analysis done duing a ModelRun.  The basic design includes interface for writing info, pre-run, and post-run to be implemented.

It wasn't widely used apart from the fields mechanism.

