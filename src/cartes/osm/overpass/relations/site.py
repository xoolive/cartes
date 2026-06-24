from shapely.geometry.collection import GeometryCollection
from shapely.ops import polygonize, unary_union

from ....utils.geometry import reorient
from .. import Overpass
from ..core import Relation


class Site(Relation):
    """A class to parse type=site relations.

    Site relations group objects that have a single identity as a whole but
    may include area, point and linear members. They are not multipolygons:
    members are collected by their own geometry instead of being interpreted
    through outer/inner roles.

    Reference: https://wiki.openstreetmap.org/wiki/Relation:site
    """

    def __init__(self, json):
        super().__init__(json)

        self.parent: Overpass = json["_parent"]
        geometries = [
            self._polygonize(elt["geometry"])
            for elt in self.parent.all_members[json["id_"]]
            if elt.get("geometry", None) is not None
        ]

        self.shape = self._collect(geometries)
        self.json["geometry"] = self.shape

    @staticmethod
    def _polygonize(geometry):
        if geometry.geom_type not in {"LineString", "MultiLineString"}:
            return geometry

        polygons = list(polygonize(geometry))
        if len(polygons) == 0:
            return geometry
        return unary_union(polygons)

    @staticmethod
    def _collect(geometries):
        groups = []
        for geometry_types in [
            {"Polygon", "MultiPolygon"},
            {"LineString", "MultiLineString"},
            {"Point", "MultiPoint"},
        ]:
            geometries_ = [
                geometry
                for geometry in geometries
                if geometry.geom_type in geometry_types
            ]
            if len(geometries_) > 0:
                groups.append(reorient(unary_union(geometries_)))

        other_geometries = [
            geometry
            for geometry in geometries
            if geometry.geom_type
            not in {
                "Polygon",
                "MultiPolygon",
                "LineString",
                "MultiLineString",
                "Point",
                "MultiPoint",
            }
        ]
        groups.extend(other_geometries)

        if len(groups) == 0:
            return GeometryCollection()
        if len(groups) == 1:
            return groups[0]
        return GeometryCollection(groups)
