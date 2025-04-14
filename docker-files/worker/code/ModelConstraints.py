import logging
from typing import Dict, Tuple, List

import gurobipy as gp

from Box_gurobi import Box
from ElementGroup_gurobi import GurobiElementGroup

primitiveDist = 10
boxDist = 10


def BoxPrimitiveExclude(model: gp.Model, Primitives: Dict[Tuple, GurobiElementGroup], Boxes: List[Box]) -> None:
    M = model._M
    for primitive in Primitives.values():
        for box in Boxes:

            if primitive in box.containedPrimitives:
                continue

            b1, b2, b3, b4 = model._BoxPrimitiveExludeVars[primitive.ID + "_" + box.ID]
            model.addConstr(b1 + b2 + b3 + b4 <= 3)

            model.addConstr(primitive.corner_right[0] + primitiveDist <= box.corner_left[0] + M * b1)
            model.addConstr(primitive.corner_right[1] + primitiveDist <= box.corner_left[1] + M * b2)
            model.addConstr(box.corner_right[0] + primitiveDist <= primitive.corner_left[0] + M * b3)
            model.addConstr(box.corner_right[1] + primitiveDist <= primitive.corner_left[1] + M * b4)

def BoxBoxSubsetConstraints(model: gp.Model, Boxes: List[Box]) -> None:
    for i in range(len(Boxes)):
        for j in range(i + 1, len(Boxes)):
            p1 = Boxes[i]
            p2 = Boxes[j]

            if p1 == p2:
                continue

            p1_set = set(p1.containedPrimitives)
            p2_set = set(p2.containedPrimitives)

            # if p2 is totally in p1
            if p2_set <= p1_set:
                model.addConstr(p1.corner_left[0] <= p2.corner_left[0] - boxDist)
                model.addConstr(p1.corner_left[1] <= p2.corner_left[1] - boxDist - p1.textSize[1])

                model.addConstr(p1.corner_right[0] - boxDist >= p2.corner_right[0])
                model.addConstr(p1.corner_right[1] - boxDist >= p2.corner_right[1])
                p1.removePrimitiveConstrains(p2.containedPrimitives)
                logging.info(f"Case 1{p2.name} in {p1.name}")
                continue

            if p1_set <= p2_set:
                logging.info(f"Case 2{p1.name} in {p2.name}")

                model.addConstr(p2.corner_left[0] <= p1.corner_left[0] - boxDist)
                model.addConstr(p2.corner_left[1] <= p1.corner_left[1] - boxDist - p2.textSize[1])

                model.addConstr(p2.corner_right[0] - boxDist >= p1.corner_right[0])
                model.addConstr(p2.corner_right[1] - boxDist >= p1.corner_right[1])
                p2.removePrimitiveConstrains(p1.containedPrimitives)
                continue

def setNameOverlapConstraints(model: gp.Model, Boxes: List[Box]) -> None:
    M = model._M
    for i in range(len(Boxes)):
        for j in range(i + 1, len(Boxes)):

            p1 = Boxes[i]
            p2 = Boxes[j]

            if p1 == p2:
                continue

            b1, b2, b3, b4 = model._setNameOverlapVars[p1.ID + "_" + p2.ID]

            c = model.addConstr(b1 + b2 + b3 + b4 <= 3)

            c = model.addConstr(p1.text_corner_right[0] + primitiveDist <= p2.text_corner_left[0] + M * b1)
            c = model.addConstr(p1.text_corner_right[1] + primitiveDist <= p2.text_corner_left[1] + M * b2)

            c = model.addConstr(p2.text_corner_right[0] + primitiveDist <= p1.text_corner_left[0] + M * b3)
            c = model.addConstr(p2.text_corner_right[1] + primitiveDist <= p1.text_corner_left[1] + M * b4)

