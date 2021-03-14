OpenStreetMap
=============

The library offers some facilities to request and parse the results from the OpenStreetMap Nominatim (search engine) and Overpass (map data database) API.

Nominatim API
-------------

You may search for a name or address (forward search) or look up data by its geographic coordinate (reverse search) or by its OpenStreetMap identifier. 

- forward search (from natural language name):

    .. code:: python

        from cartes.osm import Nominatim

        Nominatim.search("Isola di Capri")

    .. raw:: html
        :file: ./_static/capri.html

    You may access the underlying JSON information

    .. code:: python

        Nominatim.search("Isola di Capri").json

    .. code:: json

        {
          "place_id": 257200499,
          "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
          "osm_type": "relation",
          "osm_id": 2675353,
          "boundingbox": ["40.5358786", "40.5618457", "14.1957565", "14.2663337"],
          "lat": "40.54877475",
          "lon": "14.22808744705355",
          "display_name": "Capri, Anacapri, Napoli, Campania, Italia",
          "place_rank": 17,
          "category": "place",
          "type": "island",
          "importance": 0.6198426309338769,
          "address": {
            "place": "Capri",
            "village": "Anacapri"
            // truncated
           }
        }


- reverse search (from lat/lon coordinates):

    .. code:: python

        Nominatim.reverse(51.5033, -0.1277)

    .. raw:: html
        :file: ./_static/downing_street.html
  
- lookup search, if you know the identifier:

    .. code:: python

        Nominatim.lookup("R9946787")

    .. raw:: html
        :file: ./_static/eyjafjallajokull.html

Overpass API
------------

The Overpass API is a read-only API to selected parts of the OpenStreetMap data. It acts as a database where the end user can send queries using a dedicated `query language` (`Overpass QL <https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_API_by_Example>`_) in order to collect nodes, ways and relations referenced in OpenStreetMap.

The cartes library offers a direct access, with some helpers to generate the queries from a more natural Python call. The whole Overpass QL possibilities are not covered, but most simple use cases are.

Overpass QL "as is"
~~~~~~~~~~~~~~~~~~~

If you know how to write your query in Overpass QL, you can still benefit from the caching and parsing possibilities of the library with the query argument:

.. code:: python

    from cartes.osm import Overpass

    parks = Overpass.request(query="""[out:json];
    area[name="Helsinki"];
    way(area)["leisure"="park"];
    map_to_area->.a;
    (
     node(area.a)[leisure=playground];
     way(area.a)[leisure=playground];
    );
    foreach(
      (._;>;);
      is_in;
      way(pivot)["leisure"="park"];
      out geom;
    );""")

    parks

.. raw:: html
    :file: ./_static/helsinki_parks.html


.. warning::

    The representation calls the underlying Geopandas DataFrame generated upon parsing. You have access to several attributes:

    - ``parks.data`` returns the Geopandas DataFrame;
    - ``parks.json`` returns the raw JSON data received.


A simple request for Query Language (QL) illiterate people
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

| This request selects all parks within Helsinki area where playgrounds for kids are available. 
| **With Cartes, it is possible to generate a simpler request like "select all parks within Helsinki area"**.

.. code::

    # That's all folks
    parks = Overpass.request(area="Helsinki", leisure="park")

    # You may check/debug the generated request as follows.
    Overpass.build_query(area="Helsinki", leisure="park")

    #   >> returns:
    # [out:json][timeout:180];rel(id:34914);map_to_area;nwr(area)[leisure=park];out geom;

Note that unlike with the first (complicated) query above, the name ``"Helsinki"`` does not appear in the request as we use a Nominatim call first to identify the area (which can prove helpful when the name field does not use a familiar alphabet). It is possible to write the following for a closer result:

.. code::

    Overpass.build_query(area={"name": "Helsinki"}, leisure="park")

    #   >> returns:
    # [out:json][timeout:180];area[name=Helsinki];nwr(area)[leisure=park];out geom;


Making your own queries
~~~~~~~~~~~~~~~~~~~~~~~

.. warning::

    The API may change in the coming weeks. Different use cases may lead to different specifications.

The arguments to the requests function are:

- the optional ``query`` argument, for raw Overpass QL queries. If this argument is not ``None``, then all other arguments are ignored;
- the optional ``bounds`` argument can be a tuple of four floats (west, south, east, north), a ``Nominatim`` object or any other object following the ``__geo_interface__`` protocol. The bounds apply to the whole query;

  .. danger::

    The coordinate order to input here is **(west, south, east, north)**. It will be converted to (south, west, north, east) for the Overpass QL.

  .. code:: python

    bounds = (24.8, 60.15, 25.16, 60.28)
    bounds = Nominatim("Helsinki")
    bounds = parks
    bounds = Polygon(...)  # from shapely.geometry import Polygon

- the optional ``area`` argument can be a string, a Nominatim object or a dictionary of elements used to identify the area. The most commonly used tag is probably ``name``.

  .. code:: python

    area = "Helsinki"
    area = Nominatim("Helsinki")
    area = {"name": "Helsinki, "admin_level": 8}
    area = {"name:ru": "Хельсинки"}

It is possible to specify the ``as_`` argument in order to name (and reuse) the given area:

  .. code:: python

    area = {"name": "Helsinki", "as_": "a"}

- the ``node``, ``way``, ``rel`` (relation) and ``nwr`` (node-way-relation) keywords:

    .. hint::

        TODO

- any other keyword arguments are collected and passed as a dictionary to the ``nwr`` keyword:

  .. code:: python

    # All those notations are equivalent:
    Overpass.request("Helsinki", leisure="park")
    Overpass.request("Helsinki", nwr=dict(leisure="park"))
    Overpass.request("Helsinki", nwr=[dict(leisure="park)])


Post-processing
---------------

.. hint::

    TODO

- simplify()  # toulouse code_postal

- coloring()  # redirect Bayern

- area()   # sorted -> parks?

- length()  # rivières

