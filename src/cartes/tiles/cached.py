import asyncio
import os
from pathlib import Path

import httpx
import nest_asyncio
from appdirs import user_cache_dir
from cartopy.io.img_tiles import _merge_tiles
from PIL import Image

import numpy as np
from cartes import __version__

nest_asyncio.apply()

async_client = httpx.AsyncClient(
    http2=True,
    follow_redirects=True,
)

global_cache_dir = Path(user_cache_dir("cartes")) / "tiles"
if not global_cache_dir.is_dir():
    global_cache_dir.mkdir(parents=True)


class Cache(object):
    extension = ".jpg"

    def __init__(self, *args, **kwargs):
        self.params = {}

        tileset_name = "{}".format(self.__class__.__name__.lower())

        self.cache_directory = global_cache_dir / tileset_name

        if "style" in kwargs:
            self.cache_directory /= kwargs["style"]

        if "variant" in kwargs:
            self.cache_directory /= kwargs["variant"]
            del kwargs["variant"]

        if not self.cache_directory.is_dir():
            self.cache_directory.mkdir(parents=True)

        super().__init__(*args, **kwargs)

    async def get_image(self, tile):
        tile_fname = self.cache_directory / (
            "_".join(str(v) for v in tile) + self.extension
        )

        if not os.path.exists(tile_fname):
            response = await async_client.get(
                self._image_url(tile),  # type: ignore
                headers={"User-Agent": f"cartes {__version__}"},
            )
            response.raise_for_status()
            tile_fname.write_bytes(response.content)

        with open(tile_fname, "rb") as fh:
            img = Image.open(fh)
            img = img.convert(self.desired_tile_form)  # type: ignore

        return img, self.tileextent(tile), "lower", tile_fname  # type: ignore

    async def one_image(self, tile):
        img, extent, origin, _ = await self.get_image(tile)
        img = np.array(img)
        x = np.linspace(extent[0], extent[1], img.shape[1])
        y = np.linspace(extent[2], extent[3], img.shape[0])
        return [img, x, y, origin]

    async def all_images(self, target_domain, target_z):
        return await asyncio.gather(
            *[
                self.one_image(tile)
                for tile in self.find_images(target_domain, target_z)  # type: ignore
            ]
        )

    def image_for_domain(self, target_domain, target_z):
        tiles = asyncio.run(self.all_images(target_domain, target_z))

        img, extent, origin = _merge_tiles(tiles)
        return img, extent, origin
