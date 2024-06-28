from fastapi import FastAPI
from fastapi.responses import FileResponse

from . import Basemaps, GoogleTiles

app = FastAPI()

providers = {"google": GoogleTiles(), "light_all": Basemaps("light_all")}


@app.get("/{style}/{z}/{x}/{y}")
async def get_image(style, z: int, x: int, y: int):
    *_, path = await providers[style].get_image((x, y, z))

    return FileResponse(path)


def main():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=4321)
