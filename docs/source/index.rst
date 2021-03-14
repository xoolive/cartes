Cartes
======

Source code on `github <https://github.com/xoolive/cartes>`_.

Cartes is a Python library providing **facilities to produce meaningful maps**.

Cartes builds on top of most common Python visualisation libraries (Matplotlib/Cartopy, Altair, ipyleaflet) and data manipulation libraries (Pandas, Geopandas) and provides mostly:

- a **comprehensive set of geographic projections**, built on top of Cartopy and Altair/d3.js;
- an **interface to OpenstreetMap Nominatim and Overpass API**. Result of requests are parsed in a convenient format for preprocessing and storing in standard formats;
- **beautiful default parameters** for quality visualisations;
- **advanced caching facilities**. Do not download twice the same content in the same day.

The cartes library is a powerful asset to publish clean, lightweight geographical datasets; and to produce decent geographical visualisations in few lines of code.


.. toctree::
   :maxdepth: 1

   installation
   projections
   osm
   visualisation
   gallery
   troubleshooting
   alternatives

