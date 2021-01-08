import hashlib
import json
import logging
import time
from io import BytesIO
from pathlib import Path

import requests
from appdirs import user_cache_dir
from tqdm.autonotebook import tqdm

from ..utils.cache import CacheResults

session = requests.Session()


def hash_request(*args, **kwargs):
    if "timeout" in kwargs:
        del kwargs["timeout"]

    if "data" in kwargs:
        query = kwargs["data"].replace("\n", "").replace(" ", "")
        hashcode = hashlib.md5(query.encode("utf-8")).hexdigest()
    else:
        prepared_url = requests.Request("POST", *args, **kwargs).prepare().url
        assert prepared_url is not None
        hashcode = hashlib.md5(prepared_url.encode("utf-8")).hexdigest()
    return hashcode + ".json"


def write_json(json_, cache_file):
    logging.info(f"Writing cache file {cache_file}")
    cache_file.write_text(json.dumps(json_, indent=2))


def read_json(cache_file):
    logging.info(f"Reading cache file {cache_file}")
    return json.loads(cache_file.read_text())


@CacheResults(
    cache_dir=Path(user_cache_dir("cartes")) / "osm",
    hashing=hash_request,
    reader=read_json,
    writer=write_json,
)
def json_request(url, timeout=180, **kwargs):
    """
    Send a request to the Overpass API and return the JSON response.
    """
    logging.info(f"Sending POST request to {url} with {kwargs}")

    response = session.post(url=url, timeout=timeout, **kwargs)

    if response.status_code in [
        429,  # too many requests
        504,  # gateway timeout
    ]:
        msg = f"Got status code {response.status_code}. Trying again soon..."
        logging.warning(msg)
        time.sleep(5)
        return json_request(url, timeout=timeout, **kwargs)

    response.raise_for_status()

    if kwargs.get("stream", None):
        total_size = int(response.headers.get("content-length", 0))
        logging.info(f"{response.headers}")
        block_size = 1024 * 1024
        pbar = tqdm(total=total_size, unit="B", unit_scale=True)
        b = BytesIO()
        for data in response.iter_content(block_size):
            pbar.update(len(data))
            b.write(data)
        b.seek(0)
        pbar.close()
        if total_size != 0 and pbar.n != total_size:
            msg = f"Download not complete: {pbar.n}/{total_size}"
            raise RuntimeError(msg)

    try:
        if kwargs.get("stream", None):
            response_json = json.loads(b.read().decode())
        else:
            response_json = response.json()
    except Exception:
        msg = f"""Server returned no JSON data.
        {response} {response.reason}
        {response.text}"""
        logging.warning(msg)
        raise

    return response_json
