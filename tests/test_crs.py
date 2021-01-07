# type: ignore

from cartes import crs


def test_crs() -> None:
    assert isinstance(crs.Lambert93(), crs.LambertConformal)
    assert isinstance(crs.SIRGAS2000(), crs.Mercator)
