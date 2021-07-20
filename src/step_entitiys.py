from vectors import Vec
from vectors.primitives import Gerade, Ebene

class Entity:

    # Initializer / Instance Attributes
    def __init__(self, id, name, parentsstring, data, modelinstance):
        self.autoinit = True  # set to false if entity ist artificially created. Blocks calls to linked ids in __init__ of subclasses if set to false
        self.modelinstance = modelinstance
        self.name = name
        self.id = int(id)
        self.parentsstring = parentsstring
        self.children = []
        self.parents = []
        self.modelledobject = None
        self.data = data
        self.mygroups = []

    def appendparent(self, parent):
        self.parents.append(parent)

    def getparentbyname(self, name, mode):
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

    def getchildrenbyname(self, name, mode):
        result = []
        for child in self.children:
            if child.name == name:
                result.append(child)
        return result

    def appendchild(self, child):
        self.children.append(child)

    def __str__(self):
        return "id: " + str(self.id) + " Name: " + str(self.name) + " Parents: " + str(self.parentsstring)

    def getName(self):
        return self.name

    def getID(self):
        return self.id

    def getData(self):
        return self.data

    def getParentsstring(self, stelle=-1):
        if stelle >= 0:
            return self.parentsstring[stelle]
        else:
            return self.parentsstring

    def getChildstring(self, stelle=-1):
        if stelle >= 0:
            return self.parentsstring[stelle]
        else:
            return self.parentsstring

    def getChildren(self):
        children = []
        for childid in self.children:
            children.append(self.modelinstance.get_entity_by_id(childid))
        return children

    def getParents(self, stelle=-1):
        parents = []
        for parentid in self.parents:
            parents.append(self.modelinstance.get_entity_by_id(parentid))
        if stelle >= 0:
            return parents[stelle]
        else:
            return parents


class Component(Entity):


    def __init__(self, id, name, parentsstring, data, modelinstance):
        Entity.__init__(self, id, name, parentsstring, data, modelinstance)

        self.entitys = []
        self.faces = []
        self.cylinderfaces = []
        self.planefaces = []
        self.edges = []
        self.lines = []
        self.arcedges = []
        self.parents_instances = []
        self.surfacemesh = []

    def complete__init__(self):
        self.parents_instances = self.modelinstance.get_entitys_by_ids(self.parents)
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

    def __init__(self, id, name, parentsstring, data, modelinstance):
        Entity.__init__(self, id, name, parentsstring, data, modelinstance)
        Vec.__init__(self, koordinaten=data)
        self.faces = []

    def appendface(self, face):
        if face not in self.faces:
            self.faces.append(face)

    def getfaces(self):
        return self.modelinstance.getEntitysByIDs(self.faces)


class Axis(Gerade, Entity):

    def __init__(self, entity, modelinstance):
        Entity.__init__(self, entity.id, entity.name, entity.parentsstring, entity.data, modelinstance)
        # gerade.__init__(self, entity)


class Edgeloop(Entity):

    def __init__(self, entity, modelinstance):
        super().__init__(entity.id, entity.name, entity.parentsstring, entity.data, modelinstance)
        self.parents = entity.parents
        self.children = entity.children
        self.edges = []  # ids
        for edgecurve in entity.getParents():
            self.edges.append(edgecurve.getParents()[0].id)

    def getedges(self):
        return self.modelinstance.get_entitys_by_ids(self.edges)


class Edge(Entity):

    def __init__(self, entity, modelinstance):

        super().__init__(entity.id, entity.name, entity.parentsstring, entity.data, modelinstance)
        self.parents = entity.parents
        self.children = entity.children
        self.vertices = []  # type:[Vektor]
        self.carts = []  # type:[CartPoint]
        self.faces = []

        if entity.autoinit:
            for edge_curv in entity.getChildren():
                self.faces.append(edge_curv.getChildren()[0].getChildren()[0].getChildren()[0].id)

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

    def __str__(self):
        return str(self.__class__) + " " + str(self.vertices)

    @property
    def approximation(self):
        return self.vertices

    def approximate(self):
        # remove if no consequences
        return self.vertices

    def length(self):
        if self.vertices:
            length = 0
            oldvertice = self.vertices[0]
            for vertice in self.vertices[1:]:
                length += abs(oldvertice - vertice)
                oldvertice = vertice
            return round(length, 10)
        else:
            return 0

    def getfaces(self):
        return self.modelinstance.getEntitysByIDs(self.faces)

    def write_to_2dmsp(self, msp):
        points = [vektorr.getxy() for vektorr in self.vertices]
        msp.add_lwpolyline(points)

    def write_to_3dmsp(self, msp):
        points = [vektorr.getxyz() for vektorr in self.vertices]
        msp.add_polyline3d(points)


