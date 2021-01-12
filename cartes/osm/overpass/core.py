from typing import Any, Dict

from shapely.geometry import LineString, Point, Polygon, mapping, shape
from shapely.geometry.base import BaseGeometry

from ...core import GeoObject
from ...utils.descriptors import OrientedShape
from ...utils.geometry import reorient
from ...utils.mixins import HBoxMixin, HTMLAttrMixin, HTMLTitleMixin
from ..requests import GeoJSONType, JSONType


def to_geometry(elt: JSONType) -> BaseGeometry:
    if elt["type"] == "node":
        return Point(elt["lon"], elt["lat"])

    nodes = elt.get("nodes", None)
    if nodes is not None:
        assert isinstance(nodes, list)
    shape = LineString if nodes is None or nodes[0] != nodes[-1] else Polygon
    return reorient(shape(list((p["lon"], p["lat"]) for p in elt["geometry"])))


class NodeWayRelation(GeoObject, HBoxMixin, HTMLTitleMixin, HTMLAttrMixin):
    shape = OrientedShape()
    subclasses: Dict[str, Any] = dict()

    def __new__(cls, json: GeoJSONType):
        type_ = NodeWayRelation.subclasses[json["type_"]]
        if cls in NodeWayRelation.subclasses.values():
            return super().__new__(cls)
        else:
            return type_.__new__(type_, json)

    def __init__(self, json: GeoJSONType):
        super().__init__()
        self.json = json

    @classmethod
    def __init_subclass__(cls):
        super().__init_subclass__()
        NodeWayRelation.subclasses[cls.__name__.lower()] = cls

    @property
    def __geo_interface__(self) -> GeoJSONType:
        return mapping(self.shape)

    @property
    def html_attr_list(self):
        return sorted(
            key
            for key, value in self.json.items()
            if key not in ["geometry", "nodes", "members", "_parent"]
            and (
                key == "name:en"
                or not (key.startswith("name:") or "_name" in key)
            )
            and "wiki" not in key
            and not key.startswith("source:")
            and value == value
        )

    def __repr__(self) -> str:
        return f"{type(self).__name__} {self.json}"

    def _repr_html_(self) -> str:
        return (
            super()._repr_html_()
            + "<div style='float: left; margin: 10px;'>"
            + self._repr_svg_()
            + "</div>"
        )

    def __getattr__(self, name):
        if name.endswith("_"):  # in case the name is reserved
            name = name[:-1]
        value = self.json.get(name, None)
        if value is None:
            address = self.json.get("address", None)
            if address is not None:
                value = address.get(name, None)
        if value is None:
            raise AttributeError(name)
        return value


class Node(NodeWayRelation):
    def __init__(self, json: GeoJSONType):
        super().__init__(json)
        self.shape = shape(self.json["geometry"])


class Way(NodeWayRelation):
    def __init__(self, json: GeoJSONType):
        super().__init__(json)
        self.shape = shape(self.json["geometry"])


class Relation(NodeWayRelation):
    subclasses: Dict[str, Any] = dict()

    def __new__(cls, json: GeoJSONType):
        type_ = Relation.subclasses[json["type"]]
        if cls in Relation.subclasses.values():
            return super().__new__(cls, json)
        else:
            return type_.__new__(type_, json)

    @classmethod
    def __init_subclass__(cls):
        super().__init_subclass__()
        Relation.subclasses[cls.__name__.lower()] = cls
