import trimesh
import trimesh.intersections
import trimesh.viewer
import trimesh.path.entities
import trimesh.path.curve
import numpy as np
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

        angle = Vec(connecting_directions[0]).angle(Vec(connecting_directions[1]))
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
        nextedge = expanded_edges[i + 1]
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

    clean_poly = [polyline[0]]
    for i, point in enumerate(polyline[:-1], 1):
        nextpoint = polyline[i]
        if not np.allclose(point, nextpoint):
            clean_poly.append(nextpoint)
        else:
            print("filtered doublicate")

    return clean_poly


def find_profile(solid):
    profil_flachen = []
    normal_edges = []

    for face in solid.plane_faces:
        face_normal_edges = []

        # Für jeden Eckpunkt
        for vert in face.carts:

            if len(vert.edges) > 2:
                # get edge that is not part of the face
                edge = [edge for edge in vert.edges if edge not in face.edges][0]

                # get edge_direction in point
                if edge.discretized[0] == vert:
                    direction = edge.discretized[0] - Vec(edge.discretized[1])
                else:
                    direction = Vec(edge.discretized[-2]) - edge.discretized[-1]

                # check if edge is normal to face
                if Vec(direction).angle(face.normal) < np.deg2rad(10) or Vec(direction).angle(-face.normal) < np.deg2rad(10):
                    face_normal_edges.append(edge)
                else:
                    break

        else:
            profil_flachen.append(face)
            normal_edges.append(face_normal_edges)

    if len(profil_flachen) > 2:
        faces = []

        for face in profil_flachen:
            length = 0
            for edge in face.edges:
                length += edge.length()
            faces.append((face, length))

        faces.sort(key=lambda face: face[1])

        profil_flachen = [faces[0][0], faces[1][0]]
    assert len(profil_flachen) < 3

    return profil_flachen, normal_edges


def find_middle_line(boundary_polyline, intersection_polylines, target_num_segments, first_pml_point):
    pml = []
    extended_polylines = []
    ## verlängerung, sodass schnittpunkte gewährleistet sind
    for polyline in intersection_polylines:
        extended_polylines.append([Vec(polyline[0] - polyline[1]).norm(10) + polyline[0], *polyline, Vec(polyline[-1] - polyline[-2]).norm(10) + polyline[-1]])

    extended_boundary_polyline = [Vec(boundary_polyline[0] - boundary_polyline[1]).norm(10) + boundary_polyline[0], *boundary_polyline,
                                  Vec(boundary_polyline[-1] - boundary_polyline[-2]).norm(10) + boundary_polyline[-1]]
    # ------------------------------------------------------

    # eine der äußeren Profillininen:
    pbl = simplify_line(list(boundary_polyline), target_num_segments)

    for i in range(len(pbl)):
        if i == len(pbl) - 1:
            p1, p2 = pbl[i], pbl[i - 1]
        else:
            p1, p2 = pbl[i], pbl[i + 1]

        intersection_points = []
        for polyline in extended_polylines:
            segments = [[], []]
            for k in range(len(polyline) - 1):
                segments[0].append(polyline[k])
                segments[1].append(polyline[k + 1])

            pts, v = trimesh.intersections.plane_lines(p1, p2 - p1, segments)

            ## nur den schnittpunkt mit der kleinsten entfernung nutzen
            if len(pts) > 0:
                min_dist = np.linalg.norm(pts[0] - p1)
                min_point = pts[0]
                for p in pts:
                    if np.linalg.norm(p - p1) < min_dist:
                        min_point = p
                        min_dist = np.linalg.norm(p - p1)

                intersection_points.append(min_point)
            else:
                print("warning: no intersection found")

        if len(intersection_points) != len(intersection_polylines):
            print("unregelmäßigkeit in anzahl der schnittpunkte")

        intersection_points.append(p1)

        new_pml_point = np.array([0, 0, 0], dtype=float)

        for intersection in intersection_points:
            new_pml_point += intersection * (1 / len(intersection_points))

        pml.append(new_pml_point)

    aligned_pbl = []
    pml = [first_pml_point, *pml[1:]]

    for i in range(len(pml)):
        if i == len(pml) - 1:
            p1, p2 = pml[i], pml[i - 1]
        else:
            p1, p2 = pml[i], pml[i + 1]

        polyline = extended_boundary_polyline

        segments = [[], []]
        for k in range(len(polyline) - 1):
            segments[0].append(polyline[k])
            segments[1].append(polyline[k + 1])

        pts, v = trimesh.intersections.plane_lines(p1, p2 - p1, segments)

        ## nur den schnittpunkt mit der kleinsten entfernung nutzen
        if len(pts) > 0:
            min_dist = np.linalg.norm(pts[0] - p1)
            min_point = pts[0]
            for p in pts:
                if np.linalg.norm(p - p1) < min_dist:
                    min_point = p
                    min_dist = np.linalg.norm(p - p1)

            aligned_pbl.append(min_point)
        else:
            print("warning: no intersection found")

    return pml, aligned_pbl


