from abc import ABC, abstractproperty
from typing import Tuple

import pandas as pd
from cartopy.crs import Orthographic
from pyproj import Proj, Transformer
from shapely.geometry import base, shape
from shapely.ops import transform


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
