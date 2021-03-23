import logging
from concurrent.futures import Future, ProcessPoolExecutor, as_completed
from functools import lru_cache
from operator import itemgetter
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, Union

import geopandas as gpd
import pandas as pd
from pyproj import Proj
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union
from tqdm.autonotebook import tqdm

from ...crs import PlateCarree  # type: ignore
from ...dataviz import matplotlib_style
from ...utils.cache import CacheResults, cached_property
from ...utils.descriptors import Descriptor
from ...utils.geometry import reorient
from ..requests import JSONType, json_request
from .core import NodeWayRelation, to_geometry
from .query import Query


def hashing_id(*args: Dict[str, int], **kwargs: Dict[str, int]) -> int:
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
        if "latitude" in data.columns:
            x = data.query("latitude != latitude")
        else:
            x = data.assign(latitude=None, longitude=None)

        if x.shape[0] > 0:
            x = x.query("geometry == geometry and not geometry.is_empty")
            data.loc[x.index, ["latitude", "longitude"]] = x.assign(
                longitude=lambda df: df.geometry.centroid.x,
                latitude=lambda df: df.geometry.centroid.y,
            )[["latitude", "longitude"]]

        if "geometry" in data.columns:
            data = data.assign(
                # TODO This should not be necessary, yet...
                geometry=lambda df: df.geometry.apply(reorient)
            )

        return data.dropna(axis=1, how="all")

    def __set__(self, obj, data: gpd.GeoDataFrame) -> None:
        feat = ["id_", "type_", "geometry"]
        msg = f"Did you remove any of {feat} from {data.columns}?"
        if any(f not in data.columns for f in feat):
            raise TypeError(msg)

        setattr(obj, self.private_name, data)


