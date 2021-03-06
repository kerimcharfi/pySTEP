from vectors import Vec
from vectors.primitives import Gerade, Ebene
import numpy as np


class DOMElement:

    # Initializer / Instance Attributes
    def __init__(self, id, name, parent_ids, data, block: str):
        self._parent_ids = parent_ids

        self.name = name
        self.id = int(id)
        self.children = []
        self.parents = []
        self.data = data
        self.block = block

        self.entity = None

    def get_parent_by_name(self, name, mode):
        result = []
        if mode == "entity":
            for parent in self.parents:
                if parent.name == name:
                    result.append(parent)
        if mode == "object":
            for parent in self.parents:
                if parent.name == name:
                    result.append(parent.getobject)

        return result

    def get_children_by_name(self, name, mode):
        result = []
        for child in self.children:
            if child.name == name:
                result.append(child)
        return result

    def __str__(self):
        return "id: " + str(self.id) + " Name: " + str(self.name) + " Parents: " + str(self._parent_ids)

    def __repr__(self):
        return "id: #" + str(self.id) + " Name: " + str(self.name)


class Entity:

    # Initializer / Instance Attributes
    def __init__(self, domelement: DOMElement):
        self.dom_element: DOMElement = domelement
        domelement.entity = self

        self.modelledobject = None
        self.mygroups = []

    @property
    def name(self):
        return self.dom_element.name

    @property
    def id(self):
        return self.dom_element.id

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        return "id: " + str(self.id) + " Name: " + str(self.name) + " Parents: " + str(self.dom_element._parent_ids)

    def __repr__(self):
        return "id: #" + str(self.id) + " Name: " + str(self.name)


class Solid(Entity):
    """
    'CLOSED_SHELL' + 'MANIFOLD_SOLID_BREP'
    """

    def __init__(self, closed_shell_dom):
        Entity.__init__(self, closed_shell_dom)
        self.closed_shell_dom = closed_shell_dom
        self.manifold_solid_brep_dom = closed_shell_dom.children[0]
        self.bezeichnung = self.manifold_solid_brep_dom.data[0][0]

    @property
    def faces(self):
        return [face_dom.entity for face_dom in self.dom_element.parents]

    @property
    def edges(self):
        return list({edge for face in self.faces for edge in face.edges})

    @property
    def plane_faces(self) -> ["PlaneFace"]:
        return [face for face in self.faces if type(face) == PlaneFace]


class Component(Entity):
    """
    'ADVANCED_BREP_SHAPE_REPRESENTATION' -> 'SHAPE_REPRESENTATION_RELATIONSHIP' -> 'SHAPE_REPRESENTATION' (enthaelt in parents 3 koordinatensysteme, darunter auch die richtige trafo ? f??r jeden koeper ein koord? eher 1 grundkoord aud 2koerper koords)
        (groups alle koerper)

    -> UNNAMED('REPRESENTATION_RELATIONSHIP', 'REPRESENTATION_RELATIONSHIP_WITH_TRANSFORMATION', 'SHAPE_REPRESENTATION_RELATIONSHIP') ->  #2558'SHAPE_REPRESENTATION', #2557'SHAPE_REPRESENTATION', #12'ITEM_DEFINED_TRANSFORMATION'
                                                                                                                                                                                                koordinatensystem1 -> koordinatensystem2

     Definition einer Komponente, jedoch keine instanz
    #2806      PRODUCT_DEFINITION                      -> #2795 'PRODUCT_DEFINITION_SHAPE' -> #2792 'SHAPE_DEFINITION_REPRESENTATION' -> #2802 'SHAPE_REPRESENTATION'
                                                        -> 'NEXT_ASSEMBLY_USAGE_OCCURRENCE' (verknupfung zwischen parentcomponent und childcomponent + instanzname)
    """

    def __init__(self, dom_element):
        Entity.__init__(self, dom_element)

        self.bezeichung = dom_element.data[0][0]

        self.solids = None
        self.transformation = None
        self.sub_components = {}
        self.parent_component = None

        self.entitys = []
        self.faces = []
        self.cylinderfaces = []
        self.planefaces = []
        self.edges = []
        self.lines = []
        self.arcedges = []
        self.parents_instances = []
        self.surfacemesh = []

    def __repr__(self):
        return "id: #" + str(self.id) + " COMPONENT: " + str(self.bezeichung)

    def __str__(self):
        return "id: #" + str(self.id) + " COMPONENT: " + str(self.bezeichung)

    def complete__init__(self):
        for face in self.parents_instances:
            if isinstance(face, Face):
                self.faces.append(face)
                for edge in face.edge_instances:
                    if edge not in self.edges:
                        self.edges.append(edge)
                        if isinstance(edge, ArcEdge):
                            self.arcedges.append(edge)
                        if isinstance(edge, Line):
                            self.lines.append(edge)

                if isinstance(face, PlaneFace):
                    self.planefaces.append(face)
                if isinstance(face, CylindricalFace):
                    self.cylinderfaces.append(face)


