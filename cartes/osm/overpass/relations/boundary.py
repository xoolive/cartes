import itertools
from collections import UserDict
from operator import itemgetter
from typing import Dict, Iterator, Set, Tuple, Union, cast

from pyproj import Proj, Transformer
from shapely.geometry import LineString, MultiLineString, MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import linemerge, transform, unary_union

from .. import Overpass
from ....utils.cache import cached_property
from ....utils.geometry import reorient
from ..core import Relation


class RelationsDict(UserDict):
    def __missing__(self, key):
        value = self[key] = list()
        return value

    def include(self, chunk: BaseGeometry, role: str):
        if isinstance(chunk, MultiLineString):
            for c in chunk:
                self[role].append(c)
        else:
            self[role].append(chunk)


class Boundary(Relation):
    def __init__(self, json):

        super().__init__(json)

        self.known_chunks = RelationsDict()
        self.parent: Overpass = json["_parent"]

        self.parsed_keys = cast(
            Dict[int, Dict[str, Union[int, str]]],
            dict(
                (elt["ref"], elt)
                for elt in self.parent.all_members[self.json["id_"]]
            ),
        )

        self._build_geometry_parts()
        self._make_geometry(self.known_chunks)

    def simplify(self, resolution: float) -> "Boundary":
        bounds = self.parent.bounds

        def simplify_shape(shape_: BaseGeometry) -> BaseGeometry:
            proj = Proj(
                proj="aea",  # equivalent projection
                lat_1=bounds[1],
                lat_2=bounds[3],
                lat_0=(bounds[1] + bounds[3]) / 2,
                lon_0=(bounds[0] + bounds[2]) / 2,
            )

            forward = Transformer.from_proj(
                Proj("EPSG:4326"), proj, always_xy=True
            )
            backward = Transformer.from_proj(
                proj, Proj("EPSG:4326"), always_xy=True
            )
            return transform(
                backward.transform,
                transform(forward.transform, shape_).simplify(resolution),
            )

        rel_dict = RelationsDict()
        for role, shapes in self.known_chunks.items():
            for elt in shapes:
                rel_dict.include(simplify_shape(elt), role)

        self._make_geometry(rel_dict)
        return self

    def _make_geometry(self, parts: RelationsDict):

        outer = linemerge(parts["outer"])
        inner = linemerge(parts["inner"])

        if isinstance(outer, MultiLineString):
            if isinstance(inner, MultiLineString):
                list_ = [
                    Polygon(
                        o,
                        holes=list(i for i in inner if Polygon(o).contains(i)),
                    )
                    for o in outer
                ]
                shape = MultiPolygon(list_)
            else:
                list_ = [
                    Polygon(
                        o,
                        holes=[inner] if Polygon(o).contains(inner) else None,
                    )
                    for o in outer
                ]
                shape = MultiPolygon(list_)
        else:
            if isinstance(inner, LineString):
                shape = Polygon(outer, [inner])
            else:
                shape = Polygon(outer, inner)

        self.json["geometry"] = self.shape = reorient(shape)

    def intersections(self) -> Iterator[Tuple[int, Set[int]]]:
        all_sets: Dict[int, Set[int]] = dict(
            (key, set(e["ref"] for e in list_))
            for key, list_ in self.parent.all_members.items()
        )
        key_i = self.json["id_"]
        set_i = all_sets[key_i]
        for key_j, set_j in all_sets.items():
            if key_i == key_j:
                continue
            intersection = set_i.intersection(set_j)
            if len(intersection) > 0:
                yield key_j, intersection

    @cached_property
    def neighbours(self) -> Set[int]:
        return set(key for key, _value in self.intersections())

    def include(self, elements: Set[int]) -> None:
        for role, it in itertools.groupby(
            (self.parsed_keys[key] for key in elements), key=itemgetter("role")
        ):
            elts = list(elt["geometry"] for elt in it)
            chunk = unary_union(elts)
            self.known_chunks.include(chunk, role)

    def _build_geometry_parts(self) -> BaseGeometry:

        all_: Set[int] = set(self.parsed_keys.keys())

        for _id, intersection in self.intersections():
            self.include(intersection)
            all_ -= intersection

        self.include(all_)


# Forcing the inheritance for proper registration
class Land_Area(Boundary):
    pass
