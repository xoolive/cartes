import itertools
from operator import itemgetter

from shapely.ops import linemerge, unary_union

from .. import Overpass
from ..core import Relation


class Waterway(Relation):
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

        elements = [linemerge(parts.get("main_stream", parts.get("")))]
        side_stream = parts.get("side_stream", None)
        if side_stream is not None:
            elements.append(linemerge(side_stream))

        self.json["geometry"] = self.shape = unary_union(elements)