class CartPoint(Vec, Entity):

    def __init__(self, domelement, coords):
        Entity.__init__(self, domelement)
        Vec.__init__(self, koordinaten=np.array(coords, dtype=float))
        self.faces = []

    def appendface(self, face):
        if face not in self.faces:
            self.faces.append(face)

    def __hash__(self):
        return hash(self.dom_element.id)

    @property
    def edges(self):
        return [child.entity for child in self.dom_element.children if issubclass(type(child.entity), Edge)]


class Axis(Gerade, Entity):

    def __init__(self, domelement):
        Entity.__init__(self, domelement)
        # gerade.__init__(self, entity)


class Edgeloop(Entity):

    def __init__(self, dom_element):
        super().__init__(dom_element)
        self.orientations = []

    @property
    def edges(self):
        return [dom_el.parents[0].entity for dom_el in self.dom_element.parents]

    @property
    def discretized(self):
        edges = self.edges
        discretized = edges[0].discretized

        i = 0
        while len(edges) > 0:
            i += 1
            if i >= len(edges):
                i = 0
            if discretized[-1] == edges[i].carts[0]:
                discretized.extend(edges[i].discretized[1:])
                edges.pop(i)
            elif discretized[-1] == edges[i].carts[1]:
                discretized.extend(reversed(edges[i].discretized[:-1]))
                edges.pop(i)

        clean_poly = [discretized[0]]
        lastpoint = discretized[0]

        for i, point in enumerate(discretized[:-1], 1):
            nextpoint = discretized[i]

            if not np.allclose(point, nextpoint) and np.linalg.norm(nextpoint - lastpoint) > 0.2:
                clean_poly.append(nextpoint)
                lastpoint = nextpoint
            else:
                #print("edgeloop.discretized, filtered doublicate")
                pass

        return clean_poly


class Path:
    "multiple non closed, continous edges"

    def __add__(self, other):
        if self.vertices[0] == other.vertices[0]:
            for vert in other.vertices:
                self.vertices.insert(0, vert)
        elif self.vertices[len(self.vertices)] == other.vertices[0]:
            for vert in other.vertices:
                self.vertices.append(vert)
        elif self.vertices[0] == other.vertices[len(other.vertices)]:
            for vert in other.vertices:
                self.vertices.append(vert)


