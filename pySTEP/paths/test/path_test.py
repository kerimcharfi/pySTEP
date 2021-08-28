import unittest
from pySTEP.step_model import Model

import trimesh
import trimesh.intersections
import trimesh.viewer
import trimesh.path.entities
import trimesh.path.curve
import numpy as np
import shapely.geometry.base
import time
import json
from vectors import Vec

from pySTEP.paths.wire_decomposition import *



class MyTestCase(unittest.TestCase):
    def test_discretize_spline(self):
        scene = trimesh.scene.Scene()

        start = time.time()

        # model = Model("abgetrennter_draht.step")
        # model = Model("draht.step")
        # model = Model("single_wire.step")
        # model = Model("2 wires.step")
        # model = Model("component and solids.step")
        # model = Model("step_components_solids.step")
        model = Model("wires.step")

        print(start - time.time())

        wires_dicts = []
        for i, solid in enumerate(model.solids):

            wire = decompose_wire(solid)

            wires_dicts.append(wire)

            #
            # ## Visualize
            for edge in model.solids[0].edges:
                path = trimesh.load_path(edge.discretized)
                scene.add_geometry(path)


            for pl in wire.pop("polylines"):
                scene.add_geometry(trimesh.load_path(pl))

            ## visualize lower Face
            # path = trimesh.load_path([list(cart - translation) for cart in profil.discretized])
            # path.colors = [[255, 0, 0, 255]]
            # scene.add_geometry(path)

            # visualize middle line

            path = trimesh.load_path(wire["mittel_profillinie"])
            path.colors = [[0, 255, 0, 255]]
            scene.add_geometry(path)

            path = trimesh.load_path(wire["rand_profillinie"])
            path.colors = [[255, 0, 0, 255]]
            scene.add_geometry(path)

        ## safe wires.json file
        # print(time.time() - start)
        with open("wires.json", "w") as f:
            f.write(json.dumps(wires_dicts))

        # ## visualize lower Face
        # path = trimesh.load_path([list(cart - translation) for cart in profil.discretized])
        # path.colors = [[255, 0, 0, 255]]
        # scene.add_geometry(path)

        trimesh.viewer.SceneViewer(scene)


if __name__ == '__main__':
    unittest.main()
