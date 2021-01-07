from typing import List, Optional, Type, TypeVar, Union

from shapely.geometry import mapping, shape

from ..core import GeoObject
from ..utils.descriptors import OrientedShape
from ..utils.mixins import HBoxMixin, HTMLAttrMixin, HTMLTitleMixin
from .requests import json_request

T = TypeVar("T", bound="Nominatim")


class Nominatim(GeoObject, HBoxMixin, HTMLTitleMixin, HTMLAttrMixin):

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

    def __init__(self, json) -> None:
        super().__init__()
        self.json = json
        self.shape = shape(self.json["geojson"])

    @property
    def __geo_interface__(self):
        return mapping(self.shape)

    def __repr__(self):
        return f"{type(self).__name__} {self.json}"

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
    def address(self):
        if address := self.json.get("address", None):
            return address
        return self.json["display_name"].split(", ")

    def _repr_html_(self):
        return (
            super()._repr_html_()
            + "<div style='float: left; margin: 10px;'>"
            + self._repr_svg_()
            + "</div>"
        )

    @classmethod
    def search(cls: Type[T], name: str, **kwargs) -> Optional[T]:
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
        params = dict(
            lat=latitude, lon=longitude, format="jsonv2", polygon_geojson=True,
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
        params = dict(osm_ids=osm_ids, format="jsonv2", polygon_geojson=True,)
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
