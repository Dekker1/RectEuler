import json
import math
import os
from collections import namedtuple
from typing import Iterable, Tuple, Union, List, Dict, Optional

import numpy as np
import rpack
import svgwrite
import svgwrite.base
import svgwrite.drawing
import svgwrite.text
import svgwrite.container
import svgwrite.shapes

import packing
from Element import Element, TextElement, SVGImageElement, PNGImageElement, JPEGImageElement

Margin = namedtuple("Margin", "left right top bottom")


class ElemementGroup:
    def __init__(self, elements: Union[Iterable[Element], Iterable[str]], config: Optional[Dict], gurobiElementGroup):
        self.elements: List[Element] = []

        self.circleDiam = 10
        self.circleMargins = Margin(3, 3, 3, 3)
        self.RepresentationCircleSpaceMargin = Margin(0, 0, 0, 0)
        self.RepresentationCircleSpacePadding = Margin(2, 2, 2, 2)
        self.circleCols = 2

        for element in elements:
            if isinstance(element, str):
                self.elements.append(self._generateElement(element, config))
            else:
                self.elements.append(element)

        self.gurobiElementGroup = gurobiElementGroup
        self._totalSize: Tuple[int, int] = (0, 0)

        self._sortElements()
        self.pack()

    def _generateElement(self, name: str, config: Optional[Dict]):
        if config is None:
            type = "text"
            return TextElement(name)
        else:
            type = config["settings"]["type"]
            path = config["settings"]["path"]
            key = config["settings"]["key"]
            value = config["data"][name][key]
            givenMIN = config["settings"]["min-value"][key]
            givenMAX = config["settings"]["max-value"][key]
            desiredMINwidth = config["settings"]["min-width"]
            desiredMINheight = config["settings"]["min-height"]
            desiredMAXwidth = config["settings"]["max-width"]
            desiredMAXheight = config["settings"]["max-height"]
            if config["settings"]["useScaling"]:
                scaling = self._normalize(value, givenMIN, givenMAX)
                width = desiredMINwidth + math.sqrt(scaling) * (desiredMAXwidth - desiredMINwidth)
                height = desiredMINheight + math.sqrt(scaling) * (desiredMAXheight - desiredMINheight)
            else:
                width = desiredMINwidth
                height = desiredMINheight
            tooltip = config["data"][name]["name"]
            imagePath = os.path.join(path, config["data"][name]["file"])
            kwargs = {"data-set-name": tooltip, "debug": False}

            if type not in ["text", "SVG", "PNG", "JPEG"]:
                raise ValueError("Type has to be one of text, SVG, PNG, JPEG")
            if type == "SVG":
                return SVGImageElement(name, imagePath=imagePath, size=(width, height), extra=kwargs)
            if type == "JPEG":
                return JPEGImageElement(name, imagePath=imagePath, size=(width, height), extra=kwargs)
            if type == "PNG":
                return PNGImageElement(name, imagePath=imagePath, size=(width, height), extra=kwargs)

    def _sortElements(self):
        self.elements = sorted(self.elements, key=lambda element: element.getSize().width, reverse=True)

    def _normalize(self, value: float, min: float, max: float) -> float:
        return (value - min) / (max - min)

    def getSize(self) -> Tuple[int, int]:
        if len(self.gurobiElementGroup.BoxesContainedIn) == 1:
            self.circleCols = 1

        width = self._totalSize[0] + self._getRepresentationCircleSpaceSize()[0]
        height = max(self._totalSize[1], self._getRepresentationCircleSpaceSize()[1])
        return width, height

    def setGurobiElementGroup(self, group):
        self.gurobiElementGroup = group

    def _getRepresentationCircleSpaceSize(self) -> Tuple[int, int]:
        numberOfBoxes = len(self.gurobiElementGroup.BoxesContainedIn)
        rows = np.ceil(numberOfBoxes / self.circleCols)
        width = (
                        self.circleDiam + self.circleMargins.left + self.circleMargins.right) * self.circleCols + self.RepresentationCircleSpaceMargin.left + self.RepresentationCircleSpaceMargin.right + self.RepresentationCircleSpacePadding.left + self.RepresentationCircleSpacePadding.right
        height = (
                         self.circleDiam + self.circleMargins.top + self.circleMargins.bottom) * rows + self.RepresentationCircleSpaceMargin.top + self.RepresentationCircleSpaceMargin.bottom + self.RepresentationCircleSpacePadding.top + self.RepresentationCircleSpacePadding.bottom
        return width, height

    def getSVGReresentation(self) -> svgwrite.base.BaseElement:
        point, dim = self.gurobiElementGroup.value2()
        ID = self.gurobiElementGroup.ID
        ElementGroupG = svgwrite.container.Group(transform="translate ({}, {})".format(point[0], point[1]), class_=f"elementGroup {ID}", id=ID)
        boxIDs = [b.ID for b in self.gurobiElementGroup.BoxesContainedIn]
        kwargs = {'data-sets': json.dumps(boxIDs), "rx": "5px"}
        ElementGroupRect = svgwrite.shapes.Rect((0, 0), self.getSize(), class_="element-rect", debug=False, **kwargs)
        ElementGroupRect.fill(opacity=0)

        for element in self.elements:
            ElementGroupG.add(element.getSVGReresentation())

        ElementGroupG.add(self._getSVGRepresenatationCircleSpace())
        ElementGroupG.add(ElementGroupRect)
        ElementGroupG.add(self._getSVGRepresenatationCircles())

        return ElementGroupG

    def _getSVGRepresenatationCircleSpace(self) -> svgwrite.base.BaseElement:
        encodingCircleGPos = (self._totalSize[0] + self.RepresentationCircleSpaceMargin.left, self.RepresentationCircleSpaceMargin.top)
        width = self._getRepresentationCircleSpaceSize()[0] - self.RepresentationCircleSpaceMargin.left - self.RepresentationCircleSpaceMargin.right
        height = self._getRepresentationCircleSpaceSize()[1] - self.RepresentationCircleSpaceMargin.top - self.RepresentationCircleSpaceMargin.bottom
        encodingCircleRect = svgwrite.shapes.Rect((self.RepresentationCircleSpaceMargin.left + encodingCircleGPos[0], self.RepresentationCircleSpaceMargin.top + encodingCircleGPos[1]), (width, height), fill="white", rx="5")
        return encodingCircleRect

    def _getSVGRepresenatationCircles(self) -> svgwrite.base.BaseElement:
        from utils import getColor
        encodingCircleGPos = (self._totalSize[0] + self.RepresentationCircleSpaceMargin.left + self.RepresentationCircleSpacePadding.left, self.RepresentationCircleSpaceMargin.top + self.RepresentationCircleSpacePadding.top)
        encodingCircleG = svgwrite.container.Group(transform="translate ({}, {})".format(encodingCircleGPos[0], encodingCircleGPos[1]))

        for i, box in enumerate(self.gurobiElementGroup.BoxesContainedIn):
            colorIdx = box.number
            name = box.name.replace("\\n", " ")
            col = i % self.circleCols
            row = i // self.circleCols

            xPos = col * (self.circleDiam + self.circleMargins.left + self.circleMargins.right) + self.circleDiam / 2 + self.circleMargins.left
            yPos = row * (self.circleDiam + self.circleMargins.top + self.circleMargins.bottom) + self.circleDiam / 2 + self.circleMargins.top

            center = (xPos, yPos)
            kwargs = {'data-set_name': name, "data-set_id": box.ID}
            encodingCircleG.add(svgwrite.shapes.Circle(center=center, r=self.circleDiam / 2, fill=getColor(colorIdx), class_="encoding-circle", debug=False, **kwargs))
        return encodingCircleG

    def pack(self):
        sizes = [element.getSize() for element in self.elements]
        positions = packing.pack(sizes)
        for element, position in zip(self.elements, positions):
            element.setPosition(position)
        self._totalSize = rpack.bbox_size(sizes, positions)

    def to_json(self):
        d = {
            "elements": self.elements
        }
        return d
