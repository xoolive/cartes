import logging

from cartes.osm.overpass import Overpass
from cartes.osm.requests import json_request

logger = logging.getLogger()
logger.setLevel(logging.INFO)

json_request.cache_dir = "tests/cache"  # type: ignore


def test_basic_query() -> None:
    query_lfbo = "[out:json];area[icao=LFBO];nwr(area)[aeroway];out geom;"
    lfbo = Overpass.query(data=query_lfbo)
    # TODO lfbo.aeroway.runway
    runways = sorted(set(lfbo.data.query('aeroway=="runway"').ref))
    assert runways == ["14H/32H", "14L/32R", "14R/32L"]
