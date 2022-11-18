from __future__ import annotations

import json
import logging
from functools import cached_property  # noqa: F401
from pathlib import Path
from typing import Any, Callable, Dict, Generic, Hashable, TypeVar, Union

import pandas as pd

from .descriptors import DirectoryCreateIfNotExists

T = TypeVar("T")

_log = logging.getLogger(__name__)


class CacheFunction(Generic[T]):
    """Function caching utilities.

    This class puts results in a two-layer cache.

    Results are first fetched from a LRU cache available as long as the
    function exists. If the result is not in cache, then it attempts picking
    it from a file in a dedicated directory.

    The class needs four arguments:
    - cache_dir: Union[str, Path] is the place where to store the cache files;
    - hashing: Callable[..., Hashable] computes a hash based on arguments
      passed to the function. The hash will be the key to the LRU cache and the
      name of the file;
    - writer: Callable[[T, Path], None] describes how to serialize the results;
    - reader: Callable[[Path], T] describes how to read the results from a file.

    """

    cache_dir = DirectoryCreateIfNotExists()

    def __init__(
        self,
        function: Callable[..., T],
        cache_dir: Union[str, Path],
        hashing: Callable[..., Hashable],
        writer: Callable[[T, Path], None],
        reader: Callable[[Path], T],
    ):
        self.function = function
        self.cache_dir = cache_dir
        self.hashing = hashing
        self.writer = writer
        self.reader = reader

        self.lru_cache: Dict[Hashable, T] = dict()

    def __call__(self, *args, **kwargs) -> T:
        hashcode = self.hashing(*args, **kwargs)
        cache_file = self.cache_dir / str(hashcode)
        res = self.lru_cache.get(cache_file.as_posix(), None)  # type: ignore

        if res is not None:
            return res

        _log.info(f"Looking for cache file: {cache_file}")

        if cache_file.exists():
            _log.info(f"Using cache file: {cache_file}")
            res = self.reader(cache_file)

        if res is None:
            msg = f"Calling function {self.function} with {args, kwargs}"
            _log.debug(msg)
            res = self.function(*args, **kwargs)
            self.writer(res, cache_file)

        self.lru_cache[cache_file.as_posix()] = res
        return res


class CacheResults(Generic[T]):
    """Defines a decorator for functions when results should be cached.

    The class needs four arguments:
    - cache_dir: Union[str, Path] is the place where to store the cache files;
    - hashing: Callable[..., Hashable] computes a hash based on arguments
      passed to the function. The hash will be the key to the LRU cache and the
      name of the file;
    - writer: Callable[[T, Path], None] describes how to serialize the results;
    - reader: Callable[[Path], T] describes how to read the results from a file.

    """

    def __init__(
        self,
        cache_dir: Union[str, Path],
        hashing: Callable[..., Hashable],
        writer: Callable[[T, Path], None],
        reader: Callable[[Path], T],
    ):
        self.cache_dir = cache_dir
        self.hashing = hashing
        self.writer = writer
        self.reader = reader

    def __call__(self, function: Callable[..., T]) -> CacheFunction[T]:
        cache_function = CacheFunction(
            function, self.cache_dir, self.hashing, self.writer, self.reader
        )
        cache_function.__doc__ = function.__doc__
        return cache_function


def write_json(content: Any, cache_file: Path) -> None:
    _log.info(f"Writing cache file {cache_file}")
    directory = cache_file.parent
    if not directory.exists():
        directory.mkdir(parents=True)
    cache_file.write_text(json.dumps(content))


def read_json(cache_file: Path) -> Any:
    _log.info(f"Reading cache file {cache_file}")
    return json.loads(cache_file.read_text())


def write_df_json(df: pd.DataFrame, cache_file: Path) -> None:
    _log.info(f"Writing cache file {cache_file}")
    directory = cache_file.parent
    if not directory.exists():
        directory.mkdir(parents=True)
    df.to_json(cache_file, orient="records")


def read_json_df(cache_file: Path) -> pd.DataFrame | None:
    _log.info(f"Reading cache file {cache_file}")
    return pd.read_json(cache_file)
