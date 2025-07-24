import math
import numpy as np

TOL = 1e-8

class Vec(np.ndarray):

    def __init__(self, array_like, *args, **kwargs):
        self.dim = len(array_like)
        super().__init__(self, array_like, *args, **kwargs)

    @property
    def x(self):
        return self[0]

    @property
    def y(self):
        return self[1]

    @property
    def z(self):
        return self[2]

    @property
    def xy(self):
        return [self.x, self.y]

    @property
    def xz(self):
        return [self.x, self.z]

    @property
    def xyz(self):
        return [self.x, self.y, self.z]

    @property
    def length(self):
        return abs(self)

    @property
    def as_4d(self):
        if self.dim == 3:
            return Vec([*self, 1])
        else:
            raise Exception("Only 3d vec should be strechted to 4d")

    @property
    def as_3d(self):
        if self.dim == 4:
            return Vec(self[:-1])
        else:
            raise Exception("Only 4d vec should be trimmed to 3d")

    def __eq__(self, other):
        if len(self) != len(other):
            return False

        for i in range(0, self.dim):
            if not math.isclose(self[i], other[i], rel_tol=TOL):
                return False
        return True

    def __add__(self, other):
        return Vec(self + other)

    def __sub__(self, other):
        return Vec(self - other)

    def __len__(self):
        return self.dim

    def __mul__(self, v2):
        return Vec(self.dot(v2))

    def dot(self, b, out=None):

        return Vec(super().dot(b, out))

    def __str__(self):
        string = "< "
        for i in self:
            string += str(i) + " | "
        string = string[:-2]
        string += " >"
        return string

    def __neg__(self):
        return Vec(self * (-1))

    def __abs__(self):
        summe = 0.0
        for i in self:
            summe = summe + float(i) * float(i)
        betrag = math.sqrt(summe)
        return betrag

    def __round__(self, n=0):
        if n == 0:
            return Vec([int(x) for x in self])
        return Vec(self.round(n))

    def cross(self, v2):
        return Vec(np.cross(self, v2))

    def norm(self, length=1):
        if abs(self) != 0:
            return self * (length / abs(self))
        else:
            return self


XAXIS_2D = Vec([1, 0])
YAXIS_2D = Vec([0, 1])

XAXIS = Vec([1, 0, 0])
YAXIS = Vec([0, 1, 0])
ZAXIS = Vec([0, 0, 1])
