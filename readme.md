# Cartes


![build](https://github.com/xoolive/cartes/workflows/build/badge.svg)
![docs](https://github.com/xoolive/cartes/actions/workflows/github-pages.yml/badge.svg)
[![Code Coverage](https://img.shields.io/codecov/c/github/xoolive/cartes.svg)](https://codecov.io/gh/xoolive/cartes)
[![Checked with mypy](https://img.shields.io/badge/mypy-checked-blue.svg)](https://mypy.readthedocs.io/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-black.svg)](https://github.com/psf/black)

Cartes is a Python library providing facilities to produce meaningful maps.

Cartes builds on top of most common Python visualisation libraries (Matplotlib/Cartopy, Altair, ipyleaflet) and data manipulation libraries (Pandas, Geopandas) and provides mostly:

- a **comprehensive set of geographic projections**, built on top of Cartopy and Altair/d3.js;
- an **interface to OpenstreetMap Nominatim and Overpass API**. Result of requests are parsed in a convenient format for preprocessing and storing in standard formats;
- beautiful **default parameters** for quality visualisations;
- **advanced caching facilities**. Do not download twice the same content in the same day.

The cartes library is a powerful asset to **publish clean, lightweight geographical datasets**; and to **produce decent geographical visualisations** in few lines of code.

## Example

## Installation

Latest release:

_(coming soon)_

Development version:

```sh
pip install git+https://github.com/xoolive/cartes
```

## Documentation

![docs](https://github.com/xoolive/cartes/actions/workflows/github-pages.yml/badge.svg)

Documentation available at https://cartes-viz.github.io/