class ArcEdge(Edge):

    def __init__(self, entity, modelinstance):
        super().__init__(entity, modelinstance)
        self.centeraxis = entity.getParents(2).getParents(0).getParents(1)
        self.orientation = False
        if entity.getData() == "F":
            self.orientation = True  # entity is a oriented edge
        self.startvertex = entity.getParents(0).getParents(0) # get vector ( of direction and length) orientededge/edgecurve/vertex/cart/data
        self.radius = float(entity.getParents(2).getData()[0])
        self.endevertex = entity.getParents(1).getParents(0)  # get Cart
        self.carts = [entity.getParents(0).getParents(0), entity.getParents(1).getParents(0)]
        self.base = entity.getParents(2).getParents(0).getParents(0)  # circle/axisplacement/cart/data
        self.tesselate(60)

    def partof(self, line):
        pass

    def tesselate(self, resolution):
        vektorstart = self.startvertex - self.base
        vektorende = self.endevertex - self.base
        v = self.endevertex - self.startvertex
        if v == Vec([0, 0, 0]):
            v = vektorstart * (-1)
        halbierendervertex = v.cross(self.centeraxis).norm() * self.radius + self.base
        vviertel1 = halbierendervertex - self.startvertex
        viertel1vertex = vviertel1.cross(self.centeraxis).norm() * self.radius + self.base
        vviertel3 = self.endevertex - halbierendervertex
        viertel3vertex = vviertel3.cross(self.centeraxis).norm() * self.radius + self.base
        self.vertices = self.tesselatesmallarc(self.base, self.startvertex, viertel1vertex, self.radius, resolution) \
                        + self.tesselatesmallarc(self.base, viertel1vertex, halbierendervertex, self.radius, resolution) \
                        + self.tesselatesmallarc(self.base, halbierendervertex, viertel3vertex, self.radius, resolution) \
                        + self.tesselatesmallarc(self.base, viertel3vertex, self.endevertex, self.radius, resolution)

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

    def getvertices(self):
        return self.vertices

    def print(self):
        print(self.start + self.ende)


class EllipseEdge(Edge):

    def __init__(self, entity, modelinstance):
        super().__init__(entity, modelinstance)
        self.centeraxis = entity.getParents(2).getParents(0).getParents(1)
        self.referenceaxis = entity.getParents(2).getParents(0).getParents(2)

        self.startvertex = entity.getParents(0).getParents(0).id  # get vector ( of direction and length) orientededge/edgecurve/vertex/cart/data
        self.radius1 = float(entity.getParents(2).getData()[0])
        self.radius2 = float(entity.getParents(2).getData()[1])
        self.endevertex = entity.getParents(1).getParents(0).id  # get Cart
        self.carts = [entity.getParents(0).getParents(0), entity.getParents(1).getParents(0)]
        self.base = entity.getParents(2).getParents(0).getParents(0).id  # circle/axisplacement/cart/data

        self.orientation = True
        if entity.getChildren()[0].getData()[0] == "F.":
            self.orientation = False  # entity is a oriented edge
            # startvertex = self.startvertex
            # self.startvertex = self.endevertex
            # self.endevertex = startvertex
        self.centeraxis = Gerade(self.getbase(), self.centeraxis)

        # self.ellipsetesselate(60)
        self.ellipsetesselateelegantly()

    def getcenteraxis(self):
        return self.modelinstance.getEntityByID(self.centeraxis)

    def getstartvertex(self):
        return self.modelinstance.getEntityByID(self.startvertex)

    def getendevertex(self):
        return self.modelinstance.getEntityByID(self.endevertex)

    def getbase(self):
        return self.modelinstance.getEntityByID(self.base)

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


