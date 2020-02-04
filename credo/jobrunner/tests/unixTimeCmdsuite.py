from credo.analysis.modelplots as mps

testTimes = ["00:00.1", "02:04.02", "08:09.33", "7:23:06.33", "50:10:45"]

for timeElap in testTimes:
    timeSecs = mps.parseUnixTimeElapsed(timeElap)
    print "%s converted to %f seconds." % (timeElap, timeSecs)


