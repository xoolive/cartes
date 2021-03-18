from typing import List, Optional, Type, TypeVar, Union

from shapely.geometry import mapping, shape

from ..core import GeoObject
from ..utils.descriptors import OrientedShape
from ..utils.mixins import HBoxMixin, HTMLAttrMixin, HTMLTitleMixin
from .requests import GeoJSONType, JSONType, json_request

T = TypeVar("T", bound="Nominatim")


class Nominatim(GeoObject, HBoxMixin, HTMLTitleMixin, HTMLAttrMixin):
    """A class to parse Nominatim results.

    A Nominatim object is built based on JSON results of Nominatim requests.
    Nominatim requests are based on corresponding class methods:

    - Nominatim.search performs a search based on text;
    - Nominatim.reverse performs a search based on latlon coordinates;
    - Nominatim.lookup performs a search based on an OSM identifier.
    """

    shape = OrientedShape()

    endpoint = "https://nominatim.openstreetmap.org/"
    html_attr_list = [
        "osm_type",
        "osm_id",
        "address",
        "category",
        "type_",
        "importance",
    ]

    def __init__(self, json: JSONType) -> None:
        super().__init__()
        self.json = json
        self.shape = shape(self.json["geojson"])

    @property
    def __geo_interface__(self) -> GeoJSONType:
        return mapping(self.shape)

    @property
    def simple_json(self) -> JSONType:
        return {
            "place_id": self.json.get("place_id", None),
            "display_name": self.json.get("display_name", None),
            "lat": round(float(self.json.get("lat", "nan")), 5),
            "lon": round(float(self.json.get("lon", "nan")), 5),
        }

    def __repr__(self) -> str:
        return f"{type(self).__name__} {self.simple_json}"

    def __getattr__(self, name):
        if name.endswith("_"):  # in case the name is reserved
            name = name[:-1]
        value = self.json.get(name, None)
        if value is None:
            address = self.json.get("address", None)
            if address is not None:
                value = address.get(name, None)
        if value is None:
            raise AttributeError(name)
        return value

    @property
    def address(self) -> str:
        address = self.json.get("address", None)
        if address:
            return address
        return self.json["display_name"].split(", ")

    def _repr_html_(self) -> str:
        return (
            super()._repr_html_()
            + "<div style='float: left; margin: 10px;'>"
            + self._repr_svg_()
            + "</div>"
        )

    @classmethod
    def search(cls: Type[T], name: str, **kwargs) -> Optional[T]:
        """Performs a Nominatim search request.

        The request is based on the name passed in parameter.
        >>> Nominatim.search("Toulouse")
        Nominatim {'place_id': 256863032, 'display_name': 'Toulouse, ...', 'lat': 43.60446, 'lon': 1.44425}

        """
        params = dict(
            q=name,
            format="jsonv2",
            limit=1,
            dedupe=False,
            polygon_geojson=True,
            addressdetails=True,
        )
        json = json_request(
            cls.endpoint.rstrip("/") + "/" + "search",
            timeout=30,
            params=params,
            **kwargs,
        )
        if len(json) == 0:
            return None
        return cls(json[0])

    @classmethod
    def reverse(
        cls: Type[T], latitude: float, longitude: float, **kwargs
    ) -> Optional[T]:
        """Performs a Nominatim search request.

        The request is based on the latlon coordinates of the element.
        >>> Nominatim.reverse(43.608, 1.442)
        Nominatim {'place_id': 154834803, 'display_name': 'Musée Saint-Raymond, ...', 'lat': 43.60783, 'lon': 1.44112}
        """

        params = dict(
            lat=latitude,
            lon=longitude,
            format="jsonv2",
            polygon_geojson=True,
        )
        json = json_request(
            cls.endpoint.rstrip("/") + "/" + "reverse",
            timeout=30,
            params=params,
            **kwargs,
        )
        if len(json) == 0:
            return None
        return cls(json)

    @classmethod
    def lookup(
        cls: Type[T], osm_ids: Union[str, List[str]], **kwargs
    ) -> Union[None, T, List[T]]:
        """Performs a Nominatim search request.

        The request is based on the OSM id of the element. The prefix
        determines the type of the OSM object (N for node, W for way, R for
        relation)
        >>> Nominatim.lookup("R367073")
        Nominatim {'place_id': 256948794, 'display_name': 'Capitole ...', 'lat': 43.60445, 'lon': 1.44449}
        """
        params = dict(
            osm_ids=osm_ids,
            format="jsonv2",
            polygon_geojson=True,
        )
        json = json_request(
            cls.endpoint.rstrip("/") + "/" + "lookup",
            timeout=30,
            params=params,
            **kwargs,
        )
        if len(json) == 0:
            return None
        elif len(json) == 1:
            return cls(json[0])
        else:
            return list(cls(json_ for json_ in json))
