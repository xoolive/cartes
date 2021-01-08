import geopandas as gpd
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import linemerge

from ..utils.geometry import reorient


def to_geometry(elt):
    nodes = elt.get("nodes", None)
    shape_ = LineString if nodes is None or nodes[0] != nodes[-1] else Polygon
    return reorient(shape_(list((p["lon"], p["lat"]) for p in elt["geometry"])))


def parse_nodes(res):
    return gpd.GeoDataFrame.from_records(
        list(
            dict(
                id_=elt["id"],
                type_=elt["type"],
                latitude=elt["lat"],
                longitude=elt["lon"],
                geometry=Point(elt["lon"], elt["lat"]),
                **elt["tags"],
            )
            for elt in res["elements"]
            if elt["type"] == "node" and elt.get("tags", None)
        )
    )


def parse_ways(riv, process_geom=None):
    if process_geom is None:

        def process_geom(shape):
            return shape

    return gpd.GeoDataFrame.from_records(
        list(
            dict(
                id_=elt["id"],
                type_=elt["type"],
                nodes=elt["nodes"],
                geometry=process_geom(to_geometry(elt)),
                **elt["tags"],
            )
            for elt in riv["elements"]
            if elt["type"] == "way" and elt.get("tags", None)
        )
    )


def parse_relations(res, process_geom=None):
    if process_geom is None:

        def process_geom(shape):
            return shape

    return gpd.GeoDataFrame.from_records(
        list(
            dict(
                id_=elt["id"],
                type_=elt["type"],
                members=list(
                    m["ref"] for m in elt["members"] if m["type"] == "way"
                ),
                geometry=linemerge(
                    list(
                        process_geom(to_geometry(m))
                        for m in elt["members"]
                        if m["type"] == "way"
                    )
                ),
                **elt["tags"],
            )
            for elt in res["elements"]
            if elt["type"] == "relation" and elt.get("tags", None)
        )
    )
