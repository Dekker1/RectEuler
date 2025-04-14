from enum import Enum


class IntersectionStatus(str, Enum):
    EmptyUnwantedIntersection: str = "EmptyUnwantedIntersection"
    EmptyWantedIntersection: str = "EmptyWantedIntersection"
    WantedFilledIntersection: str = "WantedFilledIntersection"
