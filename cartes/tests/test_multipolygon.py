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
