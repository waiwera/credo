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


Steps
-----

At the moment several TCs (TestComponents) tries to use StGermain-specific FieldComparisonList to operate.  I want to refactor this out, so that these TCs (eg. fieldWithinTolTC etc) can be re-used by different simulators.

Here is the steps that I will be taking:

1. (Cleaning up interfaces) add TODO comments and mark methods to be removed or modified.  Use `# TODO: [Refactor] ...`.
2. Strat with `FieldWithinTolTC` (a sub-class of SingleRunTestComponent).
3. Make a mock ModelRun/ModelResult that can be used with the TC.
4. Maybe write a unit test to drive this and make sure it works.
5. Copy AUT2 hack codes into places
6. Code up for supermodel

If these works, then remove some dead codes not used by new structure, eg. AnalysisOperations, FieldComparisonList, FieldComparisonOp etc.

