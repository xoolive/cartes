import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Literal, Optional

import httpx
from appdirs import user_cache_dir

from ..utils.cache import CacheResults

JSONType = Any
GeoJSONType = Any

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0)"
    "Gecko/20100101 Firefox/116.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;"
    "q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
}
client = httpx.Client(follow_redirects=True, http2=True)

_log = logging.getLogger(__name__)


def _hash_request(*args, **kwargs) -> str:
    if "timeout" in kwargs:
        del kwargs["timeout"]

    if "method" in kwargs:
        del kwargs["method"]

    if "data" in kwargs:  # overpass requests
        query = kwargs["data"].replace("\n", "").replace(" ", "")
        hashcode = hashlib.md5(query.encode("utf-8")).hexdigest()
    else:  # usual ones
        prepared_url = httpx.Request("POST", *args, **kwargs).url
        assert prepared_url is not None
        hashcode = hashlib.md5(f"{prepared_url}".encode("utf-8")).hexdigest()
    return hashcode + ".json"


def _write_json(json_: JSONType, cache_file) -> None:  # coverage: ignore
    _log.info(f"Writing cache file {cache_file}")
    cache_file.write_text(json.dumps(json_, indent=2))


def _read_json(cache_file: Path) -> Optional[JSONType]:
    _log.info(f"Reading cache file {cache_file}")
    json_ = json.loads(cache_file.read_text())

    if isinstance(json_, list):
        return json_

    elements = json_.get("elements", None)
    if elements is None:
        return json_

    # Detect past failed cached Overpass queries
    _log.debug(f"Number of elements in cached results: {len(elements)}")
    if len(elements) == 0:
        return None

    return json_


@CacheResults(
    cache_dir=os.environ.get(
        "CARTES_CACHE",
        default=Path(user_cache_dir("cartes")) / "osm",
    ),
    hashing=_hash_request,
    reader=_read_json,
    writer=_write_json,
)
def json_request(
    url: str,
    timeout: int = 180,
    method: Literal["POST", "GET"] = "POST",
    **kwargs,
) -> JSONType:
    """
    Send a request to the Overpass API and return the JSON response.
    """
    _log.info(f"Sending POST request to {url} with {kwargs}")

    new_kwargs = kwargs.copy()
    if "data" in new_kwargs:
        new_kwargs["data"] = new_kwargs["data"].encode("utf-8")

    request = httpx.Request(
        method=method,
        url=url,
        headers=DEFAULT_HEADERS,
        **kwargs,
    )
    response = client.send(request)

    if response.status_code == 403:  # forbidden for url
        msg = "Error 403: IP address may be blocked"
        _log.warning(msg)

    if response.status_code == 504:  # gateway timeout
        msg = f"Got status code {response.status_code}. Trying again soon..."
        _log.warning(msg)
        time.sleep(5)
        return json_request(url, timeout=timeout, **kwargs)

    if response.status_code == 429:  # too many requests
        status = client.get("https://overpass-api.de/api/status")
        status.raise_for_status()
        print(status.content.decode())

    response.raise_for_status()

    # b = BytesIO()

    # if kwargs.get("stream", None):
    #     total_size = int(response.headers.get("content-length", 0))
    #     _log.info(f"{response.headers}")
    #     block_size = 1024 * 1024
    #     pbar = tqdm(total=total_size, unit="B", unit_scale=True)
    #     for data in response.iter_content(block_size):
    #         pbar.update(len(data))
    #         b.write(data)
    #     b.seek(0)
    #     pbar.close()
    #     if total_size != 0 and pbar.n != total_size:
    #         msg = f"Download not complete: {pbar.n}/{total_size}"
    #         raise RuntimeError(msg)

    # try:
    #     if kwargs.get("stream", None):
    #         response_json = json.loads(b.read().decode())
    #     else:
    try:
        response_json = response.json()
    except Exception:
        msg = f"""Server returned no JSON data.
        {response} {response.reason_phrase}
        {response.text}"""
        _log.warning(msg)
        raise

    return response_json
