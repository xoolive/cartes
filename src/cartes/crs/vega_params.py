from typing import Any

from cartopy import crs


class AlbersEqualArea(crs.AlbersEqualArea):
    def __getitem__(self, index: str) -> Any:
        if index == "type":
            return "conicEqualArea"
        if index == "rotate":
            lat = self.proj4_params["lat_0"]
            lon = self.proj4_params["lon_0"]
            return (-lon, -lat, 0)
        if index == "parallels":
            lat_1 = self.proj4_params["lat_1"]
            lat_2 = self.proj4_params["lat_2"]
            return [lat_1, lat_2]
        raise KeyError(index)

    def keys(self):
        return ["type", "rotate", "parallels"]


class AzimuthalEquidistant(crs.AzimuthalEquidistant):
    def __getitem__(self, index: str) -> Any:
        if index == "type":
            return "azimuthalEquidistant"
        if index == "rotate":
            lat = self.proj4_params["lat_0"]
            lon = self.proj4_params["lon_0"]
            return (-lon, -lat, 0)
        raise KeyError(index)

    def keys(self):
        return ["type", "rotate"]


class EqualEarth(crs.EqualEarth):
    def __getitem__(self, index: str) -> Any:
        if index == "type":
            return "equalEarth"
        if index == "rotate":
            lon = self.proj4_params["lon_0"]
            return (-lon, 0, 0)
        raise KeyError(index)

    def keys(self):
        return ["type", "rotate"]


class EquidistantConic(crs.EquidistantConic):
    def __getitem__(self, index: str) -> Any:
        if index == "type":
            return "conicEquidistant"
        if index == "rotate":
            lat = self.proj4_params["lat_0"]
            lon = self.proj4_params["lon_0"]
            return (-lon, -lat, 0)
        if index == "parallels":
            lat_1 = self.proj4_params["lat_1"]
            lat_2 = self.proj4_params["lat_2"]
            return [lat_1, lat_2]
        raise KeyError(index)

    def keys(self):
        return ["type", "rotate", "parallels"]


class Gnomonic(crs.Gnomonic):
    def __getitem__(self, index: str) -> Any:
        if index == "type":
            return "gnomonic"
        if index == "rotate":
            lat = self.proj4_params["lat_0"]
            lon = self.proj4_params["lon_0"]
            return (-lon, -lat, 0)
        raise KeyError(index)

    def keys(self):
        return ["type", "rotate"]


class Mercator(crs.Mercator):
    def __getitem__(self, index: str) -> Any:
        if index == "type":
            return "mercator"
        if index == "rotate":
            lon = self.proj4_params["lon_0"]
            return (-lon, 0, 0)
        raise KeyError(index)

    def keys(self):
        return ["type", "rotate"]


class Mollweide(crs.Mollweide):
    def __getitem__(self, index: str) -> Any:
        if index == "type":
            return "mollweide"
        if index == "rotate":
            lon = self.proj4_params["lon_0"]
            return (-lon, 0, 0)
        raise KeyError(index)

    def keys(self):
        return ["type", "rotate"]


class LambertAzimuthalEqualArea(crs.LambertAzimuthalEqualArea):
    def __getitem__(self, index: str) -> Any:
        if index == "type":
            return "azimuthalEqualArea"
        if index == "rotate":
            lat = self.proj4_params["lat_0"]
            lon = self.proj4_params["lon_0"]
            return (-lon, -lat, 0)
        raise KeyError(index)

    def keys(self):
        return ["type", "rotate"]


class LambertConformal(crs.LambertConformal):
    def __getitem__(self, index: str) -> Any:
        if index == "type":
            return "conicConformal"
        if index == "rotate":
            lat = self.proj4_params["lat_0"]
            lon = self.proj4_params["lon_0"]
            return (-lon, -lat, 0)
        if index == "parallels":
            lat_1 = self.proj4_params["lat_1"]
            lat_2 = self.proj4_params["lat_2"]
            return [lat_1, lat_2]
        raise KeyError(index)

    def keys(self):
        return ["type", "rotate", "parallels"]


class Orthographic(crs.Orthographic):
    def __getitem__(self, index: str) -> Any:
        if index == "type":
            return "orthographic"
        if index == "rotate":
            lat = self.proj4_params["lat_0"]
            lon = self.proj4_params["lon_0"]
            return (-lon, -lat, 0)
        raise KeyError(index)

    def keys(self):
        return ["type", "rotate"]


class PlateCarree(crs.PlateCarree):
    def __getitem__(self, index: str) -> Any:
        if index == "type":
            return "equirectangular"
        raise KeyError(index)

    def keys(self):
        return ["type"]


class Stereographic(crs.Stereographic):
    def __getitem__(self, index: str) -> Any:
        if index == "type":
            return "stereographic"
        if index == "rotate":
            lat = self.proj4_params["lat_0"]
            lon = self.proj4_params["lon_0"]
            return (-lon, -lat, 0)
        raise KeyError(index)

    def keys(self):
        return ["type", "rotate"]


class TransverseMercator(crs.TransverseMercator):
    def __getitem__(self, index: str) -> Any:
        if index == "type":
            return "transverseMercator"
        if index == "rotate":
            lat = self.proj4_params["lat_0"]
            lon = self.proj4_params["lon_0"]
            return (-lon, -lat, 0)
        raise KeyError(index)

    def keys(self):
        return ["type", "rotate"]


class UTM(crs.UTM):
    def __getitem__(self, index: str) -> Any:
        if index == "type":
            return "transverseMercator"
        if index == "rotate":
            zone = self.proj4_params["zone"]
            return (-(zone * 6 - 180 - 3), 0, 0)
        raise KeyError(index)

    def keys(self):
        return ["type", "rotate"]


class EuroPP(UTM, crs.EuroPP):
    pass


class OSGB(TransverseMercator, crs.OSGB):
    pass


class OSNI(TransverseMercator, crs.OSNI):
    pass
