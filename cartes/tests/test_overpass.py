import pytest

from cartes.osm.overpass import Overpass


def test_basic_query() -> None:
    query_lfbo = "[out:json];area[icao=LFBO];nwr(area)[aeroway];out geom;"
    lfbo = Overpass.request(query=query_lfbo)
    runways = sorted(set(lfbo.data.query('aeroway=="runway"').ref))
    assert runways == ["14H/32H", "14L/32R", "14R/32L"]


def test_proper_query() -> None:
    lfbo = Overpass.request(area=dict(icao="LFBO"), aeroway=True)
    runways = sorted(set(lfbo.data.query('aeroway=="runway"').ref))
    assert runways == ["14H/32H", "14L/32R", "14R/32L"]


def test_validator() -> None:
    query_mercantour = (
        "[out:json][timeout:180];"
        "area['boundary'='protected_area']['name'~'Mercantour']->.a;"
        "rel(pivot.a);"
        "out geom;"
        "node[natural=peak](area.a);"
        "out geom;"
    )
    mercantour = Overpass.request(query=query_mercantour)
    with pytest.raises(TypeError):
        mercantour.drop(columns=["geometry"])


def test_generate_query() -> None:
    assert (
        Overpass.build_query(area=dict(icao="LFBO"), aeroway=True)
        == "[out:json][timeout:180];"
        "area[icao=LFBO];nwr(area)[aeroway];out geom;"
    )

    south, west, north, east = 33, -30, 70, 35
    assert (
        Overpass.build_query(
            bounds=[west, south, east, north], node=dict(capital="yes")
        )
        == "[out:json][timeout:180][bbox:33,-30,70,35];"
        "node[capital=yes];out geom;"
    )

    mercantour = (
        "[out:json][timeout:180];"
        'area[boundary=protected_area][name~"Mercantour"]->.a;'
        "rel(pivot.a);"
        "out geom;"
        "node(area.a)[natural=peak];"
        "out geom;"
    )
    assert (
        Overpass.build_query(
            area=dict(
                boundary="protected_area",
                name=dict(regex="Mercantour"),
                as_="a",
            ),
            nwr=[
                dict(rel=dict(area="a")),
                dict(node=dict(natural="peak", area="a")),
            ],
        )
        == mercantour
    )

    toulouse = (
        "[out:json][timeout:180];"
        "area[name=Toulouse][admin_level=8];"
        "rel(area)[boundary=postal_code];out geom;"
    )

    assert (
        Overpass.build_query(
            area=dict(name="Toulouse", admin_level=8),
            rel=dict(boundary="postal_code"),
        )
        == toulouse
    )

    cannes = (
        "[out:json][timeout:180];"
        "area[name=Cannes][admin_level=8];"
        "nwr(area)[building];"
        "out geom;"
    )

    assert (
        Overpass.build_query(
            area=dict(name="Cannes", admin_level=8), building=True
        )
        == cannes
    )

    neste = (
        "[out:json][timeout:180];"
        'rel[waterway=canal][name~"Neste"];'
        "out geom;"
        "rel(around:1000)[waterway=river];"
        "out geom;"
        'rel[waterway=river][name="La Garonne"];'
        "out geom;"
    )

    assert (
        Overpass.build_query(
            rel=[
                dict(waterway="canal", name=dict(regex="Neste")),
                dict(around=1000, waterway="river"),
                dict(waterway="river", name="La Garonne"),
            ]
        )
        == neste
    )
