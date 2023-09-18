from cartopy.feature import NaturalEarthFeature

# Some convenient features with overridable decent default parameters.

# TODO: themes


def countries(**kwargs) -> NaturalEarthFeature:
    params = {
        "category": "cultural",
        "name": "admin_0_countries",
        "scale": "10m",
        "edgecolor": "#524c50",
        "facecolor": "none",
        "alpha": 0.5,
        **kwargs,
    }
    return NaturalEarthFeature(**params)


def rivers(**kwargs) -> NaturalEarthFeature:
    params = {
        "category": "physical",
        "name": "rivers_lake_centerlines",
        "scale": "10m",
        "edgecolor": "#226666",
        "facecolor": "none",
        "alpha": 0.2,
        **kwargs,
    }
    return NaturalEarthFeature(**params)


def lakes(**kwargs) -> NaturalEarthFeature:
    params = {
        "category": "physical",
        "name": "lakes",
        "scale": "10m",
        "edgecolor": "#226666",
        "facecolor": "#226666",
        "alpha": 0.2,
        **kwargs,
    }
    return NaturalEarthFeature(**params)


def ocean(**kwargs) -> NaturalEarthFeature:
    params = {
        "category": "physical",
        "name": "ocean",
        "scale": "10m",
        "edgecolor": "#226666",
        "facecolor": "#226666",
        "alpha": 0.2,
        **kwargs,
    }
    return NaturalEarthFeature(**params)
