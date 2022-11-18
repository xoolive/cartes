import itertools
import logging
from operator import itemgetter

from shapely.geometry import MultiPolygon as ShapelyMPL
from shapely.geometry import Polygon
from shapely.geometry.collection import GeometryCollection
from shapely.geometry.multilinestring import MultiLineString
from shapely.ops import linemerge, polygonize, unary_union

from .. import Overpass
from ..core import Relation

_log = logging.getLogger(__name__)


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
            (elt["ref"], elt)
            for elt in self.parent.all_members[json["id_"]]
            if elt is not None
        )

        parts = dict(
            (
                role,
                unary_union(
                    list(
                        elt["geometry"]
                        for elt in it
                        # labels do not have a geometry for instance...
                        if elt.get("geometry", None)
                    )
                ),
            )
            for role, it in itertools.groupby(
                parsed_keys.values(), key=itemgetter("role")
            )
        )

        if "outer" not in parts:  # LEBL: Terminal 2
            msg = f"Invalid geometry with id {json['id_']}: no outer element"
            _log.warning(msg)
            self.json["geometry"] = self.shape = GeometryCollection()
            return

        if isinstance(parts["outer"], ShapelyMPL):
            parts["outer"] = unary_union(
                list(Polygon(part) for part in parts["outer"].geoms)
            )

        if isinstance(parts["outer"], MultiLineString):  # LFPO, LFPG
            parts["outer"] = linemerge(parts["outer"])
            if isinstance(parts["outer"], MultiLineString):  # again, give up...
                self.json["geometry"] = ShapelyMPL(polygonize(parts["outer"]))
                self.shape = self.json["geometry"]
                return

        if parts.get("inner", None):
            if isinstance(parts["inner"], MultiLineString):
                parts["inner"] = parts["inner"].geoms
            else:  # EDDF
                # LineString has not attribute geoms...
                parts["inner"] = [parts["inner"]]

        msg = (
            f"Error parsing multigeometry with id {json['id_']}. "
            "Falling back to Polygon without holes."
        )
        try:
            self.shape = Polygon(
                shell=getattr(parts["outer"], "geoms", parts["outer"]),
                holes=parts.get("inner", None),
            )
            self.json["geometry"] = self.shape

        except Exception as msg:
            _log.warning(
                f"Error parsing multigeometry with id {json['id_']}: {msg} "
            )
            self.json["geometry"] = self.shape = GeometryCollection()


class Building(MultiPolygon):
    """Should be deprecated."""
