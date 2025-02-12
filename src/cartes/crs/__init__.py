# type: ignore

"""
This module provides facilities for producing CRS projections.

All projections defined here are simple aliases of official EPSG definitions.
Definitions are parsed and dispatched to inherit from the proper Cartopy CRS
classes. Sometimes, there seems to be errors in the bounding boxes so there
are adjustments below, overwriting the boundind boxes as class attributes.

>>> Lambert93().proj4_init
'+ellps=GRS80 +proj=lcc +lon_0=3 +lat_0=46.5 +x_0=700000 ...'

>>> LCCEurope().bbox
{'south_latitude': 24.6...}

>>> LCCEurope().proj4_params
{'ellps': 'GRS80', 'proj': 'lcc', ...}

"""

# fmt: off
import warnings
from typing import ClassVar, TypedDict

# All projections first come from the regular Cartopy CRS module
from cartopy.crs import (
    Globe,
    InterruptedGoodeHomolosine,
    LambertCylindrical,
    Miller,
    Projection,
    Robinson,
    RotatedPole,
    Sinusoidal,
)

from . import meta
from .info import valid_crs  # noqa: F401

# These ones can be unpacked in altair!
from .vega_params import (
    OSGB,
    OSNI,
    UTM,
    AlbersEqualArea,
    AzimuthalEquidistant,
    EqualEarth,
    EquidistantConic,
    EuroPP,
    Gnomonic,
    LambertAzimuthalEqualArea,
    LambertConformal,
    Mercator,
    Mollweide,
    Orthographic,
    PlateCarree,
    Stereographic,
    TransverseMercator,
)

# fmt: on

__all__ = [
    "OSGB",
    "OSNI",
    "RDN2008",
    "UTM",
    "AlbersEqualArea",
    "AlbersUSA",
    "AzimuthalEquidistant",
    "EqualEarth",
    "EquidistantConic",
    "EuroPP",
    "GaussKrueger",
    "GaussKruger",
    "Globe",
    "Gnomonic",
    "Hartebeesthoek94",
    "InterruptedGoodeHomolosine",
    "LambertAzimuthalEqualArea",
    "LambertConformal",
    "LambertCylindrical",
    "Mercator",
    "Miller",
    "Mollweide",
    "Orthographic",
    "PlateCarree",
    "Projection",
    "Robinson",
    "RotatedPole",
    "Sinusoidal",
    "Stereographic",
    "TransverseMercator",
]

# Silence a fiona warning
warnings.simplefilter(action="ignore", category=UserWarning)


class BBoxType(TypedDict):
    east_longitude: float
    north_latitude: float
    south_latitude: float
    west_longitude: float


# Official projection in Switzerland
CH1903p = meta.EPSG_2056

# Official projection in France
Lambert93 = meta.EPSG_2154


# Official projection in Sweden (adjusted to the whole country)
# This record seems to be centered on Stockholm agglomeration
class ST74(meta.EPSG_3152):
    bbox: ClassVar[BBoxType] = {
        "east_longitude": 24.17,
        "north_latitude": 69.07,
        "south_latitude": 54.96,
        "west_longitude": 10.03,
    }


# Official projection in Japan (adjusted to the whole country)
class JGD2000(meta.EPSG_2451):
    bbox: ClassVar[BBoxType] = {
        "east_longitude": 157.65,
        "north_latitude": 46.05,
        "south_latitude": 17.09,
        "west_longitude": 122.38,
    }


# Official projection in the Netherlands
Amersfoort = meta.EPSG_28992

# Lambert projection of Europe
LCCEurope = meta.EPSG_3034

# Official projection in Australia
GeoscienceAustraliaLambert = meta.EPSG_3112


# Official projection in Canada
# Bounding box adjusted because of strong distortions
class StatisticsCanadaLambert(meta.EPSG_3348):
    bbox: ClassVar[BBoxType] = {
        "east_longitude": -50.0,
        "north_latitude": 85.0,
        "south_latitude": 32.0,
        "west_longitude": -131.1,
    }


# Official projection in Singapore
SingaporeTM = meta.EPSG_3414

# Official projection in New Zealand
NZGD2000 = meta.EPSG_3851

# Official projection in Korea
Korea2000 = meta.EPSG_5179


# Official projection in Latin America
class SIRGAS2000(meta.EPSG_5641):
    bbox: ClassVar[BBoxType] = {
        "east_longitude": -25.28,
        "north_latitude": 32.72,
        "south_latitude": -59.87,
        "west_longitude": -122.19,
    }


# Official projection in Germany
class GaussKruger(meta.EPSG_5680):
    bbox: ClassVar[BBoxType] = {
        "east_longitude": 15.0,
        "north_latitude": 55.09,
        "south_latitude": 47.27,
        "west_longitude": 5.87,
    }


GaussKrueger = GaussKruger

# Official projection of the United States
AlbersUSA = meta.EPSG_6350

# Official projection in Italy
RDN2008 = meta.EPSG_6875

# Official projection in South Africa
Hartebeesthoek94 = meta.EPSG_9221


def __getattr__(name: str) -> Projection:
    return getattr(meta, name)
