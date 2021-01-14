import pytest
from cartes.osm.overpass import Overpass


def test_basic_query() -> None:
    query_lfbo = "[out:json];area[icao=LFBO];nwr(area)[aeroway];out geom;"
    lfbo = Overpass.request(query=query_lfbo)
    runways = sorted(set(lfbo.data.query('aeroway=="runway"').ref))
    assert runways == ["14H/32H", "14L/32R", "14R/32L"]


def test_validator() -> None:
    query_mercantour = """[out:json];
area["boundary"="protected_area"]["name"~"Mercantour"]->.a;
rel(pivot.a);
out geom;
node[natural=peak](area.a);
out geom;
"""
    mercantour = Overpass.request(query=query_mercantour)
    with pytest.raises(TypeError):
        mercantour.drop(columns=["geometry"])
