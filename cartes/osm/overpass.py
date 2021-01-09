from typing import Callable, Optional

import geopandas as gpd
from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import polygonize_full

from ..utils.geometry import reorient
from .requests import JSONType


def identity(elt, *args, **kwargs):
    return elt


def to_geometry(elt: JSONType) -> BaseGeometry:
    nodes = elt.get("nodes", None)
    if nodes is not None:
        assert isinstance(nodes, list)
    shape = LineString if nodes is None else Polygon
    return reorient(shape(list((p["lon"], p["lat"]) for p in elt["geometry"])))


def merge_geometries(
    elt: JSONType,
    process_geom: Optional[Callable[[BaseGeometry], BaseGeometry]] = None,
) -> BaseGeometry:
    if process_geom is None:
        process_geom = identity

    polygons_outer, dangles, cut_edges, invalid_ring_lines = polygonize_full(
        list(
            process_geom(to_geometry(m))
            for m in elt["members"]
            if m["type"] == "way" and m["role"] == "outer"
        )
    )
    polygons_inner, dangles, cut_edges, invalid_ring_lines = polygonize_full(
        list(
            process_geom(to_geometry(m))
            for m in elt["members"]
            if m["type"] == "way" and m["role"] == "inner"
        )
    )

    # DEBUG find a better hack
    outer = list(p for p in polygons_outer if p.area > 1e-5)
    inner = tuple(p for p in polygons_inner if p.area > 1e-5)

    return MultiPolygon(
        [
            Polygon(
                list(o.exterior.coords),
                [tuple(i.exterior.coords) for i in inner if o.intersects(i)],
            )
            for o in outer
        ]
    )


def parse_nodes(result: JSONType) -> gpd.GeoDataFrame:
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
            for elt in result["elements"]
            if elt["type"] == "node" and elt.get("tags", None)
        )
    )


def parse_ways(
    result: JSONType,
    process_geom: Optional[Callable[[BaseGeometry], BaseGeometry]] = None,
) -> gpd.GeoDataFrame:
    if process_geom is None:
        process_geom = identity

    return gpd.GeoDataFrame.from_records(
        list(
            dict(
                id_=elt["id"],
                type_=elt["type"],
                nodes=elt["nodes"],
                geometry=process_geom(to_geometry(elt)),
                **elt["tags"],
            )
            for elt in result["elements"]
            if elt["type"] == "way" and elt.get("tags", None)
        )
    )


def parse_relations(
    results: JSONType,
    process_geom: Optional[Callable[[BaseGeometry], BaseGeometry]] = None,
):
    if process_geom is None:
        process_geom = identity

    return gpd.GeoDataFrame.from_records(
        list(
            dict(
                id_=elt["id"],
                type_=elt["type"],
                members=list(
                    m["ref"] for m in elt["members"] if m["type"] == "way"
                ),
                geometry=merge_geometries(elt, process_geom=process_geom),
                **elt["tags"],
            )
            for elt in results["elements"]
            if elt["type"] == "relation" and elt.get("tags", None)
        )
    )
