import re
from .step_entitiys import *
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

        for b in blocks:
            data = re.findall('(\-*\w+\.\d*\w*\-*\+*\d*)', b)  ##Changed to get T. and F.
            #  data = re.findall('(\-*\d+\.\d*\w*\-*\+*\d*)', b)  ##worked perfect for numbers
            ids = re.findall('#(\d+)', b)
            if len(ids) > 1:
                id = int(ids.pop(0))
                parents = ids
                name = re.findall(r'=(\w+)|$', b)[0]
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
                    self.entitys.append(CartPoint(id, name, parents, data, self))
                elif name == "DIRECTION":
                    self.entitys.append(CartPoint(id, name, parents, data, self))
                elif name == "CLOSED_SHELL":
                    component = Component(id, name, parents, data, self)
                    self.entitys.append(component)
                    self.components.append(component)
                else:
                    self.entitys.append(Entity(id, name, parents, data, self))
            if len(self.entitys) > 0:
                self.entitys[len(self.entitys) - 1].block = b

        self.idoffset = int(self.entitys[0].getID())

        for e in self.entitys:
            for pidstring in e.getParentsstring():
                if pidstring != "NONE":
                    e.appendparent(int(pidstring))
                    self.get_entity_by_id(int(pidstring)).appendchild(e.getID())
                    # self.getEntityByID(int(pidstring)).appendchild(e) #directlink

        for i in range(0, len(self.entitys)):

            if self.entitys[i].getName() == "ADVANCED_FACE":
                if self.entitys[i].getParents()[len(self.entitys[i].getParents()) - 1].getName() == "PLANE":
                    self.entitys[i] = PlaneFace(self.entitys[i], self)

                elif self.entitys[i].getParents()[len(self.entitys[i].getParents()) - 1].getName() == "CYLINDRICAL_SURFACE":
                    self.entitys[i] = CylindricalFace(self.entitys[i], self)
                    # self.entitys[i].component.cylindersfaces.append(self.entitys[i]) Not sure if this should be here or in Component.complete__init__()

            elif self.entitys[i].getName() == "EDGE_CURVE" and self.entitys[i].getParents()[2].getName() == "LINE":

                self.entitys[i] = Line(self.entitys[i], self)

            elif self.entitys[i].getName() == "EDGE_CURVE" and self.entitys[i].getParents()[2].getName() == "CIRCLE":

                self.entitys[i] = ArcEdge(self.entitys[i], self)

            elif self.entitys[i].getName() == "EDGE_CURVE" and self.entitys[i].getParents()[2].getName() == "ELLIPSE":

                self.entitys[i] = EllipseEdge(self.entitys[i], self)

            elif self.entitys[i].getName() == "VECTOR":
                data = (Vec(self.entitys[i].getParents(0).getData()) * float(self.entitys[i].getData()[0])).koordinaten
                self.entitys[i] = CartPoint(self.entitys[i].id, self.entitys[i].name, self.entitys[i].parentsstring,
                                            data, self)

            elif self.entitys[i].getName() == "VERTEX_POINT":
                self.entitys[i].getParents()[0].children.append(self.entitys[i].getChildren())

        for component in self.components:
            component.complete__init__()

    def get_entity_by_id(self, entity_id):
        if entity_id - int(self.entitys[0].getID()) < len(self.entitys):
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
