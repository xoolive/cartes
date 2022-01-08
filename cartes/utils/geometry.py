from typing import Dict

import geopandas as gpd

from pyproj import Proj, Transformer
from shapely.geometry import MultiPolygon, Polygon, base, polygon
from shapely.ops import polygonize, transform


def reorient(shape: base.BaseGeometry, orientation=-1) -> base.BaseGeometry:
    if isinstance(shape, Polygon):
        return polygon.orient(shape, orientation)
    if isinstance(shape, MultiPolygon):
        return MultiPolygon(reorient(p) for p in shape.geoms)
    return shape


def simplify(
    shape: base.BaseGeometry, resolution: float, bounds: Dict[str, float]
) -> base.BaseGeometry:
    """Geometric shape simplification.

    Projects a given geometry to an equivalent projection before calling the
    usual Douglas-Peucker simplification.

    Reference: https://shapely.readthedocs.io/en/stable/manual.html#object.simplify
    """
    proj = Proj(
        proj="aea",  # equivalent projection
        lat_1=bounds["minlat"],
        lat_2=bounds["maxlat"],
        lat_0=(bounds["minlat"] + bounds["maxlat"]) / 2,
        lon_0=(bounds["minlon"] + bounds["maxlon"]) / 2,
    )
    transformer_fwd = Transformer.from_proj(
        Proj("EPSG:4326"), proj, always_xy=True
    )
    transformer_back = Transformer.from_proj(
        proj, Proj("EPSG:4326"), always_xy=True
    )
    return transform(
        transformer_back.transform,
        transform(transformer_fwd.transform, shape).simplify(resolution),
    )


def fix_polygon(elt: base.BaseGeometry) -> MultiPolygon:
    """Tentative to fix an invalid (multi)polygon."""
    return MultiPolygon(list(polygonize(elt)))


def fix_geodataframe(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Fix (in place) geometries in a GeoDataFrame."""
    gdf = gdf.copy()
    if ~gdf.is_valid.sum():
        fixed = gdf.loc[~gdf.is_valid, "geometry"].apply(fix_polygon)
        gdf.loc[~gdf.is_valid, "geometry"] = fixed
    return gdf
