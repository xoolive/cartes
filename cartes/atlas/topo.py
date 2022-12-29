from __future__ import annotations

import asyncio
import json
import os
import re
import time
from io import StringIO
from operator import attrgetter
from pathlib import Path
from typing import Any

import aiohttp
import altair as alt
import geopandas as gpd
import requests
from appdirs import user_cache_dir

import pandas as pd

from ..osm.requests import session
from ..utils.cache import (
    CacheResults,
    cached_property,
    read_json,
    read_json_df,
    write_df_json,
    write_json,
)
from ..utils.mixins import HTMLMixin


class GithubAPI:
    id_: str
    base_url = "https://api.github.com/repos/{username}/{repository}/contents/"

    def __init__(
        self,
        username: str = "deldersveld",
        repository: str = "topojson",
    ) -> None:
        self.base_url = GithubAPI.base_url.format(
            username=username, repository=repository
        )
        self.id_ = f"{username}_{repository}"

    async def async_get_recursive(
        self,
        session: aiohttp.ClientSession,
        path: str = "",
    ) -> pd.DataFrame:

        async with session.get(self.base_url + path) as resp:
            json = await resp.json()
            if "message" in json:
                raise RuntimeError(
                    f"{json['message']}\n{json['documentation_url']}"
                )

        df = pd.json_normalize(json)[["path", "download_url", "type", "size"]]

        futures = list(
            self.async_get_recursive(session, elt)
            for elt in df.query('type == "dir"').path
        )
        df_list = [df] + list(
            result
            for result in await asyncio.gather(*futures, return_exceptions=True)
        )

        return pd.concat(df_list)

    async def async_get_features(self) -> pd.DataFrame:
        headers = dict()
        if token := os.getenv("GITHUB_TOKEN") is not None:
            headers["authorization"] = f"{token}"
        async with aiohttp.ClientSession(trust_env=True, headers=headers) as s:
            return await self.async_get_recursive(s)

    def get_features(self) -> pd.DataFrame:
        loop = asyncio.get_event_loop()

        if loop.is_running():  # proxy for Jupyter notebook
            msg = "For details, run the same command inside a Python console."
            future = loop.create_task(self.async_get_features())
            for _ in range(5):
                if future.done():
                    result = future.result()
                    break
                time.sleep(1)
            else:
                future.cancel()
                raise TimeoutError(msg)
        else:
            result = asyncio.run(self.async_get_features())

        return result


class NpmAPI:
    api_url = "https://data.jsdelivr.com/v1/package/npm"
    base_url = "https://cdn.jsdelivr.net/npm"
    id_: str

    def __init__(self, name="world-atlas@2.0.2"):
        self.name = name
        if "@" not in name:
            c = requests.get(self.api_url + self.name)
            c.raise_for_status()
            self.latest = c.json()["tags"]["latest"]
        else:
            self.name, self.latest = name.split("@")
        self.id_ = f"{self.name}@{self.latest}"

    def get_features(self) -> pd.DataFrame:

        c = requests.get(f"{self.api_url}/{self.id_}/flat")
        c.raise_for_status()
        prefix = f"{self.base_url}/{self.id_}/"

        return (
            pd.json_normalize(c.json()["files"])
            .assign(name=lambda df: df.name.str[1:])  # remove initial /
            .assign(download_url=lambda df: prefix + df.name)
            .rename(columns=dict(name="path"))
            .drop(columns="time")
        )


@CacheResults(
    cache_dir=Path(user_cache_dir("cartes")) / "atlas",
    hashing=attrgetter("path"),
    reader=read_json,
    writer=write_json,
)
def get_json(elt: "TopoCatalogue") -> Any:
    c = session.get(elt.url)
    c.raise_for_status()
    return c.json()


class TopoCatalogue(HTMLMixin):
    def __init__(
        self,
        df: pd.DataFrame | None = None,
        api: GithubAPI | NpmAPI | None = None,
        username: str = "",
        repository: str = "",
    ) -> None:
        self.api = api
        if df is None:
            if self.api is None:
                self.api = GithubAPI(username=username, repository=repository)
            cache_dir = Path(user_cache_dir("cartes")) / "atlas" / self.api.id_
            get_features = CacheResults(
                cache_dir=cache_dir,
                hashing=lambda: "catalogue.json",
                reader=read_json_df,
                writer=write_df_json,
            )(self.api.get_features)
            df = get_features()

        self.df = df.query('path.str.endswith("json")')

    def __getattr__(self, name: str) -> "TopoCatalogue":
        if re.match("(_[0-9])?[A-Za-z0-9]+_?", name):
            if name.startswith("_"):  # escape numbers
                name = name[1:]
            res = self.q(name)
            if res is not None:
                return res
        raise AttributeError(name)

    def q(self, name: str) -> "TopoCatalogue" | None:
        if name.endswith("_"):
            query = f'not path.str.contains("{name[:-1]}")'
        else:
            query = f'path.str.contains("{name}")'
        new_data = self.df.query(query)
        if new_data.shape[0] > 0:
            return TopoCatalogue(new_data, api=self.api)
        return None

    def __repr__(self) -> str:
        return repr(self.df)

    def _repr_html_(self) -> str:
        return self.df._repr_html_()

    @property
    def url(self):
        return self.df.iloc[0].download_url

    @property
    def path(self):
        assert self.api is not None
        return Path(self.api.id_) / self.df.iloc[0].path

    @cached_property
    def features(self) -> list[str]:
        return list(get_json(self)["objects"].keys())

    @property
    def topo_feature(self):
        feature = self.features[0]
        return alt.topo_feature(self.url, feature=feature)

    @property
    def data(self):
        feature = self.features[0]
        return gpd.read_file(
            StringIO(json.dumps(get_json(self))), layout=feature
        )
