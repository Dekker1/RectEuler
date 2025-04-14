from gurobipy import GRB
import Box_gurobi
from typing import Tuple, List
from ElementGroup import ElemementGroup


class GurobiElementGroup():
    def __init__(self, element, model, ID, config):
        # self.name = name
        self.ID = 'p' + str(ID)
        self.number = ID
        self.BoxesContainedIn: List[Box_gurobi.Box] = []
        self.corner_left = (model.addVar(name="Primitive_{}_{}".format(ID, 'x1'), lb=0, vtype=GRB.CONTINUOUS),
                            model.addVar(name="Primitive_{}_{}".format(ID, 'y1'), lb=0, vtype=GRB.CONTINUOUS))

        self.corner_right = (model.addVar(name="Primitive_{}_{}".format(ID, 'x2'), lb=0, vtype=GRB.CONTINUOUS),
                             model.addVar(name="Primitive_{}_{}".format(ID, 'y2'), lb=0, vtype=GRB.CONTINUOUS))
        self.model = model
        self.item = ElemementGroup(element, config=config, gurobiElementGroup=self)
        pass

    def setSizeConctraint(self):
        size = self.item.getSize()
        self.model.addConstr((self.corner_right[0] - self.corner_left[0]) == size[0])
        self.model.addConstr((self.corner_right[1] - self.corner_left[1]) == size[1])

    def value(self):
        width = int(self.corner_right[0].X - self.corner_left[0].X)
        height = int(self.corner_right[1].X - self.corner_left[1].X)
        return (int(self.corner_left[0].X), int(self.corner_left[1].X)), (width, height)

    def value2(self):
        x = self.model.cbGetSolution([self.corner_right[0], self.corner_left[0], self.corner_right[1], self.corner_left[1]])
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
        return "ElementGroup {} ({}, {}) - ({}, {})".format(self.name, self.corner_left[0].value(),
                                                            self.corner_left[1].value(),
                                                            self.corner_right[0].value(), self.corner_right[1].value())

    def __repr__(self):
        return str(self)

    def to_json(self):
        (x, y), (width, height) = self.value2()

        d = {
            "ID": self.ID,
            "position": {"x": x, "y": y},
            "size": {"width": width, "height": height},
            "elements": self.item.elements,
            "containedin": [{"ID": b.ID, "name": b.name} for b in self.BoxesContainedIn]
        }
        return d
