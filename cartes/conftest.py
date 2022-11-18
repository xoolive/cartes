import logging
from pathlib import Path

from cartes.osm.requests import json_request


def pytest_configure(config):
    _log = logging.getLogger()
    _log.setLevel(logging.INFO)

    json_request.cache_dir = Path(config.rootdir) / "cartes" / "tests" / "cache"
    _log.warning(f"Using cache_dir {json_request.cache_dir} for tests")
