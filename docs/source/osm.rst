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


Writing your own queries
~~~~~~~~~~~~~~~~~~~~~~~~

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

- the ``node``, ``way``, ``rel`` (relation) and ``nwr`` (node-way-relation) keywords. The accept a dictionary specifying the request or a list of dictionaries:

    - the keys in the dictionary refer to the tag to be matched, the values to the value to be set to the tag. If you want to match all values, set it to ``True``:

        .. code:: python

            nwr = dict(leisure="park")

    - if the ``node`` (or ``way``, or ...) must be within a named area, specify the ``area`` keyword;
  
        .. code:: python

            area = {"name": "Helsinki", "as_": "a"},
            nwr = dict(leisure="park", area="a")

    - if the match is not exact, but refers to a regular expression, you may nest a dictionary with the ``regex`` key:

        .. code:: python

            # name must end with park or Park
            nwr = dict(leisure="park", name=dict(regex="[Pp]ark$"))
            # name must be empty
            nwr = dict(leisure="park", name=dict(regex="^$"))

    - use a list if you want several elements:

        .. code:: python

            # get both parks and railway stations
            nwr = [dict(leisure="park", area="a"), dict(railway="station", area="a")]

- any other keyword arguments are collected and passed as a dictionary to the ``nwr`` keyword:

.. code:: python

    # All those notations are equivalent:
    Overpass.request("Helsinki", leisure="park")
    Overpass.request("Helsinki", nwr=dict(leisure="park"))
    Overpass.request("Helsinki", nwr=[dict(leisure="park)])


Post-processing
---------------

Geometry simplification
~~~~~~~~~~~~~~~~~~~~~~~

The ``simplify()`` method associated to GeoPandas dataframes comes from Shapely. Its major default comes from the fact that two neighbouring geometries may be simplified differently on the borders they share.

.. code:: python

    from cartes.osm import Overpass

    toulouse = Overpass.request(
        area={"name": "Toulouse", "admin_level": 8},
        rel={"boundary": "postal_code"}
    )
    
    base = alt.Chart(
        toulouse.assign(
            geometry=toulouse.data.set_crs(epsg=4326)
            # Switch to Lambert93 to simplify (resolution 500m)
            .to_crs(epsg=2154).simplify(5e2)
            # Switch back to WGS84 (lat/lon)
            .to_crs(epsg=4326),
        )
    )

    alt.layer(
        base.mark_geoshape().encode(alt.Color("postal_code:N")),
        base.mark_text(
            color="black", font="Ubuntu", fontSize=14
        ).encode(
            alt.Latitude("latitude:Q"),
            alt.Longitude("longitude:Q"),
            alt.Text("postal_code:N"),
        )

.. raw:: html

    <div id="simplify_naive"></div>

    <script type="text/javascript">
      var spec = "../_static/simplify_naive.json";
      vegaEmbed('#simplify_naive', spec)
      .then(result => console.log(result))
      .catch(console.warn);
    </script>

The Cartes library provies a different ``.simplify()`` method on ``Overpass`` structures:

.. code:: python

    alt.concat(
        *list(
            alt.Chart(toulouse.simplify(resolution=value))
            .mark_geoshape()
            .encode(color="postal_code:N")
            .properties(width=200, height=200, title=f"simplify({value:.0f})")
            for value in [1e2, 5e2, 1e3]
        ),
        columns=2
    )

.. raw:: html

    <div id="simplify_cartes"></div>

    <script type="text/javascript">
      var spec = "../_static/simplify_cartes.json";
      vegaEmbed('#simplify_cartes', spec)
      .then(result => console.log(result))
      .catch(console.warn);
    </script>

Graph colouring
~~~~~~~~~~~~~~~

The four-colour theorem states that you can color a map with no more than 4 colors. If you only base yourself on the name of the regions you will map, you will use many colors, at the risk of looping and use the same (or similar) colors for two neighbouring regions.

The ``Overpass`` object offers as ``.coloring()`` method which builds a NetworkX graph and computes a greedy colouring algorithm on it.

The following map of administrative states of Austria and colours it with both methods. The resulting graph is also accessible via the ``graph`` attribute.


.. raw:: html

    <div id="austria"></div>

    <script type="text/javascript">
      var spec = "../_static/austria.json";
      vegaEmbed('#austria', spec)
      .then(result => console.log(result))
      .catch(console.warn);
    </script>

.. code:: python

    from cartes.osm import Overpass
    import altair as alt

    austria = Overpass.request(
        area=dict(name="Österreich"), rel=dict(admin_level=4)
    ).simplify(5e2).coloring()

    base = alt.Chart(austria)

    labels = base.encode(
        alt.Longitude("longitude:Q"), alt.Latitude("latitude:Q"), alt.Text("name:N"),
    )
    edges = pd.DataFrame.from_records(
        list(
            {
                "lat1": austria[e1].latitude, "lon1": austria[e1].longitude,
                "lat2": austria[e2].latitude, "lon2": austria[e2].longitude,
            }
            for e1, e2 in austria.graph.edges
        )
    )

    alt.vconcat(
        base.mark_geoshape().encode(alt.Color("name:N", scale=alt.Scale(scheme="set2"))),
        alt.layer(
            base.mark_geoshape().encode(
                alt.Color("coloring:N", scale=alt.Scale(scheme="set2"))
            ),
            labels.mark_text(fontSize=13, font="Ubuntu"),
        ),
        alt.layer(
            alt.Chart(edges).mark_line()
            .encode(
                alt.Latitude("lat1"), alt.Longitude("lon1"),
                alt.Latitude2("lat2"), alt.Longitude2("lon2"),
            ),
            base.mark_point(filled=True, size=100).encode(
                alt.Latitude("latitude:Q"), alt.Longitude("longitude:Q"),
                alt.Color("coloring:N", scale=alt.Scale(scheme="set2"),
            ),
            labels.mark_text(fontSize=13, font="Ubuntu", dy=-10),
        ),
    ).resolve_scale(color="independent")

Distances and areas
~~~~~~~~~~~~~~~~~~~

The methods ``.area()`` and ``.length()`` compute the area (resp. the length) of each geometry in square meters (resp. meters). They can be useful to select, sort or visualise geometries based on this criterion.

In the following example, we sort Helsinki public parks by size:

.. code:: python

    parks.area().sort_values("area", ascending=False)

.. raw:: html
    :file: ./_static/helsinki_parks_area.html

With the ``.length()`` method, we can imagine the following use case to filter rivers by their length:

.. code:: python

    riviera = Overpass.request(
        area={"name": "Alpes-Maritimes", "as_": "a"},
        rel=[
            dict(area="a"),  # the administrative region
            dict(waterway="river", area="a")  # the rivers
        ],
    ).simplify(5e2)

    alt.layer(
        # The administrative region
        alt.Chart(riviera.query('boundary=="administrative"'))
        .mark_geoshape(fill="lightgray"),
        # The rivers
        alt.Chart(
            riviera.query('waterway=="river"').length()
            # at least 20k long, and remove one going to a different drainage basin
            .query("length > 20_000 and id_ != 7203495")
        )
        .mark_geoshape(filled=False)
        .encode(alt.Tooltip("name:N")),
    ).properties(
        width=400, height=400, title="Main rivers of French Riviera"
    ).configure_title(
        font="Fira Sans", fontSize=16, anchor="start"
    )

.. raw:: html

    <div id="riviera"></div>

    <script type="text/javascript">
      var spec = "../_static/riviera.json";
      vegaEmbed('#riviera', spec)
      .then(result => console.log(result))
      .catch(console.warn);
    </script>