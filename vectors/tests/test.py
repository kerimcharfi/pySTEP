import unittest

from vectors import Vec
import numpy as np
import vectors.transformations as tr
import random


class TestCase(unittest.TestCase):
    def test_basics(self):
        # __init__()
        v1 = Vec([1, 0, 0])

        # addition, subtraction

        addition = Vec([1, 2, 7.2]) + Vec([3, 2.1, 1])
        assert (addition - Vec([1, 2, 7.2]) == Vec([3, 2.1, 1]))

        addition = Vec(np.array([1, 2, 7.2])) + Vec(np.array([3, 2.1, 1]))
        assert (addition - Vec([1, 2, 7.2]) == Vec([3, 2.1, 1]))

        # dotproduct

        self.assertAlmostEqual(Vec([1, 0, 0]) * Vec([0, 1, 0]), 0)

        assert (Vec([1, 0, 0]) * 2 == Vec([2, 0, 0]))

        assert (Vec([1, 0, 0]) * (0, 1, 0) == 0)

        # rotate
        assert (np.allclose(
            v1.rotate_around_axis(90 / 360 * 2 * np.pi, (0, 0, 1)),
            (0, 1, 0)))

        # angle

        for i in range(100):
            v1 = Vec([random.random(), random.random(), random.random()])
            rotaxis = v1.cross(Vec([random.random(), random.random(), random.random()])).norm()
            angle = random.random() * np.pi * 2
            v2 = Vec(tr.rotation_matrix(angle, rotaxis.koordinaten).dot(v1.as_4d)).as_3d
            clockwise = v1.clock_wise_angle(v2, rotaxis)
            c_clockwise = v1.counter_clock_wise_angle(v2, rotaxis)
            assert (np.isclose(c_clockwise, angle, atol=0.01))


if __name__ == '__main__':
    unittest.main()
