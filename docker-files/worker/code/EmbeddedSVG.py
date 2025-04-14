from io import StringIO

import svgwrite
from svgwrite.base import BaseElement
from svgwrite.mixins import Presentation, Transform, XLink, Clipping
from svgwrite.utils import iterflatlist, strlist, is_string
from xml.dom.minidom import parseString
from svgwrite.mixins import Transform, _vert, _horiz, Clipping
import base64


class EmbeddedSVG(BaseElement, Transform, Clipping):
    elementname = 'image'

    def __init__(self, content, insert=None, size=None,
                 **extra):
        """
        :param string text: **tspan** content
        :param 2-tuple insert: The **insert** parameter is the absolute insert point
                               of the text, don't use this parameter in combination
                               with the **x** or the **y** parameter.
        :param list x: list of absolute x-axis values for characters
        :param list y: list of absolute y-axis values for characters
        :param list dx: list of relative x-axis values for characters
        :param list dy: list of relative y-axis values for characters
        :param list rotate: list of rotation-values for characters (in degrees)
        """
        super(EmbeddedSVG, self).__init__(**extra)
        dom = parseString(content)
        SVGs = dom.getElementsByTagName('svg')

        if len(SVGs) == 0:
            raise ValueError("Given String does not contain SVG Tag")
        self.rootSVG = SVGs[0]

        #self.rootSVG.setAttribute("width", size[0])
        #self.rootSVG.setAttribute("height", size[1])

        out = StringIO()
        for child in self.rootSVG.childNodes:
            child.writexml(out)
        # self.text = out.getvalue()

        # self['src'] = "data:image/svg+xml;utf8," + out.getvalue()

        self['xlink:href'] = "data:image/svg+xml;base64," + base64.b64encode(content.encode('ascii')).decode('ascii')

        # for key, attribute in self.rootSVG.attributes.items():
        #    if key not in extra.keys():
        #       self[key] = attribute

        # self.text = text
        if insert is not None:
            self['x'] = insert[0]
            self['y'] = insert[1]
        if size is not None:
            self['width'] = size[0]
            self['height'] = size[1]

        # self['xlink:href'] = ""

    def stretch(self):
        """ Stretch viewBox in x and y direction to fill viewport, does not
        preserve aspect ratio.
        """
        self['preserveAspectRatio'] = 'none'

    def fit(self, horiz="center", vert="middle", scale="meet"):
        """ Set the preserveAspectRatio attribute.
        :param string horiz: horizontal alignment ``'left'|'center'|'right'``
        :param string vert: vertical alignment ``'top'|'middle'|'bottom'``
        :param string scale: scale method ``'meet'|'slice'``
        ============= ===========
        Scale methods Description
        ============= ===========
        ``meet``      preserve aspect ration and zoom to limits of viewBox
        ``slice``     preserve aspect ration and viewBox touch viewport on all bounds, viewBox will extend beyond the bounds of the viewport
        ============= ===========
        """
        if self.debug and scale not in ('meet', 'slice'):
            raise ValueError("Invalid scale parameter '%s'" % scale)
        self.attribs['preserveAspectRatio'] = "%s%s %s" % (_horiz[horiz], _vert[vert], scale)

    # def get_xml(self):
    #    xml = super(EmbeddedSVG, self).get_xml()
    #    xml.text = self.text
    #   return xml

    # def tostring(self):
    #   return self.get_xml().text


if __name__ == "__main__":
    ch = open("ch.svg", "r").read()
    print(ch)
    dwg = svgwrite.Drawing("out.svg", debug=False, profile='full')
    textrect = dwg.g()
    args = {"src": "data:image/svg+xml;utf8,<svg ... > ... </svg>"}
    img = dwg.image("", **args)
    extra = {"id": "abc"}
    s = EmbeddedSVG(ch, size=(40, 30), **extra)

    t1 = s.get_xml()
    t2 = s.tostring()

    textrect.add(s)
    dwg.add(textrect)
    dwg.save()
    pass
