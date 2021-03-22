from cartes.osm import Overpass


def test_multipolygon():
    airport = Overpass.request(
        query="""[out:json][timeout:180];area[icao="LFPO"];nwr(area)[aeroway];
        out geom;""",
    )
    assert airport.data.shape[0] == 361

    airport = Overpass.request(
        query="""[out:json][timeout:180];area[icao="LEBL"];nwr(area)[aeroway];
        out geom;""",
    )
    assert airport.data.shape[0] == 864

    airport = Overpass.request(
        query="""[out:json][timeout:180];area[icao="EDDF"];nwr(area)[aeroway];
        out geom;""",
    )
    assert airport.data.shape[0] == 5297


def test_simplify():
    tls = Overpass.request(
        query="""[out:json][timeout:180];
area[name='Toulouse'][admin_level=8];
rel(area)["boundary"="postal_code"];
out geom;
 """
    )
    # Useless test, just check it works
    assert tls.simplify(1e3).data.shape[0] == 6
