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
        self.solids = []
        self.entitys = []
        self.DOM = []

        self.idcounter = 0

        # blocks = re.findall(r'([\S\s]+?);', document)
        blocks = document.replace('\n', '').split(";")
        data_section = False

        # parse text and create DOM elements

        for b in blocks:

            if not data_section and "DATA" in b:
                data_section = True

            if data_section:

                # data = re.findall('(\-*\w+\.\d*\w*\-*\+*\d*)', b)  ##Changed to get T. and F.
                # data = re.findall('(\-*\d+\.\d*\w*\-*\+*\d*)', b)  ##worked perfect for numbers
                bracket_stack = []
                container_stack = [[]]
                stream = ''
                current_stream_is_string = False

                for char in b:
                    if "(" == char or (char == "'" and bracket_stack[-1] != "'"):
                        if stream:
                            container_stack[-1].append(stream)
                            stream = ''
                        bracket_stack.append(char)
                        newcontainer = []
                        container_stack[-1].append(newcontainer)
                        container_stack.append(newcontainer)

                    elif ")" == char and bracket_stack[-1] == "(" or (char == "'" and bracket_stack[-1] == "'"):
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
                        if char not in ["\n"]:
                            stream += char

                else:
                    if stream:
                        container_stack[-1].append(stream)

                all_ids_in_b = re.findall('#(\d+)', b)

                if all_ids_in_b:
                    id_and_name_block = container_stack[0][0]
                    data = container_stack[0][-1]
                    id = int(all_ids_in_b.pop(0))
                    parent_ids = [int(id_str) for id_str in all_ids_in_b]
                    name = re.findall(r'=(\w+)|$', id_and_name_block)[0]

                    self.DOM.append(DOMElement(id, name, parent_ids, data, b))


        ### link DOM elements
        self.idoffset = int(self.DOM[0].id)

        for domelement in self.DOM:
            for parent_id in domelement._parent_ids:
                domelement.parents.append(self.get_dom_elem_by_id(parent_id))
                self.get_dom_elem_by_id(parent_id).children.append(domelement)

        assembly_connections = []
        ### create entities
        for domelement in self.DOM:

            if domelement.name == "CARTESIAN_POINT":
                coords = domelement.data[1]
                self.entitys.append(CartPoint(domelement, coords))
            elif domelement.name == "DIRECTION":
                coords = domelement.data[1]
                self.entitys.append(CartPoint(domelement, coords))

            elif domelement.name == "NEXT_ASSEMBLY_USAGE_OCCURRENCE":
                assembly_connections.append(domelement)

            elif domelement.name == "CLOSED_SHELL":
                solid = Solid(domelement)
                self.entitys.append(solid)
                self.solids.append(solid)

            elif domelement.name == "PRODUCT_DEFINITION":
                component = Component(domelement)
                self.entitys.append(component)
                self.components.append(component)

            elif domelement.name == "ADVANCED_FACE":
                if domelement.parents[-1].name == "PLANE":
                    self.entitys.append(PlaneFace(domelement))

                elif domelement.parents[-1].name == "CYLINDRICAL_SURFACE":
                    self.entitys.append(CylindricalFace(domelement))
                    # self.entitys[i].component.cylindersfaces.append(self.entitys[i]) Not sure if this should be here or in Component.complete__init__()
                else:
                    self.entitys.append(Face(domelement))

            elif domelement.name == "EDGE_CURVE":

                if domelement.parents[2].name == "LINE":

                    self.entitys.append(Line(domelement))

                elif domelement.parents[2].name == "CIRCLE":

                    self.entitys.append(ArcEdge(domelement))

                elif domelement.parents[2].name == "ELLIPSE":

                    self.entitys.append(EllipseEdge(domelement))

                elif domelement.parents[2].name == "B_SPLINE_CURVE_WITH_KNOTS":
                    entity = domelement.parents[2]

                    control_raw = np.array(entity.data[7], dtype=float)
                    repeats = np.array(entity.data[6], dtype=int)
                    control = []
                    for c, rep in zip(control_raw, repeats):
                        for xxxx in range(rep):
                            control.append(c)

                    self.entitys.append(SplineEdge(domelement, control))

                elif domelement.parents[2].name == "":
                    data = domelement.parents[2].data
                    if data[2].strip() == "B_SPLINE_CURVE":
                        control_raw = np.array(data[5][1], dtype=float)
                        repeats = np.array(data[5][0], dtype=int)
                        control = []
                        for c, rep in zip(control_raw, repeats):
                            for xxxx in range(rep):
                                control.append(c)
                        self.entitys.append(SplineEdge(domelement, control))

            elif domelement.name == "EDGE_LOOP":
                self.entitys.append(Edgeloop(domelement))

            elif domelement.name == "VECTOR":
                coords = (Vec(np.array(domelement.parents[0].data[1], dtype=float)) * float(domelement.data[2])).koordinaten
                self.entitys.append(CartPoint(domelement, coords))

            elif domelement.name == "VERTEX_POINT":

                vertex = domelement
                cart = vertex.parents[0]

                for child in vertex.children:
                    i = child.parents.index(vertex)
                    child.parents[i] = cart

                cart.children.remove(vertex)
                cart.children.extend(vertex.children)
                self.entitys.append(cart)

            else:
                pass

                # insert basic entity ? self.entitys.append(Entity(id, name, parents, data, self))

        for domelement in assembly_connections:
            parent = domelement.parents[0].entity
            child = domelement.parents[1].entity
            name = domelement.data[0][0]
            parent.sub_components[name] = child

        for component in self.components:
            component.complete__init__()

        print("Model loaded")

    def get_dom_elem_by_id(self, dom_elem_id):
        if dom_elem_id - self.idoffset < len(self.DOM):
            return self.DOM[dom_elem_id - self.idoffset]
        else:
            return None

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
