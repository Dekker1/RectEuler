import json
from PIL import ImageFont, ImageDraw, Image
import colorbrewer as brewer
import colorsys
import random
from ShapeInfo import ShapeInfo


circleDiam = 10
circleMargin = 5


class JSONEncoder(json.JSONEncoder):

    # overload method default
    def default(self, obj):
        # Match all the types you want to handle in your converter
        if isinstance(obj, ShapeInfo):
            return {"status": str(obj.status.name), "area": obj.shape.area}
        # Call the default method for other types
        return json.JSONEncoder.default(self, obj)


def get_text_dimensions(text_string, fontFamily, fontSize=16):
    fontName = fontFamily.lower() + ".ttf"
    font = ImageFont.truetype('DejaVuSans.ttf', fontSize)
    # https://stackoverflow.com/a/46220683/9263761
    ascent, descent = font.getmetrics()
    text_string = text_string.replace("\\n", '\n')

    text_width = font.getmask(text_string).getbbox()[2]
    text_height = font.getmask(text_string).getbbox()[3] + descent
    img = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(img)
    textsize = draw.textsize(text_string, font)

    return textsize


def getTextSizes(TextList, textMargins, fontFamily="Arial", fontSize=16):
    returnList = []
    for word in TextList:
        width, height = get_text_dimensions(word, fontFamily, fontSize)
        width += textMargins[0] + textMargins[1]
        height += textMargins[2] + textMargins[3]
        returnList.append((width, height))
    return returnList


def rgb_to_hex(color):
    r, g, b = color
    return f'#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}'


def randomColor(seed=None):
    v = 0.5 * random.random() + 0.5
    s = 0.5 * random.random() + 0.5
    random.seed(seed)
    h = random.random()
    rgb = colorsys.hsv_to_rgb(h, s, v)
    color = '#' + rgb_to_hex(rgb)
    return rgb_to_hex(rgb)


def getColor(idx):
    colors = brewer.qualitative['tableau'][20]

    if idx >= 20:
        color = randomColor(idx)
    else:
        color = colors[idx]

    return color