class Line(Edge, Gerade):

    def __init__(self, entity, modelinstance):
        Edge.__init__(self, entity, modelinstance)

        self.floatlength = 0

        if entity.autoinit:
            for vertex in entity.getParents()[:-1]:
                self.vertices.append(vertex.getParents()[0])

            if len(self.vertices) == 2:
                self.richtung = self.vertices[1] - self.vertices[0]
                self.floatlength = abs(self.richtung)
                Gerade.__init__(self, stutze=self.vertices[0], richtung=self.richtung)

        self.carts = self.vertices

    def equals(self, line):
        None

    def partof(self, line):
        None

    def getdirection(self):
        return self.direction

    def getbase(self):
        return self.base

    def getstart(self):
        None

    def getvertices(self):
        pass

    def write_to_2dmsp(self, msp):
        msp.add_line(self.carts[0].getxy(), self.carts[1].getxy())

    def tesselate(self, resolution, mode):
        return self.getvertices()

    def __str__(self):
        return "LINE" + str(self.vertices[0]) + str(self.vertices[1])


class Face(Entity):  # advanced face
    def __init__(self, entity: Entity, Modelinstance):
        super().__init__(entity.id, entity.name, entity.parentsstring, entity.data, Modelinstance)

        self.connectingedge = None
        self.parents = entity.parents
        self.children = entity.children
        self.outerbound = Modelinstance.override_entity(Edgeloop(self.getParents()[0].getParents()[0], Modelinstance))  # outboundid
        self.innerbounds = []  # array of edgeloopids
        for innerbound in self.getParents()[1:-1]:
            innerboundid = Modelinstance.overrideentity(Edgeloop(innerbound.getParents()[0], Modelinstance))
            self.innerbounds.append(innerboundid)
        self.edges = []
        self.edge_instances = []
        self.neighbours = []
        self.connectingedges = []

        self.component = Modelinstance.get_entity_by_id(self.children[0])  # type:Component

        outerbound = self.getouterbound()

        for edge in outerbound.getedges():

            self.edges.append(edge.id)  ##serving dif context
            self.edge_instances.append(edge)
            for cart in edge.carts:
                cart.appendface(self)

            for faceid in edge.faces:
                if not faceid == self.id:
                    self.neighbours.append(faceid)
                    self.connectingedges.append(edge.id)

        for edgeloop in self.getinnerbounds():
            for edge in edgeloop.getedges():

                self.edges.append(edge.id)
                self.edge_instances.append(edge)
                for cart in edge.carts:
                    cart.appendface(self)
                for faceid in edge.faces:
                    if not faceid == self.id:
                        self.neighbours.append(faceid)



    def getneighbours(self):
        neighbours = self.modelinstance.getEntitysByIDs(self.neighbours)
        connectingedges = self.modelinstance.getEntitysByIDs(self.connectingedges)
        for neighbour, connectingedge in zip(neighbours, connectingedges):
            neighbour.connectingedge = connectingedge
        return neighbours

    def getedges(self):
        return self.modelinstance.get_entitys_by_ids(self.edges)

    def getouterbound(self):
        return self.modelinstance.get_entity_by_id(self.outerbound)

    def getinnerbounds(self):
        return self.modelinstance.get_entitys_by_ids(self.innerbounds)

    def area(self):
        pass


class PlaneFace(Face, Ebene):
    def __init__(self, entity, Modelinstance):
        Face.__init__(self, entity, Modelinstance)

        self.plane = self.getParents()[len(self.parents) - 1].id

        plane = self.getplane().getParents()[0]
        plane2 = plane.getParents()
        self.base = plane2[0].id
        normalenvektor = plane2[1]
        self.normalenvektor = normalenvektor.id
        self.nv_instance = normalenvektor

        Ebene.__init__(self, self.getBase(), self.nv_instance)

    def __str__(self):
        return "planeface: " + str(self.plane)

    def getplane(self):
        return self.modelinstance.get_entity_by_id(self.plane)

    def getBase(self):
        return self.modelinstance.get_entity_by_id(self.base)

    def getunitvector(self):
        return self.modelinstance.get_entity_by_id(self.normalenvektor)

    def tesselate(self, mode):
        if mode == "vertex":
            vertices = []
            for edgeloop in self.edgeloops:
                for edge in edgeloop:
                    vertices.append(edge.tesselate(20, mode))
            return vertices
        if mode == "polygon":
            vertices = []
            for edgeloop in self.edgeloops:
                subvertices = []
                for edge in edgeloop:
                    subvertices.append(edge.tesselate(20, "vertex"))
                vertices.append(subvertices)
                del subvertices
            return vertices
        else:
            return None

    def paralleltoplane(self, plane):
        pass

    def rotatetoxy(self):
        zaxis = Vektor([0, 0, 1])
        nv = self.nv_instance
        angle = (-nv).angle(zaxis)
        rotaxis = nv.cross(zaxis).norm()
        result = []

        for edge in self.edge_instances:
            edgeverts = []
            for vert in edge.vertices:
                edgeverts.append(vert.rotate_copy_around_axis(Gerade(Vektor([0, 0, 0]), rotaxis), angle))
            result.append(edgeverts)

        return result

    def write_to_3dmsp(self, msp):
        msp.add_polyline3d([self.getBase().getxyz(), (self.getBase() + self.nv_instance.norm(15)).getxyz()])
        msp.add_circle((self.getBase() + self.nv_instance.norm(15)).getxyz(), 1)
        msp.add_text(str(self.plane)).set_pos(self.getBase().getxyz())


