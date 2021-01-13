import logging
from pathlib import Path

from cartes.osm.requests import json_request


def pytest_configure(config):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    current_dir = Path(__file__).parent
    while next(current_dir.glob("tests"), None) is None:
        current_dir = current_dir.parent

    json_request.cache_dir = current_dir / "tests" / "cache"  # type: ignore
