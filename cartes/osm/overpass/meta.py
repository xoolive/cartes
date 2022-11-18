import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from appdirs import user_cache_dir
from bs4 import BeautifulSoup

from ...utils.cache import CacheResults
from ..requests import session

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

__all__ = ["features", "taglist"]  # noqa: F822

_log = logging.getLogger(__name__)


class TaglistType(TypedDict):
    features: List[str]
    taglist: Dict[str, List[str]]


JSONType = Any


def _hash_request(*args, **kwargs) -> str:
    return "taglist.json"


def _write_json(json_: JSONType, cache_file) -> None:  # coverage: ignore
    _log.info(f"Writing cache file {cache_file}")
    cache_file.write_text(json.dumps(json_, indent=2))


def _read_json(cache_file: Path) -> Optional[JSONType]:
    _log.info(f"Reading cache file {cache_file}")
    json_ = json.loads(cache_file.read_text())
    return json_


@CacheResults(
    cache_dir=Path(user_cache_dir("cartes")) / "osm",
    hashing=_hash_request,
    reader=_read_json,
    writer=_write_json,
)
def _feat_tags() -> TaglistType:

    c = session.get("https://wiki.openstreetmap.org/wiki/Map_Features")
    c.raise_for_status()
    e = BeautifulSoup(c.content)

    features = sorted(
        set(
            a.attrs["title"].split(":")[1].replace(" ", "_")
            for a in e.find_all("a", attrs={"href": re.compile("/wiki/Key:")})
        )
    )

    taglist = dict(
        (
            d.attrs["data-taginfo-taglist-tags"].split("=")[0],
            d.attrs["data-taginfo-taglist-tags"].split("=")[1].split(","),
        )
        for d in e.find_all("div", attrs={"class": "taglist"})
    )

    return dict(features=features, taglist=taglist)


def __getattr__(name: str) -> Any:
    if name in ["features", "taglist"]:
        return _feat_tags().get(name)
    raise AttributeError(f"No attribute '{name}'")
