from functools import lru_cache
from operator import itemgetter
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, Union

import geopandas as gpd
from tqdm.autonotebook import tqdm

from ...utils.cache import CacheResults, cached_property
from ...utils.descriptors import Descriptor
from ..requests import JSONType, json_request
from .core import NodeWayRelation, to_geometry


def hashing_id(*args, **kwargs):
    elt = args[1] if len(args) > 1 else kwargs["elt"]
    return elt["id"]


cache_by_id = CacheResults(
    cache_dir=".",
    hashing=hashing_id,
    # no storing in files
    writer=lambda _a, _b: None,
    reader=lambda _: dict(unused=True),
)


class OverpassDataDescriptor(Descriptor[gpd.GeoDataFrame]):
    """Builds the GeoDataFrame on demand.
    Validates it has required fields when replaced.
    """

    def __get__(self, obj, cls=None) -> gpd.GeoDataFrame:
        data = getattr(obj, self.private_name)
        if data is None:
            data = obj.parse()
            for col in ["_parent", "members", "nodes"]:
                if col in data.columns:
                    data = data.drop(columns=col)
            setattr(obj, self.private_name, data)
        return data

    def __set__(self, obj, data: gpd.GeoDataFrame) -> None:
        feat = ["id_", "type_", "geometry"]
        msg = f"Ensure you do not remove the following features: {feat}"
        if any(f not in data.columns for f in feat):
            raise TypeError(msg)

        setattr(obj, self.private_name, data)


class Overpass:
    endpoint = "http://www.overpass-api.de/api/interpreter"
    data = OverpassDataDescriptor()

    def __init__(self, json: JSONType, data: Optional[gpd.GeoDataFrame] = None):
        super().__init__()
        self.json = json
        if data is None:
            self._data = None
        else:
            self.data = data

    def _repr_html_(self):
        return self.data._repr_html_()

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        return tuple(  # type: ignore
            eval(key[:3])(
                (x["bounds"] for x in self.json["elements"]),
                key=itemgetter(key),
            )[key]
            for key in ["minlon", "minlat", "maxlon", "maxlat"]
        )

    @property
    def extent(self) -> Tuple[float, float, float, float]:
        west, south, east, north = self.bounds
        return west, east, south, north

    @classmethod
    def request(
        cls, query: Optional[str] = None, *args, **kwargs
    ) -> "Overpass":
        if query is None:
            query = cls.build_query(*args, **kwargs)
        res = json_request(url=Overpass.endpoint, data=query, **kwargs)
        return Overpass(res)

    @staticmethod
    def build_query(*args, **kwargs) -> str:
        return ""

    def assign(self, *args, **kwargs) -> "Overpass":
        return Overpass(self.json, self.data.assign(*args, **kwargs))

    def query(self, *args, **kwargs) -> "Overpass":
        return Overpass(self.json, self.data.query(*args, **kwargs))

    def drop(self, *args, **kwargs) -> "Overpass":
        return Overpass(self.json, self.data.drop(*args, **kwargs))

    def dropna(self, *args, **kwargs) -> "Overpass":
        return Overpass(self.json, self.data.dropna(*args, **kwargs))

    def sort_values(self, *args, **kwargs) -> "Overpass":
        return Overpass(self.json, self.data.sort_values(*args, **kwargs))

    def simplify(
        self, resolution: Optional[float] = None, **kwargs
    ) -> "Overpass":
        if resolution is None:
            return self
        new_overpass = Overpass(self.json)
        return new_overpass.data.assign(
            geometry=list(
                nwr.simplify(resolution, **kwargs).shape  # TODO multiprocess
                for nwr in tqdm(self, total=self.data.shape[0])
            )
        )

    def __iter__(self) -> Iterator[NodeWayRelation]:
        for _, line in self.data.iterrows():
            yield NodeWayRelation({"_parent": self, **dict(line)})

    def __getitem__(self, item) -> NodeWayRelation:
        elt = self.data.query("id_ == @item")
        if elt.shape[0] == 0:
            raise AttributeError(f"No {item} id_ in the current data")
        return NodeWayRelation({"_parent": self, **dict(elt.iloc[0])})

    @property
    def __geo_interface__(self):
        return self.data.__geo_interface__

    @cache_by_id
    def make_node(self, elt: Dict[str, Any]) -> Dict[str, Any]:
        return dict(
            _parent=self,
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
            _parent=self,
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
                    if entry["type"] != "relation"
                    # TODO subrelations not supported
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
