from dataclasses import dataclass
from IntersectionStatus import IntersectionStatus
import shapely.geometry


@dataclass
class ShapeInfo:
    shape: shapely.geometry.base.BaseGeometry
    status: IntersectionStatus

    def to_json(self):
        d = {
            "status": self.status,
            "points": shapely.geometry.mapping(self.shape)['coordinates'][0],
            "area":self.shape.area
        }
        return d
