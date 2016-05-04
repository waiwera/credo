import unittest
from credo.systest import FieldWithinTolTC

class MockModelResult(object):
    def __init__(self, v):
        import numpy as np
        super(MockModelResult, self).__init__()
        self.data = np.zeros(5)
        self.data += v

    def getFieldAtStep(self, field, time_step):
        return self.data

    def getPositions(self):
        return [(0.0, 0.0)] * 5

class TestFieldWithinTolTC(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_fieldWithinTolTC(self):
        res1 = MockModelResult(0.0100001)
        res2 = MockModelResult(0.0102)
        ref = MockModelResult(0.01)

        tc = FieldWithinTolTC(
                              fieldsToTest=['a'],
                              defFieldTol=0.01,
                              fieldTols=None,
                              expected=ref,
                              testTimestep=-1)
        self.assertEqual(True, tc.check(res1))
        self.assertEqual(False, tc.check(res2))


if __name__ == '__main__':
    unittest.main()

