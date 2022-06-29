from __future__ import annotations

from abc import ABC, abstractproperty
from typing import TYPE_CHECKING, Any, Iterator, Tuple

from cartopy.crs import Orthographic

import pandas as pd
from pyproj import Proj, Transformer
from shapely.geometry import base, shape
from shapely.ops import transform

if TYPE_CHECKING:
    from ipyleaflet import Map, Marker, Polygon, Polyline


class GeoObject(ABC):
    @abstractproperty
    def __geo_interface__(self):
        return 0

    @classmethod
    def __subclasshook__(cls, C):
        if cls is GeoObject:
            if any("__geo_interface__" in B.__dict__ for B in C.__mro__):
                return True
        return NotImplemented

    @property
    def shape(self) -> base.BaseGeometry:
        return shape(self.__geo_interface__)

    @property
    def ortho_shape(self):
        shape_ = shape(self)
        lon, lat = shape_.centroid.coords[0]
        proj = Orthographic(lon, lat)
        transformer = Transformer.from_proj(
            Proj("EPSG:4326"), Proj(proj.proj4_init), always_xy=True
        )
        return transform(transformer.transform, shape_)

    @property
    def equivalent_shape(self):
        shape_ = shape(self)
        bounds = self.bounds
        proj = Proj(
            proj="aea",  # equivalent projection
            lat_1=bounds[1],
            lat_2=bounds[3],
            lat_0=(bounds[1] + bounds[3]) / 2,
            lon_0=(bounds[0] + bounds[2]) / 2,
        )

        transformer = Transformer.from_proj(
            Proj("EPSG:4326"), proj, always_xy=True
        )
        return transform(transformer.transform, shape_)

    @property
    def area(self) -> float:
        return self.equivalent_shape.area

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        return self.shape.bounds

    @property
    def extent(self) -> Tuple[float, float, float, float]:
        west, south, east, north = self.bounds
        return west, east, south, north

    @property
    def _geom(self):
        # convenient for cascaded_union
        return self.shape._geom

    @property
    def type(self):
        # convenient for intersections, etc.
        return self.shape.type

    def _repr_svg_(self):
        return self.ortho_shape._repr_svg_()

    def valid_crs(self) -> pd.DataFrame:
        from .crs.info import valid_crs

        return valid_crs(self)

    def zoom_level(self) -> int:
        x1, y1, x2, y2 = self.bounds

        if x1 == x2:
            return 17

        def func(n):
            factor = (360 * 2**-n) / (x2 - x1)
            if factor < 1:
                return 1 / factor
            return factor

        return min(range(20), key=func)

    def leaflet(
        self, **kwargs: Any
    ) -> None | "Polygon" | "Polyline" | "Marker":
        """Returns a Leaflet layer to be directly added to a Map.

        .. warning::
            This is only available if the Leaflet `plugin <plugins.html>`_ is
            activated. (true by default)

        The elements passed as kwargs as passed as is to the Polygon __init__
        method.
        """
        from ipyleaflet import Marker, Polygon, Polyline

        kwargs = {**dict(weight=3), **kwargs}
        coords: list[Any] = []

        def unfold(shape: Any) -> Iterator[Any]:
            yield shape.exterior
            yield from shape.interiors

        if self.shape.geom_type == "Polygon":
            coords = list(
                list((lat, lon) for (lon, lat, *_) in x.coords)
                for x in unfold(self.shape)
            )
            return Polygon(locations=coords, **kwargs)
        if self.shape.geom_type == "MultiPolygon":
            coords = list(
                list((lat, lon) for (lon, lat, *_) in x.coords)
                for piece in self.shape.geoms
                for x in unfold(piece)
            )
            return Polygon(locations=coords, **kwargs)
        if self.shape.geom_type == "LineString":
            return Polyline(
                locations=list((lat, lon) for (lon, lat) in self.shape.coords),
                **kwargs,
            )
        if self.shape.geom_type == "MultiLineString":
            return Polyline(
                locations=list(
                    list((lat, lon) for (lon, lat) in piece.coords)
                    for piece in self.shape.geoms
                ),
                **kwargs,
            )
        if self.shape.geom_type == "Point":
            (lon, lat), *_ = self.shape.coords
            return Marker(location=(lat, lon), **kwargs)

        return None

    def map_leaflet(self, **kwargs) -> "Map":
        from ipyleaflet import Map

        x1, y1, x2, y2 = self.bounds
        m = Map(
            center=(0.5 * (y1 + y2), 0.5 * (x1 + x2)), zoom=self.zoom_level()
        )

        layer = self.leaflet(**kwargs)
        if layer is not None:
            m.add_layer(layer)

        return m