class Edge(Entity):

    def __init__(self, domelement):

        super().__init__(domelement)

        self.faces = []

        self._discretized: [Vec] = None

        for edge_curv in domelement.children:
            self.faces.append(edge_curv.children[0].children[0].children[0])

    @property
    def carts(self):

        return [self.dom_element.parents[0].entity, self.dom_element.parents[1].entity]

    @property
    def connected_edges(self):
        carts = []
        edges = [edge for cart in self.carts for edge in cart.edges if edge.id != self.id and carts.append(cart) is None]
        return edges, carts

    def __str__(self):
        return str(self.__class__) + " " + str(self.carts)

    @property
    def discretized(self):
        if self._discretized is None:
            verts = self._discretize()

            if abs(self.carts[0] - Vec(verts[0])) > abs(self.carts[1] - Vec(verts[0])):
                verts.reverse()

            verts[0] = self.carts[0]
            verts[-1] = self.carts[1]

            self._discretized = verts

        return self._discretized

    def _discretize(self):
        return self.carts

    def length(self):
        length = 0
        oldvertice = self.discretized[0]
        for vertice in self.discretized[1:]:
            length += np.linalg.norm(oldvertice - vertice)
            oldvertice = vertice
        return round(length, 10)


class ArcEdge(Edge):

    def __init__(self, domelement):
        super().__init__(domelement)
        self.centeraxis_dom = domelement.parents[2].parents[0].parents[1]
        # self.orientation = False
        if ".F." in domelement.data:
            self.orientation = False  # entity is a oriented edge
        else:
            self.orientation = True

        self.radius = float(domelement.parents[2].data[2])
        self.base_dom = domelement.parents[2].parents[0].parents[0]  # circle/axisplacement/cart/data

    def partof(self, line):
        pass

    def _discretize(self, num_points=3):
        if self.orientation:
            startvertex, endevertex = self.carts[0], self.carts[1]
        else:
            startvertex, endevertex = self.carts[1], self.carts[0]

        vektorstart = startvertex - self.base_dom.entity
        vektorende = endevertex - self.base_dom.entity
        v = endevertex - startvertex
        if v == Vec([0, 0, 0]):
            v = vektorstart * (-1)

        halbierendervertex = v.cross(self.centeraxis_dom.entity).norm() * self.radius + self.base_dom.entity
        vviertel1 = halbierendervertex - startvertex
        viertel1vertex = vviertel1.cross(self.centeraxis_dom.entity).norm() * self.radius + self.base_dom.entity
        vviertel3 = endevertex - halbierendervertex
        viertel3vertex = vviertel3.cross(self.centeraxis_dom.entity).norm() * self.radius + self.base_dom.entity

        return self.tesselatesmallarc(self.base_dom.entity, startvertex, viertel1vertex, self.radius, num_points)[1:] \
               + self.tesselatesmallarc(self.base_dom.entity, viertel1vertex, halbierendervertex, self.radius, num_points) \
               + self.tesselatesmallarc(self.base_dom.entity, halbierendervertex, viertel3vertex, self.radius, num_points) \
               + self.tesselatesmallarc(self.base_dom.entity, viertel3vertex, endevertex, self.radius, num_points)

    def tesselatesmallarc(self, base, startvertex, endevertex, radius, resolution):
        edges = []

        vektorstart = startvertex - base
        vektorende = endevertex - base
        dieserpunkt = startvertex
        vertices = [dieserpunkt]
        for i in range(0, resolution + 1):
            gewichteterstart = vektorstart * ((resolution - i) / resolution)
            gewichteterend = vektorende * (i / resolution)
            richtung = gewichteterstart + gewichteterend
            einheitsvektor = richtung * (1 / abs(richtung))
            naechsterpunkt = einheitsvektor * radius + base
            edges.append([dieserpunkt, naechsterpunkt])
            vertices.append(naechsterpunkt)
            dieserpunkt = naechsterpunkt
        return vertices