def simplify_line(polyline, target_num_segments):
    """
    fuse smallest segment with smalles neighbour until target_num_segments is reached

    :param polyline:
    :param target_num_segments:
    :return:
    """

    polyline = np.array(polyline, dtype=float)
    polyline = list(polyline)

    # segments = [(polyline[i] - polyline[i + 1], i, i+1)for i in range(len(polyline) - 1)]
    # segments.sort(key=lambda x: x[0])

    while len(polyline) > target_num_segments:
        smallest_segment = (polyline[0] - polyline[1], 0)
        for i in range(len(polyline) - 1):
            if np.linalg.norm(polyline[i] - polyline[i + 1]) < np.linalg.norm(smallest_segment[0]):
                smallest_segment = (polyline[i] - polyline[i + 1], i)

        index = smallest_segment[1]
        if index == 0:
            polyline.pop(index + 1)
        elif index < len(polyline) - 2 and np.linalg.norm(polyline[index + 1] - polyline[index + 2]) < np.linalg.norm(polyline[index - 1] - polyline[index]):
            polyline.pop(index + 1)
        else:
            polyline.pop(smallest_segment[1])

    return polyline


def decompose_wire(solid):
    # Profilfläche und Startkanten für Polylines
    profil_flachen, pl_seeds = find_profile(solid)

    # untere profilfläche durch z koordinate identifizieren
    if profil_flachen[0].sv.z < profil_flachen[1].sv.z:
        lowerplaneface = profil_flachen[0]
        pl_seeds = pl_seeds[0]
    else:
        lowerplaneface = profil_flachen[1]
        pl_seeds = pl_seeds[1]

    # mittelpunkt des profils durch zentroidmethode
    base_point_pml = np.array([0, 0, 0])
    num_points = len(lowerplaneface.carts)
    for point in lowerplaneface.carts:
        base_point_pml = base_point_pml + point * (1 / num_points)

    # Polylines aus den Kanten aufbauen
    polylines = []
    for pl_seed in pl_seeds:
        polylines.append(expand_path(pl_seed))

    base_point_pbl = polylines[0][0]

    # po
    pml, pbl = find_middle_line(polylines[0], polylines[1:], 15, base_point_pml)

    profil = lowerplaneface.outerbound
    translation = pml[0]

    z = Vec([0, 0, 1])
    x = Vec(base_point_pml) - Vec(base_point_pbl)
    y = z.cross(x).norm()
    base_kos = [x.norm().koordinaten, y.norm().koordinaten, z.norm().koordinaten]

    return {
        "wire_id": solid.bezeichnung.replace('\\', ''),
        "base_pose": [
            (translation / 100).tolist(),
            [0, 0, 0, 1]
        ],
        "base_kos": [list(direction) for direction in base_kos],
        "type": "Wire",
        "seg_lengths": [np.linalg.norm(pml[i] - pml[i + 1]) for i in range(len(pml) - 1)],
        "poly_middle_line": [list(point - translation) for point in pml],
        "orientation_points": [list(point - translation) for point in pbl],
        "profil": {
            "type": "polygon",
            "points": [list(cart - translation) for cart in profil.discretized]
        },
        "polylines":  [[list(point) for point in polyline] for polyline in polylines]
    }