class Overpass:
    endpoint = "http://www.overpass-api.de/api/interpreter"
    data = OverpassDataDescriptor()

    def __init__(self, json: JSONType, data: Optional[gpd.GeoDataFrame] = None):
        super().__init__()
        self.json = json
        self._bounds: Optional[Tuple[float, float, float, float]] = None
        if data is None:
            self._data = None
        else:
            self.data = data

    def _repr_html_(self):
        return self.data._repr_html_()

    def __getstate__(self):
        """
        In order for the multiprocessing step to be efficient, we choose here
        to empty the JSON and avoid numerous useless pickling.

        Currently used only in .simplify()
        """
        # Compute it once, because we need it for the simplification process
        if getattr(self, "simplify_flag", None):
            _ = self.bounds, self.data
        # Copy the object's state from self.__dict__ which contains
        # all our instance attributes. Always use the dict.copy()
        # method to avoid modifying the original state.
        state = self.__dict__.copy()
        # Usually, we do not need the json of the parent for the simplification
        if getattr(self, "simplify_flag", None):
            state["json"] = dict(
                (key, value)
                for key, value in self.json.items()
                if key != "elements"
            )
        return state

    def __setstate__(self, state):
        # Restore instance attributes
        self.__dict__.update(state)

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        if self._bounds is not None:
            return self._bounds
        if "geometry" in self.data.columns:
            x = (
                self.data.query("geometry == geometry")
                .assign(empty=lambda df: df.geometry.is_empty)
                .query("not empty")
            )
            if x.shape[0] > 0:
                self._bounds = unary_union(self.data.geometry).bounds
                return self._bounds
        self._bounds = tuple(  # type: ignore
            eval(key[:3])(
                (x["bounds"] for x in self.json["elements"] if "bounds" in x),
                key=itemgetter(key),
            )[key]
            for key in ["minlon", "minlat", "maxlon", "maxlat"]
        )
        return self._bounds  # type: ignore

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
        res = json_request(url=Overpass.endpoint, data=query)
        return Overpass(res)

    @staticmethod
    def build_query(*, out: str = "json", timeout: int = 180, **kwargs) -> str:
        query = Query(out=out, timeout=timeout, **kwargs)
        return query.generate()

    def assign(self, *args, **kwargs) -> "Overpass":
        return Overpass(self.json, self.data.assign(*args, **kwargs))

    def query(self, *args, **kwargs) -> "Overpass":
        return Overpass(self.json, self.data.query(*args, **kwargs))

    def drop(self, *args, **kwargs) -> "Overpass":
        return Overpass(self.json, self.data.drop(*args, **kwargs))

    def merge(self, *args, **kwargs) -> "Overpass":
        return Overpass(self.json, self.data.merge(*args, **kwargs))

    def dropna(self, *args, **kwargs) -> "Overpass":
        return Overpass(self.json, self.data.dropna(*args, **kwargs))

    def sort_values(self, *args, **kwargs) -> "Overpass":
        return Overpass(self.json, self.data.sort_values(*args, **kwargs))

    def area(self) -> "Overpass":
        bounds = self.bounds
        proj = Proj(
            proj="aea",  # equivalent projection
            lat_1=bounds[1],
            lat_2=bounds[3],
            lat_0=(bounds[1] + bounds[3]) / 2,
            lon_0=(bounds[0] + bounds[2]) / 2,
        )
        return self.assign(
            area=self.data.geometry.set_crs(epsg=4326).to_crs(crs=proj.crs).area
        )

    def length(self) -> "Overpass":
        bounds = self.bounds
        proj = Proj(
            proj="aea",  # equivalent projection
            lat_1=bounds[1],
            lat_2=bounds[3],
            lat_0=(bounds[1] + bounds[3]) / 2,
            lon_0=(bounds[0] + bounds[2]) / 2,
        )
        return self.assign(
            length=self.data.geometry.set_crs(epsg=4326)
            .to_crs(crs=proj.crs)
            .length
        )

    def coloring(self) -> "Overpass":
        import networkx as nx

        self.graph = nx.Graph()
        for elt in self:
            for neighbour in elt.neighbours:
                self.graph.add_edge(elt.json["id_"], neighbour)
        colors = nx.algorithms.coloring.greedy_color(self.graph)
        merge = self.merge(
            pd.Series(colors, name="coloring"), left_on="id_", right_index=True
        )
        merge.graph = self.graph
        return merge

    def simplify(
        self,
        resolution: Optional[float] = None,
        max_workers: Optional[int] = 4,
        **kwargs,
    ) -> "Overpass":

        if resolution is None:
            return self

        new_overpass = Overpass(self.json)

        if max_workers is not None and max_workers > 1:
            self.simplify_flag = True
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures: Dict[Future, int] = dict()
                for i, nwr in enumerate(self):
                    futures[
                        executor.submit(nwr.simplify, resolution, **kwargs)
                    ] = i
                result: List[Tuple[int, BaseGeometry]] = list()
                for future in tqdm(as_completed(futures), total=len(futures)):
                    result.append((futures[future], future.result().shape))
            self.simplify_flag = False
        else:
            result = list(
                (i, nwr.simplify(resolution, **kwargs))
                for i, nwr in tqdm(enumerate(self), total=self.data.shape[0])
            )

        new_overpass.data = self.data.assign(
            geometry=list(elt for _, elt in sorted(result))
        )
        new_overpass.json = self.json

        return new_overpass

    def __iter__(self) -> Iterator[NodeWayRelation]:
        for _, line in self.data.iterrows():
            yield NodeWayRelation({"_parent": self, **dict(line)})

    @lru_cache()
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

    def plot(self, ax, by: Optional[str] = None, **kwargs):
        if by is None:
            return self.data.plot(ax=ax, transform=PlateCarree())
        for key, elt in self.data.groupby(by):
            if (
                by not in matplotlib_style
                and key not in matplotlib_style
                and by not in kwargs
                and key not in kwargs
            ):
                logging.warning(f"{by}={key} not in stylesheet, hence ignored")
                continue
            current_style = {
                **matplotlib_style.get(by, {}),
                **matplotlib_style.get(key, {}),
                **kwargs.get(by, {}),
                **kwargs.get(key, {}),
            }
            if "key" in current_style:
                if current_style["key"] not in elt.columns:
                    continue
                for cat, piece in elt.groupby(current_style["key"]):
                    if cat in matplotlib_style[key]:
                        piece.plot(
                            ax=ax,
                            transform=PlateCarree(),
                            **current_style.get(cat, {}),
                        )
                    else:
                        msg = f"{key}={cat} not in stylesheet, hence ignored"
                        logging.warning(msg)
            else:
                elt.plot(ax=ax, transform=PlateCarree(), **current_style)
