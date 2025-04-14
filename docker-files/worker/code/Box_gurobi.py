from utils import getTextSizes
from gurobipy import GRB
from typing import Tuple, Iterable
import ElementGroup_gurobi


class Box():
    def __init__(self, name, model, boxID):
        self.name = name
        self.ID = 'b' + str(boxID)
        self.number = boxID
        self.PrimitiveConstrains = {}
        self.model = model
        self.corner_left = (model.addVar(name="Box_{}_{}".format(boxID, 'x1'), lb=0, vtype=GRB.CONTINUOUS),
                            model.addVar(name="Box_{}_{}".format(boxID, 'y1'), lb=0, vtype=GRB.CONTINUOUS))

        self.corner_right = (model.addVar(name="Box_{}_{}".format(boxID, 'x2'), lb=0, vtype=GRB.CONTINUOUS),
                             model.addVar(name="Box_{}_{}".format(boxID, 'y2'), lb=0, vtype=GRB.CONTINUOUS))
        self.model = model
        self.containedPrimitives: Iterable[ElementGroup_gurobi.GurobiElementGroup] = []

        self.text_corner_left = (model.addVar(name="Box_text_{}_{}".format(boxID, 'x1'), lb=0, vtype=GRB.CONTINUOUS),
                                 model.addVar(name="Box_text_{}_{}".format(boxID, 'y1'), lb=0, vtype=GRB.CONTINUOUS))
        self.text_corner_right = (model.addVar(name="Box_text_{}_{}".format(boxID, 'x2'), lb=0, vtype=GRB.CONTINUOUS),
                                  model.addVar(name="Box_text_{}_{}".format(boxID, 'y2'), lb=0, vtype=GRB.CONTINUOUS))

        self.textSize = getTextSizes([self.name], [0, 2, 0, 0], fontSize=18)[0]

        self.model.addConstr(self.text_corner_left[0] == self.corner_left[0] + 10)
        self.model.addConstr(self.text_corner_left[1] == self.corner_left[1] + 10)

        self.model.addConstr(self.text_corner_right[0] == self.text_corner_left[0] + self.textSize[0])
        self.model.addConstr(self.text_corner_right[1] == self.text_corner_left[1] + self.textSize[1])

        self.model.addConstr(self.corner_right[0] - self.corner_left[0] >= self.text_corner_right[0] - self.text_corner_left[0] + 5)

    def addPrimitive(self, p):
        c1 = self.model.addConstr(p.corner_left[0] - self.corner_left[0] >= 10)
        c2 = self.model.addConstr(p.corner_left[1] - self.corner_left[1] >= max(30, self.textSize[1] + 10))

        c3 = self.model.addConstr(self.corner_right[0] - p.corner_right[0] >= 10)
        c4 = self.model.addConstr(self.corner_right[1] - p.corner_right[1] >= 10)
        self.PrimitiveConstrains[p.ID] = [c1, c2, c3, c4]
        self.containedPrimitives.append(p)

    def removePrimitiveConstrains(self, primitives):
        for p in primitives:
            for c in self.PrimitiveConstrains[p.ID]:
                self.model.remove(c)

    def value(self):
        width = int(self.corner_right[0].X - self.corner_left[0].X)
        height = int(self.corner_right[1].X - self.corner_left[1].X)
        return (int(self.corner_left[0].X), int(self.corner_left[1].X)), (width, height)

    def value2(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        x = self.model.cbGetSolution([self.corner_right[0], self.corner_left[0], self.corner_right[1], self.corner_left[1]])
        width = int(x[0] - x[1])
        height = int(x[2] - x[3])
        return ((int(x[1]), int(x[3])), (width, height))

    def nameCoords(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        x = self.model.cbGetSolution([self.text_corner_right[0], self.text_corner_left[0], self.text_corner_right[1], self.text_corner_left[1]])
        width = int(x[0] - x[1])
        height = int(x[2] - x[3])
        return ((int(x[1]), int(x[3])), (width, height))

    def getPolygon(self):
        pos, size = self.value2()
        corners = [pos, (pos[0] + size[0], pos[1]), (pos[0] + size[0], pos[1] + size[1]), (pos[0], pos[1] + size[1])]
        return corners

    def getShapelyBoxCoords(self) -> Tuple[int, int, int, int]:
        pos, size = self.value2()
        corners = (pos[0], pos[1], pos[0] + size[0], pos[1] + size[1])
        return corners

    def __str__(self):
        return "Box {} ({}, {}) - ({}, {})".format(self.name, self.corner_left[0].X, self.corner_left[1].X,
                                                   self.corner_right[0].X, self.corner_right[1].X)

    def __repr__(self):
        return str(self)

    def to_json(self):
        (x, y), (width, height) = self.value2()
        (Name_x, Name_y), (Name_width, Name_height) = self.nameCoords()

        d = {
            "ID": self.ID,
            "position": {"x": x, "y": y},
            "size": {"width": width, "height": height},
            "name": {"size": {"width": Name_width, "height": Name_height}, "text": self.name},
            #"elementGroups": self.containedPrimitives

        }
        return d
