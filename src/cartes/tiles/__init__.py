from cartopy.io.img_tiles import GoogleTiles as _GoogleTiles

from .cached import Cache
from .cartocdn import Basemaps


class GoogleTiles(Cache, _GoogleTiles):
    pass


__all__ = ["GoogleTiles", "Basemaps"]
