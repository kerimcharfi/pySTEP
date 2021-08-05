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

def steady_neighbour_edges(edge):
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

def expand_path(seed_edge):
    """
    linie muss hintereinander alle verts wiedergeben
    :param seed_edge:
    :return:
    """
    polyline = []

    expanded_edges = [seed_edge]
    expanding = True

    lastedge = seed_edge
    while expanding:

        nextedges = set(steady_neighbour_edges(lastedge))
        nextedges.difference_update(expanded_edges)

        expanded_edges.extend(nextedges)

        if len(nextedges) == 0:
            expanding = False
        else:
            lastedge = list(nextedges)[0]

    for i, edge in enumerate(expanded_edges[:-1]):
        nextedge = expanded_edges[i+1]
        if edge.discretized[-1] == nextedge.discretized[-1] or edge.discretized[-1] == nextedge.discretized[0]:
            polyline.extend(edge.discretized)
        elif edge.discretized[0] == nextedge.discretized[-1] or edge.discretized[0] == nextedge.discretized[0]:
            polyline.extend(list(reversed(edge.discretized)))
        else:
            raise Exception("non matching discretized")

    if expanded_edges[-1].discretized[0] == polyline[-1]:
        polyline.extend(expanded_edges[-1].discretized)
    elif expanded_edges[-1].discretized[-1] == polyline[-1]:
        polyline.extend(list(reversed(expanded_edges[-1].discretized)))

    return polyline

def find_profile(solid):
    profil_flachen = []
    normal_edges = []

    for face in solid.plane_faces:
        face_normal_edges = []
        for vert in face.carts:
            for edge in vert.edges:
                if edge.discretized[0] == vert:
                    direction = edge.discretized[0] - Vec(edge.discretized[1])
                else:
                    direction = Vec(edge.discretized[-2]) - edge.discretized[-1]
                if Vec(direction).isparallelto(face.normal):
                    face_normal_edges.append(edge)
                    break
            else:
                break
        else:
            profil_flachen.append(face)
            normal_edges.append(face_normal_edges)

    assert len(profil_flachen) < 3

    return profil_flachen, normal_edges

def find_middle_line(polylines):
    pml = []
    pl = list(polylines.pop())
    for i in range(len(pl) - 1):

        p1, p2 = pl[i], pl[i + 1]

        intersection_points = []
        for polyline in polylines:
            segments = [[], []]
            for k in range(len(polyline) - 1):
                segments[0].append(polyline[k])
                segments[1].append(polyline[k + 1])

            p, v = trimesh.intersections.plane_lines(p1, p2 - p1, segments)
            if len(p) > 0:
                intersection_points.append(p[0])

        intersection_points.append(p1)

        new_pml_point = np.array([0, 0, 0], dtype=float)

        for intersection in intersection_points:
            new_pml_point += intersection * (1 / len(intersection_points))

        pml.append(new_pml_point)
    return pml

class MyTestCase(unittest.TestCase):
    def test_discretize_spline(self):
        scene = trimesh.scene.Scene()

        start = time.time()

        model = Model("draht.step")
        # model = Model("component and solids.step")
        # model = Model("step_components_solids.step")

        for edge in model.solids[0].edges:
            path = trimesh.load_path(edge.discretized)
            scene.add_geometry(path)

        profil_flachen, pl_seeds = find_profile(model.solids[0])
        lowerplaneface = profil_flachen[0]
        pl_seeds = pl_seeds[0]

        #splinedges = [236, 237, 245, 249, 253, 257, 260, 261]
        splinedges = [236, 237, 245, 249, 253, 257, 260, 261]

        polylines = []
        for pl_seed in pl_seeds:
            polylines.append(expand_path(pl_seed))

        pml = find_middle_line(polylines)


        for edge in lowerplaneface.edges:
            path = trimesh.load_path(edge.discretized)
            path.colors = [[255,0,0,255]]
            scene.add_geometry(path)



        # print(time.time() - start)
        # with open("polyline.json", "w") as f:
        #     f.write(json.dumps(np.array([pml, pl], dtype=float).tolist()))
        path = trimesh.load_path(pml)
        scene.add_geometry(path)
        trimesh.viewer.SceneViewer(scene)

        #check for lower z value

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
