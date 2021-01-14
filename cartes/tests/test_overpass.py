from cartes.osm.overpass import Overpass


def test_basic_query() -> None:
    query_lfbo = "[out:json];area[icao=LFBO];nwr(area)[aeroway];out geom;"
    lfbo = Overpass.request(query=query_lfbo)
    runways = sorted(set(lfbo.data.query('aeroway=="runway"').ref))
    assert runways == ["14H/32H", "14L/32R", "14R/32L"]