class EllipseEdge(Edge):

    def __init__(self, domelement):
        super().__init__(domelement)
        self.centeraxis_dom = domelement.parents[2].parents[0].parents[1]
        self.referenceaxis_dom = domelement.parents[2].parents[0].parents[2]

        self.radius1 = float(domelement.parents[2].getData()[0])
        self.radius2 = float(domelement.parents[2].getData()[1])

        self.base_dom = domelement.parents[2].parents[0].parents[0]  # circle/axisplacement/cart/data

        self.orientation = True
        if domelement.getChildren()[0].getData()[0] == "F.":
            self.orientation = False  # entity is a oriented edge
            # startvertex = self.startvertex
            # self.startvertex = self.endevertex
            # self.endevertex = startvertex
        self.centeraxis = Gerade(self.base, self.centeraxis)

        # self.ellipsetesselate(60)
        self.ellipsetesselateelegantly()

    def partof(self, line):
        pass

    def ellipsetesselateelegantly(self):
        resolution = 30
        vektorstart = self.getstartvertex() - self.getbase()
        vektorende = self.getendevertex() - self.getbase()
        vektorenvonderbase = [vektorstart, vektorende]
        mainaxis = self.referenceaxis
        a = self.radius1
        b = self.radius2
        counter = 0
        index = 1
        while (counter < resolution):
            # verbindung = vektorende - vektorstart
            verbindung = vektorenvonderbase[index].norm() - vektorenvonderbase[index - 1].norm()
            winkelhalbierender = verbindung.cross(self.centeraxis.richtung).norm()
            alpha = winkelhalbierender.angle(mainaxis)
            length = math.sqrt((math.cos(alpha) * a) ** 2 + (math.sin(alpha) * b) ** 2)
            neuervektor = winkelhalbierender * length
            if neuervektor != vektorenvonderbase[index] and neuervektor != vektorenvonderbase[index - 1]:
                vektorenvonderbase.insert(index, neuervektor)

                if index == len(vektorenvonderbase) - 2:
                    index = 1
                else:
                    index += 2

            elif index == len(vektorenvonderbase) - 2:
                index = 1

            else:
                index += 1

            counter += 1
        self.vertices = []
        for vert in vektorenvonderbase:
            newvert = vert + self.getbase()
            self.vertices.append(newvert)

    def getvertices(self):
        return self.vertices

    def write_to_3dmsp(self, msp):
        points = [vektorr.getxyz() for vektorr in self.vertices]
        msp.add_polyline3d(points)
        self.centeraxis.draw_to_msp(msp)


import trimesh.path.curve


class SplineEdge(Edge):

    def __init__(self, domelement, controls):
        super().__init__(domelement)
        self.knots_dom = domelement.parents[2].parents
        self.controls = controls

    @property
    def knots(self):
        return [dom_knot.entity for dom_knot in self.knots_dom]

    def _discretize(self, num_points=80):
        return list(trimesh.path.curve.discretize_bspline(self.knots, self.controls, num_points))


class Line(Edge):

    def __init__(self, domelement):
        Edge.__init__(self, domelement)


class Face(Entity):  # advanced face
    def __init__(self, domelement):
        super().__init__(domelement)

        self.connectingedge = None

        self.outerbound_dom = domelement.parents[0].parents[0]  # outboundid
        self.innerbounds_dom = []  # array of edgeloopids
        for innerbound in domelement.parents[1:-1]:
            self.innerbounds_dom.append(innerbound.parents[0])

        self._edges = []
        self._neighbours = []

    @property
    def neighbours(self):
        """
        gives neighbouring faces of this face as tuple (face, connecting_edge)
        :return: [(face, connecting_edge), ]
        """
        if not self._neighbours:
            for edge in self.edges:
                for face in edge.faces:
                    if face != self:
                        self._neighbours.append((face, edge))

        return self._neighbours

    @property
    def edge_loops(self):
        return [self.outerbound, *self.innerbounds]

    @property
    def edges(self):
        return [edge for edgeloop in self.edge_loops for edge in edgeloop.edges]

    @property
    def carts(self):
        return list({cart for edge in self.edges for cart in edge.carts})

    @property
    def outerbound(self):
        return self.outerbound_dom.entity

    @property
    def innerbounds(self):
        return [loop.entity for loop in self.innerbounds_dom]


