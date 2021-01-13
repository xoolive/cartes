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
    musee = Nominatim.reverse(43.608, 1.442)
    assert musee is not None
    assert musee.tourism == "Musée Saint-Raymond"
    assert musee.road == "Place Saint-Sernin"
    assert musee.osm_type == "way"
