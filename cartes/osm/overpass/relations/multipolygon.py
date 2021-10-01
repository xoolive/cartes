import itertools
import logging
from operator import itemgetter

from shapely.geometry import Polygon
from shapely.geometry.collection import GeometryCollection
from shapely.geometry.multilinestring import MultiLineString
from shapely.ops import linemerge, unary_union

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

        if "outer" not in parts:  # LEBL
            logging.warning(f"Invalid geometry with id {json['id_']}")
            self.json["geometry"] = self.shape = GeometryCollection()
            return

        if isinstance(parts["outer"], MultiLineString):  # LFPO
            parts["outer"] = linemerge(parts["outer"])

        if parts.get("inner", None) and not isinstance(  # EDDF
            parts["inner"], MultiLineString
        ):
            parts["inner"] = [parts["inner"]]

        msg = (
            f"Error parsing multigeometry with id {json['id_']}. "
            "Falling back to Polygon without holes."
        )
        try:
            self.shape = Polygon(
                shell=parts["outer"], holes=parts.get("inner", None)
            )
            self.json["geometry"] = self.shape
        except NotImplementedError:
            logging.warning(msg)
            try:
                self.shape = unary_union(
                    list(Polygon(part) for part in parts["outer"])
                )
                self.json["geometry"] = self.shape
            except ValueError:
                logging.warning(f"Invalid geometry with id {json['id_']}")
                self.json["geometry"] = self.shape = GeometryCollection()

        except ValueError:  # YSSY
            logging.warning(msg)
            self.shape = Polygon(shell=parts["outer"])
            self.json["geometry"] = self.shape


class Building(MultiPolygon):
    """Should be deprecated."""
