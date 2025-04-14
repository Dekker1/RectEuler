import base64
from typing import Tuple, Optional
from PIL import ImageFont, ImageDraw, Image
from collections import namedtuple
import svgwrite
from svgwrite import base, text, image
from functools import lru_cache

Size = namedtuple("Size", "width height")
Position = namedtuple("Position", "x y")
Margin = namedtuple("Margin", "left right top bottom")


class Element:

    def __init__(self, name, margin: Tuple[int, int, int, int] = (4, 4, 4, 4), **extra):
        self.position: Position = None
        self.name = name
        self.margin = Margin(left=margin[0], right=margin[1], top=margin[2], bottom=margin[3])

    def getSize(self) -> Size:
        raise NotImplementedError()

    def getSVGReresentation(self) -> svgwrite.base.BaseElement:
        raise NotImplementedError()

    def setPosition(self, position: Tuple[int, int]):
        self.position = Position(position[0], position[1])


class TextElement(Element):
    def __init__(self, inputText: str, font: str = "Arial", fontSize: int = 16, **extra):
        self.text: str = inputText
        self.font: str = font
        self.fontSize: int = fontSize
        super().__init__(self.text, **extra)

    @lru_cache
    def _getSize(self, text_string: str, fontFamily: str, fontSize: int, margin: Margin) -> Size:
        fontName = fontFamily.lower() + ".ttf"
        font = ImageFont.truetype('DejaVuSans.ttf', fontSize)
        # https://stackoverflow.com/a/46220683/9263761
        text_string = text_string.replace("\\n", '\n')
        img = Image.new("RGBA", (1, 1))
        draw = ImageDraw.Draw(img)
        self.textsize = draw.textsize(text_string, font)
        self.margin = margin
        return Size(self.textsize[0] + margin.left + margin.right, self.textsize[1] + margin.top + margin.bottom)

    def getSize(self) -> Size:
        return self._getSize(self.text, self.font, self.fontSize, self.margin)

    def getSVGReresentation(self) -> svgwrite.text.Text:
        text = svgwrite.text.Text('', class_="element", fill='black')
        # TODO Hacky
        text.add(svgwrite.text.TSpan(self.text, x=[self.position[0] + self.margin.left], y=[self.position[1]], font_family="Arial, Helvetica, sans-serif"))
        return text

    def to_json(self):
        d = {
            "type": "Text",
            "text": self.text,
            "x": self.position[0],
            "y": self.position[1]+20
        }
        return d


class ImageElement(Element):

    def __init__(self, name, size: Tuple[int, int], imageContent: Optional[str] = None, imagePath: Optional[str] = None, extra={}):

        if imageContent is None and imagePath is None:
            raise ValueError("Either imageContent or imagePath might be None, but not both!")
        if imageContent is not None and imagePath is not None:
            raise ValueError("Either imageContent or imagePath might be not None, but not both!")
        self.imageContent = imageContent
        self.imagePath = imagePath
        self.size = size
        self.name = name
        self.extra = extra
        super().__init__(name, **extra)

    def getSize(self) -> Tuple[int, int]:
        return Size(width=self.size[0] + self.margin.right + self.margin.left, height=self.size[1] + self.margin.top + self.margin.bottom)

    def getSVGReresentation(self) -> svgwrite.base.BaseElement:
        if self.imagePath is not None:
            self.imageContent = open(self.imagePath, "r").read()
        x = self.position[0] + self.margin.left
        y = self.position[1] + self.margin.top
        return svgwrite.image.Image(self._imgtoBase64(self.imageContent), size=self.size, x=x, y=y, class_="element", **self.extra)

    def _imgtoBase64(self, imgData) -> str:
        raise NotImplementedError()

    def to_json(self):
        d = {
            "type": "Image",
            "image": self.imagePath,
            "position": {
                "x": self.position[0],
                "y": self.position[1]
            },
            "size": {
                "width": self.size[0],
                "height": self.size[1],

            }
        }
        return d


class SVGImageElement(ImageElement):
    def _imgtoBase64(self, imgData) -> str:
        return "data:image/svg+xml;base64," + base64.b64encode(imgData.encode('ascii')).decode('ascii')


class PNGImageElement(ImageElement):
    def _imgtoBase64(self, imgData) -> str:
        return "data:image/png;base64," + base64.b64encode(imgData.encode('ascii')).decode('ascii')


class JPEGImageElement(ImageElement):
    def _imgtoBase64(self, imgData) -> str:
        return "data:image/jpeg;base64," + base64.b64encode(imgData.encode('ascii')).decode('ascii')

