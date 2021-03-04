import logging
import sys
from pathlib import Path
from typing import Callable, Dict, Generic, Hashable, TypeVar, Union

from .descriptors import DirectoryCreateIfNotExists

T = TypeVar("T")


if sys.version_info >= (3, 8):
    from functools import cached_property
else:

    _not_found = object()

    class cached_property(object):
        """Super simple implementation from functools."""

        def __init__(self, func):
            self.func = func
            self.__doc__ = getattr(func, "__doc__")

        def __set_name__(self, owner, name):
            self.attrname = name

        def __get__(self, instance, cls):
            if instance is None:
                return self
            cache = instance.__dict__
            val = cache.get(self.attrname, _not_found)
            if val is _not_found:
                cache[self.attrname] = val = self.func(instance)
            return val


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
        if cache_file.exists():
            logging.info(f"Using cache file: {cache_file}")
            res = self.reader(cache_file)
        else:
            msg = f"Calling function {self.function} with {args, kwargs}"
            logging.debug(msg)
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
