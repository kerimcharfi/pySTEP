import unittest
from step_model import Model

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

from paths.wire_decomposition import *


class MyTestCase(unittest.TestCase):
    def test_discretize_spline(self):
        scene = trimesh.scene.Scene()

        start = time.time()

        model = Model("abgetrennter_draht.step")
        # model = Model("draht.step")
        # model = Model("2 wires.step")
        # model = Model("component and solids.step")
        # model = Model("step_components_solids.step")
        #model = Model("wires.step")

        print(start - time.time())
        for edge in model.solids[0].edges:
            path = trimesh.load_path(edge.discretized)
            scene.add_geometry(path)
        wires_dicts = []
        for i, solid in enumerate(model.solids):
            profil_flachen, pl_seeds = find_profile(solid)
            lowerplaneface = profil_flachen[0]
            pl_seeds = pl_seeds[0]

            splinedges = [236, 237, 245, 249, 253, 257, 260, 261]

            polylines = []
            for pl_seed in pl_seeds:
                polylines.append(expand_path(pl_seed))

            pml = find_middle_line(polylines)

            ## Profil extrahieren
            profil = lowerplaneface.outerbound
            translation = pml[0]
            pml = simplify_line(pml, 15)
            wires_dicts.append({
                "wire_id": solid.bezeichnung.replace('\\', '') + str(i),
                "base_pose": [
                    (translation / 100).tolist(),
                    [0, 0, 0, 1]
                ],
                "type": "wire",
                "seg_lengths": [np.linalg.norm(pml[i] - pml[i + 1]) for i in range(len(pml) - 1)],
                "mittel_profillinie": [list(point - translation) for point in pml],
                "rand_profillinie": [list(point - translation) for point in simplify_line(polylines[0], 15)],
                "profil": {
                    "type": "polygon",
                    "points": [list(cart - translation) for cart in profil.discretized]
                }
            })

            #
            # ## Visualize
            #
            for pl in polylines:
                scene.add_geometry(trimesh.load_path(pl))

            ## visualize lower Face
            path = trimesh.load_path([list(cart - translation) for cart in profil.discretized])
            path.colors = [[255, 0, 0, 255]]
            scene.add_geometry(path)

            # visualize middle line

            path = trimesh.load_path(pml)
            path.colors = [[0, 255, 0, 255]]
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

        ## Zentroid methode

        print(model)


if __name__ == '__main__':
    unittest.main()
