import shapely as sp
import shapely.geometry
from shapely import ops
from Box_gurobi import Box
from ShapeInfo import ShapeInfo

from typing import Iterable, Tuple, List, Union, Set, Dict
from collections import namedtuple

SetShape = namedtuple("SetShape", "shape setIDs")
from IntersectionStatus import IntersectionStatus


class FakeBox:
    def __init__(self, pos: Tuple[int, int], size: Tuple[int, int], ID, name):
        self.pos = pos
        self.size = size
        self.ID = ID
        self.name = name
        self.containedPrimitives = []


class FakePrimitive:
    def __init__(self, ID, name):
        self.ID = ID
        self.BoxesContainedIn = []
        self.Name = name

    def getShapelyBoxCoords(self):
        return self.pos[0], self.pos[1], self.pos[0] + self.size[0], self.pos[1] + self.size[1]


# extend the json.JSONEncoder class


def calculateEmptyIntersection(boxes: Iterable[Union[Box, FakeBox]]) -> (Dict, str):
    intersectionByDepth = {1: dict()}
    intersectionByDepthIsEmpty = {1: dict()}

    boxdict = {}
    shapes = []
    depth = 1

    # for polygons in intersectionByDepth[1]
    for box in boxes:
        boxdict[box.ID] = box
        b = sp.geometry.box(*box.getShapelyBoxCoords())
        shapes.append(SetShape(b, box.ID))
        IDset = frozenset([box.ID])
        intersectionByDepth[depth][IDset] = b

    foundIntersection = True
    while foundIntersection:
        foundIntersection = False
        intersectionByDepth[depth + 1] = dict()
        intersectionByDepthIsEmpty[depth + 1] = dict()
        for setshape in shapes:
            shapeID = setshape.setIDs
            shape = setshape.shape
            for intersectionIDsSet, intersectionShape in intersectionByDepth[depth].items():
                if shapeID in intersectionIDsSet:
                    continue
                intersection = shape.intersection(intersectionShape)

                diff = intersectionShape.difference(intersection)

                intersectionByDepth[depth][intersectionIDsSet] = diff

                if not intersection.is_empty and intersection.geom_type in ["MultiPolygon", "Polygon"]:
                    foundIntersection = True
                    IDset = frozenset([*intersectionIDsSet, shapeID])
                    intersectionByDepth[depth + 1][IDset] = intersection
                    #continue
                else:
                    foundIntersection = foundIntersection or False


        depth += 1

    if not intersectionByDepth[depth]:
        del intersectionByDepth[depth]

    # draw(list(map(lambda x: x.shape, shapes)), list(map(lambda x: x.shape, shapes)))
    svg = []
    for i in range(1, depth):
        l = []
        for k, v, in intersectionByDepth[i].items():
            l.append(v)
    #            svg.append(v.shape.exterior.coords)
    # draw(l, list(map(lambda x: x.shape, shapes)))

    SVGDict = filterIntersectionDict(intersectionByDepth, boxdict)
    JSON = transformDict(SVGDict)

    return SVGDict, JSON


def filterIntersectionDict(intersectionByDepth: Dict[int, Dict[Set, shapely.geometry.base.BaseGeometry]], boxdict):
    returnDict = dict()

    for depth, d in intersectionByDepth.items():
        if not d:
            continue
        returnDict[depth] = dict()
        for setIDs, shape in d.items():
            l = []
            elementGroups = []

            for setID in setIDs:
                elementGroups.extend(boxdict[setID].containedPrimitives)
            boxesElementGroupsContainedIn = map(lambda x: x.BoxesContainedIn, elementGroups)

            if setIDs in [set(list(map(lambda x: x.ID, y))) for y in boxesElementGroupsContainedIn]:
                status = IntersectionStatus.EmptyWantedIntersection
            else:
                status = IntersectionStatus.EmptyUnwantedIntersection

            elementPolys = [sp.geometry.box(*elementGroup.getShapelyBoxCoords()) for elementGroup in elementGroups]

            if shape.geom_type == "Polygon" and not shape.is_empty:
                for elementPoly in elementPolys:
                    if shape.contains(elementPoly):
                        status = IntersectionStatus.WantedFilledIntersection
                        break
                l.append(ShapeInfo(shape, status))

            if shape.geom_type == "MultiPolygon" and not shape.is_empty:
                for polygon in shape.geoms:
                    tmpstatus = status
                    for elementPoly in elementPolys:
                        if polygon.contains(elementPoly):
                            tmpstatus = IntersectionStatus.WantedFilledIntersection
                            break
                    l.append(ShapeInfo(polygon, tmpstatus))

            if len(l) > 0:
                returnDict[depth][setIDs] = l
    return returnDict


def transformDict(inputDict):
    returndict = {}
    for depth, d in inputDict.items():
        returndict[depth] = []
        for sets, value in d.items():
            returndict[depth].append({"sets": list(sets), "shapes": value})
    return returndict


def drawoutineShape(axs, outlineshapes):
    new_shape = sp.ops.unary_union(outlineshapes)
    if new_shape.geom_type == 'MultiPolygon':
        for geom in new_shape.geoms:
            xs, ys = geom.exterior.xy
            axs.fill(xs, ys, fc='none', ec='b')
    elif new_shape.geom_type == 'Polygon':
        xs, ys = new_shape.exterior.xy
        axs.fill(xs, ys, fc='none', ec='b')


if __name__ == "__main__":
    s1 = shapely.geometry.MultiPolygon([
        shapely.geometry.Polygon([(0, 0), (0, 1), (1, 1), (1, 0)]),
        shapely.geometry.Polygon([(5, 5), (5, 6), (6, 6), (6, 0)])

    ])

    s2 = shapely.geometry.Polygon([(0, 0.1), (0, 1), (1, 1), (1, 0)])
    s = s1.difference(s1)
    pass
    # draw([r1, r2, r3])
