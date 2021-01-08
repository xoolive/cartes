import functools
from pathlib import Path
from typing import Union

from .descriptors import DirectoryCreateIfNotExists


class CacheFunction:
    cache_dir = DirectoryCreateIfNotExists()

    def __init__(self, function, cache_dir, hashing, writer, reader):
        self.function = function
        self.cache_dir = cache_dir
        self.hashing = hashing
        self.writer = writer
        self.reader = reader
        self.lru_cache = dict()

    def __call__(self, *args, **kwargs):
        hashcode = self.hashing(*args, **kwargs)
        cache_file = self.cache_dir / hashcode
        res = self.lru_cache.get(cache_file.as_posix(), None)
        if res is not None:
            return res
        if cache_file.exists():
            res = self.reader(cache_file)
        else:
            res = self.function(*args, **kwargs)
            self.writer(res, cache_file)
        self.lru_cache[cache_file.as_posix()] = res
        return res


class CacheResults:
    def __init__(self, cache_dir: Union[str, Path], hashing, writer, reader):
        self.cache_dir = cache_dir
        self.hashing = hashing
        self.writer = writer
        self.reader = reader

    def __call__(self, function):
        cache_function = CacheFunction(
            function, self.cache_dir, self.hashing, self.writer, self.reader
        )
        return functools.wraps(function)(cache_function)