class CylindricalFace(Face):
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

    def __str__(self):
        return "Cylinderface with radius: " + str(self.radius) + " and base: " + str(self.base) + " and mainaxis: " + str(self.mainaxis)

    def plane_is_tangential(self, plane):
        # Idealerweise sollte das Linesegment genommen werden, welches nah an der Geraden ist.
        # man kann das ideal über die connecting edge ermitteln
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

    @property
    def area(self):
        if self.area == 0:
            self.triangulate()
        else:
            return self.areavalue

    def triangulate(self):
        RESOLUTION = 72

        def project_to_xy(vert):
            verbindung = self.base - vert
            y_koordinate = verbindung * self.mainaxis.richtung.norm()
            y_vektor = y_koordinate * self.mainaxis.richtung.norm()
            r_vektor = verbindung - y_vektor
            winkel = self.secondaxis.richtung.angle(r_vektor)
            x_koordinate = winkel * self.radius
            projeziert_vektor = Vektor(x=x_koordinate, y=y_koordinate)
            projeziert_vektor.original = vert
            return projeziert_vektor

        def project_back(vert):
            if vert.original:
                return vert.original
            x = vert.x
            winkel = x / self.radius
            y = vert.y
            return self.base + y * self.mainaxis.richtung.norm() + self.secondaxis.richtung.norm().rotate_copy_around_axis(
                Gerade(Vektor([0, 0, 0]), self.mainaxis.richtung),
                winkel
            )

        # projeziere alle Linien auf xy Ebene

        projezierteverts = [project_to_xy(vert) for vert in self.vertices]

        # Trianguliere das Projezierte Bild

        projectedtriangles = []

        # Teile die projezierten Dreiecke um die Zylinderform zu erhalten

        for i in range(RESOLUTION):
            phi = i / 2 * math.pi
            x = phi * self.radius
            splitterline = Linesegment(Vektor(x, -10000), Vektor(x, 10000))

            for triangle in projectedtriangles:
                triangle.split(splitterline)

        # move to triangle object
        class Triangle:
            def __init__(self, point1, point2, point3):

                self.points = [point1, point2, point3]
                self.linesegments = [Linesegment(point1, point2), Linesegment(point2, point3), Linesegment(point3, point1)]

            def split(self, splitterline):

                intersections = []
                polygon = []
                for linesegment in self.linesegments:
                    polygon.extend(linesegment.start)
                    intersection = linesegment.intersect(splitterline)
                    if intersection:
                        polygon.extend(intersection)

                # triangles = earcut.earcut(polygon)
                triangles = [(polygon[index * 2], polygon[index * 2 + 1]) for index in earcut.earcut(polygon)]
                return triangles

                ## Fallunterscheidung:
                # 1. splitter trifft nur einen Punkt
                # 2. splitter liegt auf einem Liniensegment
                # 3. splitter trifft einen Punkt und schneidet eine Linie
                # 4. splitter schneidet zwei Linien

        # Tranformation zurück

        mesh = [project_back(vert) for vert in projectedtriangles]

        self.areavalue = 0
        self.mesh = mesh


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

    def triangulate(self):
        projeziert = []

        def project_to_xy(vert):
            verbindung = self.base - vert
            y_koordinate = verbindung * self.mainaxis.richtung.norm()
            y_vektor = y_koordinate * self.mainaxis.richtung.norm()
            r_vektor = verbindung - y_vektor
            winkel = self.secondaxis.richtung.angle(r_vektor)
            x_koordinate = winkel * self.radius
            projeziert.append(Vektor(x=x_koordinate, y=y_koordinate))

        for vert in self.vertices:
            project_to_xy(vert)


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
