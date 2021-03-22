from typing import Any, Dict, Optional, Tuple, TypeVar, Union

from pyproj import Proj, Transformer
from shapely.geometry import LineString, Point, Polygon, mapping, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform

from ...core import GeoObject
from ...utils.descriptors import OrientedShape
from ...utils.geometry import reorient
from ...utils.mixins import HBoxMixin, HTMLAttrMixin, HTMLTitleMixin
from ..requests import GeoJSONType, JSONType


def to_geometry(elt: JSONType) -> BaseGeometry:
    """Builds a shapely geometry based on JSON representations.

    Parses the usual `out geom` format for geometries.

    >>> str(to_geometry({'type': 'node', 'lon': 1.5, 'lat': 43.6}))
    'POINT (1.5 43.6)'

    """
    if elt["type"] == "node":
        return Point(elt["lon"], elt["lat"])

    nodes = elt.get("nodes", None)
    if nodes is not None:
        assert isinstance(nodes, list)
    shape = LineString if nodes is None or nodes[0] != nodes[-1] else Polygon
    return reorient(shape(list((p["lon"], p["lat"]) for p in elt["geometry"])))


T = TypeVar("T", bound="NodeWayRelation")


class NodeWayRelation(GeoObject, HBoxMixin, HTMLTitleMixin, HTMLAttrMixin):
    """Common behaviour of Node, Way and Relation classes.

    This class is de facto an abstract class. Instantiating it will always
    fallback to a child class registered in `subclasses`, based on the type
    of the feature (`json["type_"]`).

    - Representation for such objects in implemented with usual mixins.
    - Default simplification is available as well.

    """

    shape = OrientedShape()
    subclasses: Dict[str, Any] = dict()
    instances: Dict[int, "NodeWayRelation"] = dict()

    def __new__(cls, json: Optional[GeoJSONType] = None):

        if json is None:
            return super().__new__(cls)

        # Singleton instances
        id_ = json["id_"]
        if id_ in NodeWayRelation.instances.keys():
            return NodeWayRelation.instances[id_]
        # Otherwise dispatch on subclasses
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

        if name in ["__getstate__", "__setstate__"]:  # security for pickling
            raise AttributeError(name)

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

    def simplify(
        self: T,
        resolution: float,
        bounds: Union[None, Tuple[float, float, float, float]] = None,
    ) -> T:

        if bounds is None:
            bounds = self.parent.bounds

        proj = Proj(
            proj="aea",  # equivalent projection
            lat_1=bounds[1],
            lat_2=bounds[3],
            lat_0=(bounds[1] + bounds[3]) / 2,
            lon_0=(bounds[0] + bounds[2]) / 2,
        )

        forward = Transformer.from_proj(Proj("EPSG:4326"), proj, always_xy=True)
        backward = Transformer.from_proj(
            proj, Proj("EPSG:4326"), always_xy=True
        )
        new = type(self)(self.json)
        new.shape = transform(
            backward.transform,
            transform(forward.transform, self.shape).simplify(resolution),
        )
        return new


class Node(NodeWayRelation):
    """Node just delegates the shape parsing to shapely."""

    def __init__(self, json: GeoJSONType):
        super().__init__(json)
        self.shape = shape(self.json["geometry"])


class Way(NodeWayRelation):
    """Way just delegates the shape parsing to shapely."""

    def __init__(self, json: GeoJSONType):
        super().__init__(json)
        self.shape = shape(self.json["geometry"])


class Relation(NodeWayRelation):
    """Common behaviour for all Relation specifications.

    This class is de facto an abstract class. Instantiating it will always
    fallback to a child class registered in `subclasses`, based on the type
    of the feature (`json["type"]`).

    - json['type_'] is node, way, or relation
    - json['type'] is the `type` key in the `tags` subdictionary
    """

    subclasses: Dict[str, Any] = dict()

    def __new__(cls, json: Optional[GeoJSONType] = None):
        if json is None:
            return super().__new__(cls, json)
        if json["type"] not in Relation.subclasses:
            msg = (
                f"The parser for {json['type'].title()} is not implemented yet."
                f"\nIf you feel enthusiastic, you may implement a class "
                f"{json['type'].title()} which inherits from Relation"
                "\nand knows how to parse this relation."
            )
            raise NotImplementedError(msg)
        type_ = Relation.subclasses[json["type"]]
        if cls in Relation.subclasses.values():
            return super().__new__(cls, json)
        else:
            return type_.__new__(type_, json)

    @classmethod
    def __init_subclass__(cls):
        super().__init_subclass__()
        Relation.subclasses[cls.__name__.lower()] = cls
