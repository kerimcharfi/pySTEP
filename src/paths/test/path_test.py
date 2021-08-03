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

        trimesh.viewer.SceneViewer(scene)

        profil_flachen = []

        for face in model.planefaces:

            for vert in face.vertices:
                for edge in vert.edges:
                    if edge.direction[0].parallel(face.normi):
                        break
                else:
                    break
            else:
                profil_flachen.append(face)


        assert len(profil_flachen) < 3

        lowerplaneface = profil_flachen[0] #check for lower z value

        ## Finde Anfang der PL
        profil_linien = []
        for vert in lowerplaneface:
            for edge in vert.edges:
                if edge not in lowerplaneface.edges:
                    profil_linien.append(edge)

        ## PLs expandieren
        paths = []

        def find_next_segment(pl):
            vert = pl[-1]
            for edge in vert.edges:
                if edge[-1].angle(pl[-1]) < np.deg2rad(5):
                    paths[-1].append(edge)
                    find_next_segment(edge)
                    break


        for pl in profil_linien:
            paths.append([pl])
            find_next_segment(pl)

        ## Profil extrahieren
        profil = lowerplaneface.edgeloops[0]

        ## Zentroid methode




        print(model)


if __name__ == '__main__':
    unittest.main()
