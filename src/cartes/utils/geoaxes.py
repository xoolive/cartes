from __future__ import annotations

from typing import Any

import geopandas as gpd
from cartopy.crs import PlateCarree, Projection
from cartopy.img_transform import mesh_projection
from cartopy.mpl.geoaxes import GeoAxesSubplot

import numpy as np
from pyproj import Proj, Transformer
from shapely.geometry import Polygon, box
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform

from ..core import GeoObject
from ..osm import Nominatim
from ..utils.geometry import fix_geodataframe

# We patch the set_extent method to use GeoObjects instead.


def _set_extent(self, shape, crs: None | Any = None, buffer: float = 0.01):
    if isinstance(shape, str):
        shape = Nominatim.search(shape)
    if isinstance(shape, GeoObject):
        x1, x2, y1, y2 = shape.extent
        extent = (x1 - buffer, x2 + buffer, y1 - buffer, y2 + buffer)
        return self._set_extent(extent, crs=crs)
    return self._set_extent(shape, crs=crs)


def set_square_ratio(self, crs: None | Any = None) -> None:
    if crs is None:
        crs = PlateCarree()
    bbox = self.get_extent(crs=crs)
    lon_range = bbox[1] - bbox[0]
    lat_range = bbox[3] - bbox[2]
    aspect_ratio = lon_range / lat_range

    # Adjust the extent to make the aspect ratio 1:1
    if aspect_ratio > 1:
        center_lat = (bbox[3] + bbox[2]) / 2
        lat_range = lon_range
        new_extent = [
            bbox[0],
            bbox[1],
            center_lat - lat_range / 2,
            center_lat + lat_range / 2,
        ]
    else:
        center_lon = (bbox[1] + bbox[0]) / 2
        lon_range = lat_range
        new_extent = [
            center_lon - lon_range / 2,
            center_lon + lon_range / 2,
            bbox[2],
            bbox[3],
        ]

    # Set the new extent to achieve a 1:1 aspect ratio
    self.set_extent(new_extent, crs)


GeoAxesSubplot._set_extent = GeoAxesSubplot.set_extent
GeoAxesSubplot.set_extent = _set_extent
GeoAxesSubplot.set_square_ratio = set_square_ratio


def make_polygon(projection, x1, x2, y1, y2):
    X, Y, _extent = mesh_projection(projection, 100, 100, (x1, x2), (y1, y2))
    x = np.r_[X[:, 0], X[-1, 1:], X[-2::-1, -1], X[0, -2::-1]].tolist()
    y = np.r_[Y[:, 0], Y[-1, 1:], Y[-2::-1, -1], Y[0, -2::-1]].tolist()
    return Polygon(list(zip(x, y)))


def gpd_extent(
    gdf: gpd.GeoDataFrame,
    shape,
    projection: Projection | None = None,
    buffer: float = 0.01,
) -> BaseGeometry:
    """Computes the intersection of all geometries in a bounding box.

    1. Creates a square boundingbox in the destination CRS (projection);
    2. Filters out geometries not intersecting the bounding box;
    3. Tentatively fix invalid geometries;
    4. Computes intersection with the projected bounding box

    """

    if isinstance(shape, str):
        shape = Nominatim.search(shape)
    if isinstance(shape, GeoObject):
        x1, x2, y1, y2 = shape.extent
        x1, x2, y1, y2 = (x1 - buffer, x2 + buffer, y1 - buffer, y2 + buffer)
    else:
        x1, x2, y1, y2 = shape

    if projection is not None:
        proj = Proj(projection.proj4_init)

        box_extent = make_polygon(projection, x1, x2, y1, y2)
        transformer = Transformer.from_proj(
            Proj("EPSG:4326"), proj, always_xy=True
        )
        projected_box = transform(transformer.transform, box_extent)

        x1, y1, x2, y2 = projected_box.bounds
        square_in_projected = make_polygon(projection, x1, x2, y1, y2)
        transformer = Transformer.from_proj(
            proj, Proj("EPSG:4326"), always_xy=True
        )
        shape_in_latlon = transform(transformer.transform, square_in_projected)
    else:
        shape_in_latlon = box(x1, y1, x2, y2)

    return (
        gdf.loc[gdf.geometry.intersects(shape_in_latlon)]
        .pipe(fix_geodataframe)
        .assign(geometry=lambda df: df.geometry.intersection(shape_in_latlon))
    )


gpd.GeoDataFrame.extent = gpd_extent
