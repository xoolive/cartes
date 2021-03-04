import itertools
from operator import itemgetter

from shapely.geometry.multilinestring import MultiLineString
from shapely.ops import linemerge, unary_union

from .. import Overpass
from ..core import Relation


class Waterway(Relation):
    """A class to parse waterway=* relations.

    The purpose of waterway relations is to have an object for each river.

    Reference: https://wiki.openstreetmap.org/wiki/Relation:waterway

    Tags:
      - type (waterway)
      - waterway [river, stream, canal, drain, ditch]
      - name (*)
      - destination ?
      - ref ?
      - ref:sandre ?
      - ref:fgkz ?
      - ...

    Relation members:
      - None or main_stream 1+
      - side_stream 0+
      - spring ?
      - tributary 0+

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
        main_stream = parts.get("main_stream", parts.get(""))
        elements = [
            linemerge(main_stream)
            if isinstance(main_stream, MultiLineString)
            else main_stream
        ]
        side_stream = parts.get("side_stream", None)
        if side_stream is not None:
            elements.append(
                linemerge(side_stream)
                if isinstance(side_stream, MultiLineString)
                else side_stream
            )

        self.json["geometry"] = self.shape = unary_union(elements)
