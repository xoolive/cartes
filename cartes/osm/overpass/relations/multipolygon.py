import itertools
from operator import itemgetter

from shapely.geometry import Polygon
from shapely.ops import unary_union

from .. import Overpass
from ..core import Relation


class MultiPolygon(Relation):
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
