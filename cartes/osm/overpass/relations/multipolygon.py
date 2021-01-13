import itertools
from operator import itemgetter

from shapely.geometry import Polygon
from shapely.ops import unary_union

from .. import Overpass
from ..core import Relation


class MultiPolygon(Relation):
    """A class to parse multipolygon=* relations.

    Relations of type multipolygon are used to represent complex areas with
    holes inside or consisting of multiple disjoint areas.

    Reference: https://wiki.openstreetmap.org/wiki/Relation:multipolygon

    Tags:
      - type (multipolygon)
      - natural
      - landuse
      - building
      - man_made
      - amenity
      - leisure
      - highway (pedestrian)
      - waterway
      - ...

    Relation members:
      - outer 1+
      - inner 0+

    """

    def __init__(self, json):

        super().__init__(json)

        self.parent: Overpass = json["_parent"]
        parsed_keys = dict(
            (elt["ref"], elt) for elt in self.parent.all_members[json["id_"]]
        )

        parts = dict(
            (role, unary_union(list(elt["geometry"] for elt in it)))
            for role, it in itertools.groupby(
                parsed_keys.values(), key=itemgetter("role")
            )
        )

        self.json["geometry"] = self.shape = Polygon(
            shell=parts["outer"], holes=parts.get("inner", None)
        )
