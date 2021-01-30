import importlib_metadata

# Monkey-patches GeoAxesSubplot for .set_extent()
from .utils import geoaxes  # noqa: F401

__version__ = importlib_metadata.version("cartes")
