from typing import Union

import pandas as pd
import pyproj
from shapely.geometry import shape

from ..core import GeoObject
from ..osm import Nominatim


def valid_crs(area: Union[str, GeoObject]) -> pd.DataFrame:
    """Returns a list of valid CRS according to a GeoObject."""
    if isinstance(area, str):
        candidate = Nominatim.search(area)
        if candidate is None:
            raise ValueError("No such place found.")
        area = candidate
    msg = "The argument must implement the __geo_interface__ protocol"
    if not isinstance(area, GeoObject):
        raise TypeError(msg)
    features = [
        "auth_name",  # EPSG
        "code",  # This one is of interest!
        "deprecated",  # mostly False
        "name",
        "projection_method_name",  # projection family
    ]
    return pd.DataFrame.from_records(
        list(
            {
                "area": crsinfo.area_of_use.name  # type: ignore
                # typing: explain (the hasattr catches it)
                if hasattr(crsinfo, "area_of_use") else None,
                **dict((col, getattr(crsinfo, col)) for col in features),
            }
            for crsinfo in pyproj.database.query_crs_info(
                "EPSG",
                "PROJECTED_CRS",  # type: ignore
                # typing: explain (str are also valid)
                pyproj.aoi.AreaOfInterest(
                    *shape(area.__geo_interface__).bounds
                ),
            )
        )
    )
