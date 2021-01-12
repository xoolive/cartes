import itertools
from collections import UserDict
from operator import itemgetter
from typing import Dict, Iterator, Set, Tuple, Union, cast

from shapely.geometry import MultiLineString
from shapely.geometry.base import BaseGeometry
from shapely.ops import linemerge, unary_union

from .. import Overpass
from ....utils.cache import cached_property
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
        self.shape = linemerge(
            # TODO par category
            list((chunk) for chunk in self.known_chunks["outer"])
        )
        self.json["geometry"] = self.shape

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
