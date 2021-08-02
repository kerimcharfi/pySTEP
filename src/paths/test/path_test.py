import unittest
from step_model import Model

import trimesh
import trimesh.viewer
import trimesh.path.entities
import trimesh.path.curve

import numpy as np


class MyTestCase(unittest.TestCase):
    def test_discretize_spline(self):
        scene = trimesh.scene.Scene()

        model = Model("draht.step")

        splinedges = [236, 237, 245, 249, 253, 257, 260, 261]
        for spline_id in splinedges:
            line = trimesh.load_path(model.get_entity_by_id(spline_id).discretize())
            scene.add_geometry(line)

#         spline_ids = [22, 23 ,24, 25, 26]
#         for spline_id in spline_ids:
#
#             entity = model.get_entity_by_id(spline_id)
#             degree = 3
#             knots = np.array(entity.parents)
#             control_raw = np.array(entity.data[7], dtype=float)
#             repeats = np.array(entity.data[6], dtype=int)
#             control = []
#             for c, rep in zip(control_raw, repeats):
#                 for i in range(rep):
#                     control.append(c)
#
#             spline = trimesh.path.curve.discretize_bspline(knots, control, 500)
#
#             #trimesh.path.Path3D()
#             line = trimesh.load_path(spline)
#             scene.add_geometry(line)
# #        scene.add_geometry(spline.discrete())
        trimesh.viewer.SceneViewer(scene)

        print(model)


if __name__ == '__main__':
    unittest.main()
