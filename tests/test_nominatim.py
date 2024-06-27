from cartes.osm import Nominatim


def test_search() -> None:
    toulouse = Nominatim.search("Toulouse")
    assert toulouse is not None
    assert toulouse.display_name.startswith("Toulouse")
    assert toulouse.city == "Toulouse"
    assert toulouse.osm_id == 35738

    assert "2154" in list(toulouse.valid_crs().code)


def test_lookup() -> None:
    capitole = Nominatim.lookup("R367073")
    assert capitole is not None
    assert capitole.city == "Toulouse"  # type: ignore
    assert capitole.category == "tourism"  # type: ignore


def test_reverse() -> None:
    place = Nominatim.reverse(43.60838, 1.441970)
    assert place is not None
    assert place.name == "Basilique Saint-Sernin"
    assert place.road == "Place Saint-Sernin"
    assert place.osm_type == "way"
