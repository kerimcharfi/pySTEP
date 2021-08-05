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

def expand_path(edge):
    connected_edges, connecting_verts = edge.connected_edges
    extending_edges = []
    for connected_edge, connecting_vert in zip(connected_edges, connecting_verts):
        connecting_segmnents = []
        connecting_directions = []
        if np.allclose(connecting_vert, connected_edge.discretized[0]):
            connecting_segmnents.append([connected_edge.discretized[0], connected_edge.discretized[1]])
            connecting_directions.append(connected_edge.discretized[1] - connected_edge.discretized[0])

        elif np.allclose(connecting_vert, connected_edge.discretized[-1]):
            connecting_segmnents.append([connected_edge.discretized[-1], connected_edge.discretized[-2]])
            connecting_directions.append(connected_edge.discretized[-2] - connected_edge.discretized[-1])

        if np.allclose(connecting_vert, edge.discretized[0]):
            connecting_segmnents.append([edge.discretized[0], edge.discretized[1]])
            connecting_directions.append(edge.discretized[1] - edge.discretized[0])

        elif np.allclose(connecting_vert, edge.discretized[-1]):
            connecting_segmnents.append([edge.discretized[-1], edge.discretized[-2]])
            connecting_directions.append(edge.discretized[-1] - edge.discretized[-2])

        angle =  Vec(connecting_directions[0]).angle(Vec(connecting_directions[1]))
        if angle < 0.2 or angle > np.pi - 0.2:
            extending_edges.append(connected_edge)


    return extending_edges


def find_profile(solid):
    profil_flachen = []
    for face in solid.plane_faces:
        for vert in face.carts:
            for edge in vert.edges:
                if edge.direction[0].parallel(face.normi):
                    break
            else:
                break
        else:
            profil_flachen.append(face)

    assert len(profil_flachen) < 3


class MyTestCase(unittest.TestCase):
    def test_discretize_spline(self):
        scene = trimesh.scene.Scene()

        start = time.time()

        model = Model("draht.step")
        # model = Model("component and solids.step")
        # model = Model("step_components_solids.step")
        splinedges = [236, 237, 245, 249, 253, 257, 260, 261]

        polylines = []
        for spline_id in splinedges:

            e1, e2 = expand_path(model.get_dom_elem_by_id(spline_id).entity)
            path = trimesh.load_path(e1.discretized)
            scene.add_geometry(path)
            path = trimesh.load_path(e2.discretized)
            scene.add_geometry(path)

            polyline = model.get_dom_elem_by_id(spline_id).entity.discretized
            polylines.append(polyline)
            path = trimesh.load_path(polyline)
            scene.add_geometry(path)

        pl = list(polylines.pop())

        pml = []

        for i in range(len(pl)-1):

            p1, p2 = pl[i], pl[i+1]

            intersection_points = []
            for polyline in polylines:
                segments = [[], []]
                for k in range(len(polyline) - 1):
                    segments[0].append(polyline[k])
                    segments[1].append(polyline[k + 1])

                p, v = trimesh.intersections.plane_lines(p1, p2-p1, segments)
                if len(p) > 0:
                    intersection_points.append(p[0])

            intersection_points.append(p1)

            new_pml_point = np.array([0,0,0], dtype=float)

            for intersection in intersection_points:
                new_pml_point += intersection * (1/len(intersection_points))

            pml.append(new_pml_point)

        profil_flachen = find_profile(model.solids[0])


        # print(time.time() - start)
        # with open("polyline.json", "w") as f:
        #     f.write(json.dumps(np.array([pml, pl], dtype=float).tolist()))
        path = trimesh.load_path(pml)
        scene.add_geometry(path)
        trimesh.viewer.SceneViewer(scene)


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
