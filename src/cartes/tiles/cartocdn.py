from cartopy.io.img_tiles import GoogleTiles

from .cached import Cache


class Basemaps(Cache, GoogleTiles):
    extension = ".png"

    def __init__(self, variant):
        self.variant = variant
        super().__init__(variant=variant)

    def _image_url(self, tile):
        x, y, z = tile
        return f"https://basemaps.cartocdn.com/{self.variant}/{z}/{x}/{y}.png"