def preventBoxOverlap(model: gp.Model, Boxes: List[Box]) -> None:
    M = model._M
    for i in range(len(Boxes)):
        for j in range(i + 1, len(Boxes)):
            # continue
            box1 = Boxes[i]
            box2 = Boxes[j]

            # text if two sets share elements
            if bool(set(box1.containedPrimitives) & set(box2.containedPrimitives)):
                logging.info(f"{box1.name} and {box2.name} share elements")
                continue

            logging.info(f"Apply preventBoxOverlap for {box1.name} and {box2.name}")

            b1, b2, b3, b4 = model._BoxOverlapVars[box1.ID + "_" + box2.ID]

            model.addConstr(b1 + b2 + b3 + b4 <= 3)

            model.addConstr(box1.corner_right[0] + primitiveDist <= box2.corner_left[0] + M * b1)
            model.addConstr(box1.corner_right[1] + primitiveDist <= box2.corner_left[1] + M * b2)

            model.addConstr(box2.corner_right[0] + primitiveDist <= box1.corner_left[0] + M * b3)
            model.addConstr(box2.corner_right[1] + primitiveDist <= box1.corner_left[1] + M * b4)

def BoxtoBoxDistance(model: gp.Model) -> bool:
    M = model._M
    Boxes = model._boxes

    for i in range(len(Boxes)):
        for j in range(i + 1, len(Boxes)):

            p1 = Boxes[i]
            p2 = Boxes[j]

            p1_set = set(p1.containedPrimitives)
            p2_set = set(p2.containedPrimitives)

            # if p2 is sbubset of p1 or vice versa
            if p2_set <= p1_set or p1_set <= p2_set:
                continue
            if not bool(p1_set & p2_set):
                if preventBoxOverlap:
                    continue

            b1, b2, b3, b4, b5, b6, b7, b8 = model._BoxtoBoxDistanceVariables["{}_{}".format(p1.ID, p2.ID)]

            # distance of right edge of p1 to left edge of p2
            model.addConstr((p1.corner_right[0] - p2.corner_left[0]) + b1 * M >= boxDist)
            model.addConstr(-(p1.corner_right[0] - p2.corner_left[0]) + (1 - b1) * M >= boxDist)

            # distance of left edge of p1 to left edge of p2
            model.addConstr((p1.corner_left[0] - p2.corner_left[0]) + b2 * M >= boxDist)
            model.addConstr(-(p1.corner_left[0] - p2.corner_left[0]) + (1 - b2) * M >= boxDist)

            # distance of right edge of p1 to right edge of p2
            model.addConstr((p1.corner_right[0] - p2.corner_right[0]) + b3 * M >= boxDist)
            model.addConstr(-(p1.corner_right[0] - p2.corner_right[0]) + (1 - b3) * M >= boxDist)

            # distance of left edge of p1 to right edge of p2
            model.addConstr((p2.corner_right[0] - p1.corner_left[0]) + b7 * M >= boxDist)
            model.addConstr(-(p2.corner_right[0] - p1.corner_left[0]) + (1 - b7) * M >= boxDist)

            # distance of bottom edge of p1 to top edge of p2
            model.addConstr((p1.corner_right[1] - p2.corner_left[1]) + b4 * M >= boxDist)
            model.addConstr(-(p1.corner_right[1] - p2.corner_left[1]) + (1 - b4) * M >= boxDist)

            # distance of top edge of p1 to top edge of p2
            model.addConstr((p1.corner_left[1] - p2.corner_left[1]) + b5 * M >= boxDist)
            model.addConstr(-(p1.corner_left[1] - p2.corner_left[1]) + (1 - b5) * M >= boxDist)

            # distance of bottom edge of p1 to bottom edge of p2
            model.addConstr((p1.corner_right[1] - p2.corner_right[1]) + b6 * M >= boxDist)
            model.addConstr(-(p1.corner_right[1] - p2.corner_right[1]) + (1 - b6) * M >= boxDist)

            # distance of top edge of p1 to bottom edge of p2
            model.addConstr((p2.corner_right[1] - p1.corner_left[1]) + b8 * M >= boxDist)
            model.addConstr(-(p2.corner_right[1] - p1.corner_left[1]) + (1 - b8) * M >= boxDist)
