import re
from src.step_entitiys import *
import pathlib
import typing

DEBUG = False


class Model:

    def __init__(self, file_path: typing.Union[str, pathlib.Path] = None, document: str = ""):

        if document == "" and file_path is None:
            raise Exception("No step file provided")

        if document == "":
            with open(file_path) as f:
                document = f.read()

        self.file_path = file_path

        self.components = []
        self.entitys = []

        self.idcounter = 0
        blocks = re.findall(r'([\S\s]+?);', document)
        data_section = False

        for b in blocks:

            if not data_section and "DATA" in b:
                data_section = True

            if data_section:

                # data = re.findall('(\-*\w+\.\d*\w*\-*\+*\d*)', b)  ##Changed to get T. and F.
                #  data = re.findall('(\-*\d+\.\d*\w*\-*\+*\d*)', b)  ##worked perfect for numbers
                bracket_stack = []
                container_stack = [[]]
                stream = ''

                for char in b:
                    if "(" == char or (char == "'" and bracket_stack[-1]!="'"):
                        if stream:
                            container_stack[-1].append(stream)
                            stream = ''
                        bracket_stack.append(char)
                        newcontainer = []
                        container_stack[-1].append(newcontainer)
                        container_stack.append(newcontainer)

                    elif ")" == char and bracket_stack[-1] == "(" or (char == "'" and bracket_stack[-1]=="'"):
                        if stream:
                            container_stack[-1].append(stream)
                            stream = ''
                        container_stack.pop()
                        bracket_stack.pop()

                    elif "," == char:
                        if stream:
                            container_stack[-1].append(stream)
                            stream = ''

                    else:
                        stream += char

                else:
                    if stream:
                        container_stack[-1].append(stream)


                id_and_name_block = container_stack[0][0]
                data = container_stack[0][-1]

                ids = re.findall('#(\d+)', b)
                if len(ids) > 1:
                    id = int(ids.pop(0))
                    parents = ids
                    name = re.findall(r'=(\w+)|$', id_and_name_block)[0]
                    if id > self.idcounter:
                        self.idcounter = id
                    # re.search(r'=(\w+)', line)
                    if name == "CARTESIAN_POINT":
                        self.entitys.append(CartPoint(id, name, parents, data, self))
                    elif name == "DIRECTION":
                        self.entitys.append(CartPoint(id, name, parents, data, self))
                    elif name == "CLOSED_SHELL":
                        component = Component(id, name, parents, data, self)
                        self.entitys.append(component)
                        self.components.append(component)
                    else:
                        self.entitys.append(Entity(id, name, parents, data, self))

                elif len(ids) > 0:
                    id = int(ids.pop(0))
                    parents = ['NONE']
                    name = re.findall(r'=(\w+)|$', b)[0]
                    if name == "CARTESIAN_POINT":
                        coords = data[1]
                        self.entitys.append(CartPoint(id, name, parents, coords, self))
                    elif name == "DIRECTION":
                        coords = data[1]
                        self.entitys.append(CartPoint(id, name, parents, coords, self))
                    elif name == "CLOSED_SHELL":
                        component = Component(id, name, parents, data, self)
                        self.entitys.append(component)
                        self.components.append(component)
                    else:
                        self.entitys.append(Entity(id, name, parents, data, self))
                if len(self.entitys) > 0:
                    self.entitys[len(self.entitys) - 1].block = b

        self.idoffset = int(self.entitys[0].id)

        for e in self.entitys:
            for pidstring in e.parentsstring:
                if pidstring != "NONE":
                    e.parents.append(self.get_entity_by_id(int(pidstring)))
                    self.get_entity_by_id(int(pidstring)).children.append(e)

        for i in range(0, len(self.entitys)):

            if self.entitys[i].name == "ADVANCED_FACE":
                if self.entitys[i].parents[len(self.entitys[i].parents) - 1].name == "PLANE":
                    self.entitys[i] = PlaneFace(self.entitys[i], self)

                elif self.entitys[i].parents[len(self.entitys[i].parents) - 1].name == "CYLINDRICAL_SURFACE":
                    self.entitys[i] = CylindricalFace(self.entitys[i], self)
                    # self.entitys[i].component.cylindersfaces.append(self.entitys[i]) Not sure if this should be here or in Component.complete__init__()

            elif self.entitys[i].name == "EDGE_CURVE" and self.entitys[i].parents[2].name == "LINE":

                self.entitys[i] = Line(self.entitys[i], self)

            elif self.entitys[i].name == "EDGE_CURVE" and self.entitys[i].parents[2].name == "CIRCLE":

                self.entitys[i] = ArcEdge(self.entitys[i], self)

            elif self.entitys[i].name == "EDGE_CURVE" and self.entitys[i].parents[2].name == "ELLIPSE":

                self.entitys[i] = EllipseEdge(self.entitys[i], self)

            elif self.entitys[i].name == "EDGE_CURVE" and self.entitys[i].parents[2].name == "B_SPLINE_CURVE_WITH_KNOTS":
                entity = self.entitys[i].parents[2]

                control_raw = np.array(entity.data[7], dtype=float)
                repeats = np.array(entity.data[6], dtype=int)
                control = []
                for c, rep in zip(control_raw, repeats):
                    for xxxx in range(rep):
                        control.append(c)

                self.entitys[i] = SplineEdge( self.entitys[i], self, control)

            elif self.entitys[i].name == "EDGE_CURVE" and self.entitys[i].parents[2].name == "":
                data = self.entitys[i].parents[2].data
                if data[2].strip() == "B_SPLINE_CURVE":
                    control_raw = np.array(data[5][1], dtype=float)
                    repeats = np.array(data[5][0], dtype=int)
                    control = []
                    for c, rep in zip(control_raw, repeats):
                        for xxxx in range(rep):
                            control.append(c)
                    self.entitys[i] = SplineEdge( self.entitys[i], self, control)

            elif self.entitys[i].name == "VECTOR":
                coords = (Vec(self.entitys[i].parents[0].koordinaten) * float(self.entitys[i].data[2])).koordinaten
                self.entitys[i] = CartPoint(self.entitys[i].id, self.entitys[i].name, self.entitys[i].parentsstring,
                                            coords, self)

            elif self.entitys[i].name== "VERTEX_POINT":
                self.entitys[i].parents[0].children.append(self.entitys[i].children)



        for component in self.components:
            component.complete__init__()

        print("Model loaded")

    def get_entity_by_id(self, entity_id):
        if entity_id - int(self.entitys[0].id) < len(self.entitys):
            return self.entitys[entity_id - self.idoffset]
        else:
            return None

    def get_entitys_by_ids(self, entiids):
        entitys = []
        for entiid in entiids:
            entitys.append(self.entitys[entiid - self.idoffset])
        return entitys

    def override_entity(self, entity):
        self.entitys[entity.id - self.idoffset] = entity
        return entity.id

    def get_new_id(self):
        self.idcounter += 1
        return self.idcounter

    def add_entity(self, entity, component):
        entity.id = self.get_new_id()
        self.entitys.append(entity)
        if isinstance(entity, Edge):
            print("new edge created")
            component.edges.append(entity)

    def get_entitys_by_name(self, name):
        namelist = []
        for e in self.entitys:
            if str(name) == str(e.getName()):
                namelist.append(e)
        return namelist

    def save(self):
        raise Exception("save is not implemented yet")
        pass
