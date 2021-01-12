from functools import lru_cache
from typing import Any, Callable, Dict, Iterator, List, Union

import geopandas as gpd

from ...core import GeoObject
from ...utils.cache import CacheResults, cached_property
from ..requests import JSONType, json_request
from .core import NodeWayRelation, to_geometry


def hashing_id(*args, **kwargs):
    elt = args[1] if len(args) > 1 else kwargs["elt"]
    return elt["id"]


cache_by_id = CacheResults(
    cache_dir=".",
    hashing=hashing_id,
    writer=lambda _a, _b: None,
    reader=lambda _: dict(unused=True),
)


class Overpass(GeoObject):
    endpoint = "http://www.overpass-api.de/api/interpreter"

    def __init__(self, json: JSONType):
        self.json = json

    @property
    def gdf(self) -> gpd.GeoDataFrame:
        return self.parse()

    @classmethod
    def query(cls, data: str, **kwargs) -> "Overpass":
        res = json_request(url=Overpass.endpoint, data=data, **kwargs)
        return Overpass(res)

    def __iter__(self) -> Iterator[NodeWayRelation]:
        for _, line in self.gdf.iterrows():
            yield NodeWayRelation(dict(line))

    @property
    def __geo_interface__(self):
        return self.gdf.drop(columns="_parent").__geo_interface__

    @cache_by_id
    def make_node(self, elt: Dict[str, Any]) -> Dict[str, Any]:
        return dict(
            id_=elt["id"],
            type_=elt["type"],
            latitude=elt["lat"],
            longitude=elt["lon"],
            geometry=to_geometry(elt),
            **elt["tags"],
        )

    @cache_by_id
    def make_way(self, elt: Dict[str, Any]) -> Dict[str, Any]:
        return dict(
            id_=elt["id"],
            type_=elt["type"],
            nodes=elt["nodes"],
            geometry=to_geometry(elt),
            **elt["tags"],
        )

    @cache_by_id
    def make_relation(self, elt: Dict[str, Any]) -> Dict[str, Any]:
        return NodeWayRelation(
            dict(
                _parent=self,
                id_=elt["id"],
                type_=elt["type"],
                members=elt["members"],
                **elt["tags"],
            )
        ).json

    @cached_property
    def all_members(self) -> Dict[int, List[Dict[str, Union[int, str]]]]:
        return dict(
            (
                elt["id"],
                list(
                    {
                        "ref": entry["ref"],
                        "role": entry["role"],
                        "geometry": to_geometry(entry),
                    }
                    for entry in elt.get("members", [])
                    if entry["type"] != "relation"  # TODO
                ),
            )
            for elt in self.json["elements"]
        )

    @lru_cache()
    def parse(self) -> gpd.GeoDataFrame:
        make_dict: Dict[
            str, Callable[[Overpass, Dict[str, Any]], Dict[str, Any]]
        ] = {
            "node": Overpass.make_node,
            "way": Overpass.make_way,
            "relation": Overpass.make_relation,
        }
        return gpd.GeoDataFrame.from_records(
            list(
                make_dict[elt["type"]](self, elt)
                for elt in self.json["elements"]
                if elt.get("tags", None)
            )
        )
