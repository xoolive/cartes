# fmt: off

import inspect
import logging
import pprint
from abc import ABCMeta
from typing import Any, Dict, List

from cartopy.crs import (
    UTM, AlbersEqualArea, AzimuthalEquidistant, EqualEarth,
    EquidistantConic, Globe, Gnomonic, InterruptedGoodeHomolosine,
    LambertAzimuthalEqualArea, LambertConformal, LambertCylindrical,
    Mercator, Miller, Mollweide, Orthographic, Projection, Robinson,
    RotatedPole, Sinusoidal, Stereographic, TransverseMercator
)
from pyproj import CRS, Proj, Transformer
from shapely import geometry
from shapely.ops import transform

# fmt:on

base_classes: Dict["str", Projection] = {
    "lcc": LambertConformal,
    "laea": LambertAzimuthalEqualArea,
    "aea": AlbersEqualArea,
    "tmerc": TransverseMercator,
    "utm": UTM,
    "merc": Mercator,
    "cea": LambertCylindrical,
    "mill": Miller,
    "ob_tran": RotatedPole,  # or RotatedGeometric...
    "gnom": Gnomonic,
    "stere": Stereographic,
    "ortho": Orthographic,
    "eqearth": EqualEarth,
    "moll": Mollweide,
    "robin": Robinson,
    "igh": InterruptedGoodeHomolosine,
    "aeqd": AzimuthalEquidistant,
    "sinu": Sinusoidal,
    "eqdc": EquidistantConic,
}

arg_codes = {
    8801: "central_latitude",
    8802: "central_longitude",
    8803: "standard_parallel_1",
    8804: "standard_parallel_2",
    8805: "scale_factor",
    8806: "false_easting",
    8807: "false_northing",
    8821: "central_latitude",
    8822: "central_longitude",
    8823: "standard_parallel_1",
    8824: "standard_parallel_2",
    8825: "scale_factor",
    8826: "false_easting",
    8827: "false_northing",
}


class EPSGProjectionMeta(ABCMeta):
    @staticmethod
    def init_args(parameters: List[Dict[str, Any]], proj: Projection):
        all_ = dict(
            (arg_codes[elt["id"]["code"]], elt["value"]) for elt in parameters
        )
        if "standard_parallel_1" in all_ and "standard_parallel_2" in all_:
            all_["standard_parallels"] = (
                all_.pop("standard_parallel_1"),
                all_.pop("standard_parallel_2"),
            )
        # Get the arguments for the selected CRS projection
        init_args = inspect.getargs(proj.__init__.__code__).args
        remove_args = list(
            key for key, _value in all_.items() if key not in init_args
        )

        for key in remove_args:
            logging.warning(f"argument '{key}' ignored")
            del all_[key]

        return all_

    @staticmethod
    def projected_shape(bbox: Dict[str, float], transformer):
        y0 = bbox["south_latitude"]
        x0 = bbox["east_longitude"]
        y1 = bbox["north_latitude"]
        x1 = bbox["west_longitude"]

        return transform(
            transformer.transform,
            geometry.LineString(
                [(x0, y0), (x0, y1), (x1, y1), (x1, y0), (x0, y0)]
            ),
        )

    def __new__(metacls, name, bases, attr_dict):
        identifier = attr_dict.get("identifier", None)
        if identifier is None:
            for base in bases:
                identifier = vars(base).get("identifier", None)
                if identifier is not None:
                    break
            else:  # not found
                raise TypeError("No identifier in class or parent classes.")

        crs = CRS(identifier)
        basic_dict = crs.to_dict()
        logging.debug(pprint.pformat(basic_dict))
        base_class = base_classes.get(basic_dict["proj"], Projection)
        logging.debug(f"Generate a class based on {base_class.__name__}")

        transformer = Transformer.from_proj(
            Proj("epsg:4326"), Proj(crs), always_xy=True
        )
        attr_dict = {**crs.to_json_dict(), **attr_dict}
        logging.debug(f"Based on {pprint.pformat(attr_dict)}")

        if base_class is Projection:
            attr_dict["threshold"] = 1e4

        def __init__(self):
            if base_class is Projection:
                return Projection.__init__(self, crs.to_dict())

            ellipse = basic_dict.get("ellps", None)
            if ellipse is not None:
                globe = Globe(ellipse=ellipse)
            else:
                a, rf = basic_dict.get("a", None), basic_dict.get("rf", None)
                if a is None or rf is None:
                    msg = f"Fallback to regular Projection with {crs.to_dict()}"
                    logging.warning(msg)
                    return Projection.__init__(self, crs.to_dict())
                globe = Globe(semimajor_axis=a, inverse_flattening=rf)

            base_class.__init__(
                self,
                **EPSGProjectionMeta.init_args(
                    attr_dict["conversion"]["parameters"], base_class
                ),
                globe=globe,
            )

        attr_dict["__init__"] = __init__

        projected_shape = EPSGProjectionMeta.projected_shape(
            attr_dict["bbox"], transformer
        )

        def x_limits(self):
            x0, y0, x1, y1 = projected_shape.bounds
            return x0, x1

        attr_dict["x_limits"] = property(x_limits)

        def y_limits(self):
            x0, y0, x1, y1 = projected_shape.bounds
            return y0, y1

        attr_dict["y_limits"] = property(y_limits)

        def boundary(self):
            x0, x1 = self.x_limits
            y0, y1 = self.y_limits
            return geometry.LineString(
                [(x0, y0), (x0, y1), (x1, y1), (x1, y0), (x0, y0)]
            )

        attr_dict["boundary"] = property(boundary)

        attr_dict["projected_shape"] = projected_shape

        return super().__new__(metacls, name, (base_class,), attr_dict)


def __getattr__(name: str) -> Projection:
    if name.startswith("EPSG_"):
        return EPSGProjectionMeta(name, (), dict(identifier=f"EPSG:{name[5:]}"))

    raise AttributeError
