from vectors.vector import Vec
import numpy as np


def random_orthogonal(vec):
    result = Vec([vec[1], -vec[0], 0])
    if abs(result) == 0:
        Vec([vec[2], 0, -vec[0]])
    if abs(result) == 0:
        Vec([0, vec[2], -vec[1]])

    return result


def angle(self, v2):
    return np.arccos((self * v2) / (abs(self) * abs(v2)))


def clock_wise_angle(self, other, rot_axis):
    v = other.norm() - self.norm()
    if np.allclose(v.koordinaten, 0):
        return 0
    # rot_axis = self.cross(other).norm()
    whr = rot_axis.cross(v)
    return self.angle(whr) + other.angle(whr)


def counter_clock_wise_angle(self, other, rot_axis):
    return 2 * np.pi - self.clock_wise_angle(other, rot_axis)


def is_parallel_to(v1, v2, **kwargs):
    if len(v1) != 3 or len(v2) != 3:
        raise NotImplementedError()

    return np.allclose(np.cross(v1, v2), 0, **kwargs)
