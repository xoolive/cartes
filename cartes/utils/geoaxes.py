from cartopy.mpl.geoaxes import GeoAxesSubplot

from ..core import GeoObject
from ..osm import Nominatim

# We patch the set_extent method to use GeoObjects instead.


def _set_extent(self, shape, buffer: float = 0.01):
    if isinstance(shape, str):
        shape = Nominatim(shape)
    if isinstance(shape, GeoObject):
        x1, x2, y1, y2 = shape.extent
        extent = (x1 - buffer, x2 + buffer, y1 - buffer, y2 + buffer)
        return self._set_extent(extent)
    self._set_extent(shape)


GeoAxesSubplot._set_extent = GeoAxesSubplot.set_extent
GeoAxesSubplot.set_extent = _set_extent