class PlaneFace(Face, Ebene):
    def __init__(self, domelement):
        Face.__init__(self, domelement)

        self.plane_dom = domelement.parents[-1]

        plane = self.plane_dom.parents[0]
        plane2 = plane.parents
        self.base_dom = plane2[0]

        self.normal_dom = plane2[1]

        Ebene.__init__(self, Vec(np.array(self.base_dom.data[1], dtype=float)), Vec(np.array(self.normal_dom.data[1], dtype=float)))

    @property
    def normal(self):
        return self.normal_dom.entity

    def rotatetoxy(self):
        zaxis = Vec([0, 0, 1])
        nv = self.normal
        angle = (-nv).angle(zaxis)
        rotaxis = nv.cross(zaxis).norm()
        result = []

        for edge in self.edges:
            edgeverts = []
            for vert in edge.vertices:
                edgeverts.append(vert.rotate_copy_around_axis(Gerade(Vec([0, 0, 0]), rotaxis), angle))
            result.append(edgeverts)

        return result


class CylindricalFace(Face):
    def __init__(self, domelement):
        super().__init__(domelement)
        cylinder = domelement.parents[1]  # cylinderform
        self.radius = float(cylinder.data[2])
        self.base = cylinder.parents[0].parents[0]
        mainaxis = cylinder.parents[0].parents[1]
        self.mainaxis = Gerade(self.base, mainaxis)
        self.secondaxis = cylinder.parents[0].parents[2]
        self.faceboundedges = domelement.parents[0].parents[0].parents
        self.areavalue = 0  # to do extract lines,  actually OUTDATED ? difference between getedges of super ?

    def __str__(self):
        return "Cylinderface with radius: " + str(self.radius) + " and base: " + str(self.base) + " and mainaxis: " + str(self.mainaxis)

    def plane_is_tangential(self, plane):
        # Idealerweise sollte das Linesegment genommen werden, welches nah an der Geraden ist.
        # man kann das ideal ??ber die connecting edge ermitteln
        # Im Moment werden das erste und das letzte linesegment des bogens genutzt
        for edge in self.getedges():
            if isinstance(edge, ArcEdge):
                approxi = edge.approximate()
                nearlinesegments = [approxi[1:3], approxi[-3:-1]]
                nearvektor1 = (nearlinesegments[0][0] - nearlinesegments[0][1]).norm()
                nearvektor2 = (nearlinesegments[1][0] - nearlinesegments[1][1]).norm()
                if round(plane.getunitvector() * nearvektor1, 1) == 0 or round(plane.getunitvector() * nearvektor2, 1) == 0:
                    return True

        print(str(plane) + " is not tangetial to: " + str(self))
        return False


class ConeFace(Face):
    def __init__(self, entity, Modelinstance):
        super().__init__(entity, Modelinstance)
        cylinder = self.getParents(1)  # cylinderform
        self.radius = float(cylinder.getData()[0])
        self.base = cylinder.getParents(0).getParents(0)
        mainaxis = cylinder.getParents(0).getParents(1)
        self.mainaxis = Gerade(self.base, mainaxis)
        self.secondaxis = cylinder.getParents(0).getParents(2)
        self.faceboundedges = self.getParents(0).getParents(0).getParents()
        self.areavalue = 0  # to do extract lines,  actually OUTDATED ? difference between getedges of super ?


class Linesegment():
    def __init__(self, start, stop):
        self.start = start
        self.stop = stop
        self.shapelyobject = LineString([self.start, self.stop])
        if len(self.start) == len(self.stop):
            self.dimension = len(self.start)
        else:
            raise Exception("Mixed 2D mit 3D!")
        self.richtung = stop - start

    def intersect(self, otherlinesegment):
        if self.dimension == otherlinesegment.dimension:
            if self.dimension == 2:
                result = self.shapelyobject.intersection(otherlinesegment.shapelyobject)
                if result:
                    return Vektor(result)
                return None
        else:
            raise Exception("Mixed 2D and 3D!")
        return None
