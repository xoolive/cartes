Atlas
=====

Introduction
------------

Cartes comes with a facilitated access to repositories of topojson files online.
topojson is a very lightweight format compared to geojson, so it is excellent
for transferring files over the Internet, and for a direct integration in
Altair.

Currently we have two major repositories for maps:

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - name
     - repository
     - type
   * - ``default``
     - `https://github.com/deldersveld/topojson <https://github.com/deldersveld/topojson>`_
     - Github
   * - ``world_atlas``
     - `https://cdn.jsdelivr.net/npm/world-atlas@2/ <https://cdn.jsdelivr.net/npm/world-atlas@2/>`_
     - npm


The list of maps available in each repository is available with each module:

.. jupyter-execute::

    from cartes.atlas import default

    default

Filtering the atlas collection
------------------------------

You can filter the table with regular accessors:

.. jupyter-execute::

    default.europe  # equivalent to from cartes.atlas import europe


When only one element is left, you can access:

- | a ``topo_feature`` element, for a direct access in Altair.
  | Here, data is not included in the Altair JSON, only a link to the url.

- | a ``data`` element for the corresponding Geopandas dataframe.
  | This option is comfortable for exploring data, or for further postprocessing.


.. jupyter-execute::

    import altair as alt

    from cartes.atlas import europe
    from cartes.crs import EuroPP

    (
        alt.Chart(europe.topo_feature)
        .mark_geoshape(stroke="white")
        .project(**EuroPP())
        .configure_view(stroke=None)
        .properties(width=400, height=400)
    )

Corresponding data is available, and stored in cache:

.. jupyter-execute::

    europe.data.head()

It is possible to chain filtering:

.. jupyter-execute::

    from cartes.atlas import japan  # or from cartes.atlas.default import japan

    japan

.. jupyter-execute::

    japan.towns

Simple maps
-----------

The ``data`` attribute is convenient to explore data and create a first visualisation:

.. jupyter-execute::

    japan.towns.data.query('NAME_1 == "Shiga"').iloc[:15, :10]

.. jupyter-execute::

    from cartes.crs import JGD2000

    (
        alt.Chart(japan.towns.data.query('NAME_1 == "Shiga"'))
        .mark_geoshape(stroke="white")
        .encode(
            color=alt.condition(
                "datum.ENGTYPE_2 == 'Water body'",
                alt.value("steelblue"),
                alt.value("#bab0ac"),
            ),
            tooltip=alt.Tooltip("NAME_2"),
        )
        .project(**JGD2000())
        .configure_view(stroke=None)
        .properties(width=400, height=400)
    )

.. tip::
    If no postprocessing has been done on geometry, consider coming back to the
    ``topo_feature``.

.. jupyter-execute::

    (
        alt.Chart(default.japan.towns.topo_feature)
        .mark_geoshape(stroke="white")
        .encode(
            color=alt.condition(
                "datum.properties.ENGTYPE_2 == 'Water body'",
                alt.value("steelblue"),
                alt.value("#bab0ac"),
            ),
            tooltip=alt.Tooltip("properties.NAME_2:N"),
        )
        .transform_filter("datum.properties.NAME_1 == 'Shiga'")
        .project(**JGD2000())
        .configure_view(stroke=None)
        .properties(width=400, height=400)
    )

.. warning::

    Note how the ``.query()`` becomes a ``.transform_filter()`` and how feature
    names are then prefixed with ``properties.``


Tricks for filtering
--------------------

- A final ``_`` in a filtering attribute negates it:

  .. jupyter-execute::

      from cartes.atlas import world

      world.countries

  .. jupyter-execute::

      world.countries.sans_ 


- An attribute starting with a number yields a ``SyntaxError``. Use the ``_`` prefix:

  .. jupyter-execute::

      from cartes.atlas import world_atlas

      world_atlas.countries._10


.. tip::

    If you can't find a work-around a special argument, try the ``.q()`` method
    and forget about ``SyntaxError``:

    .. jupyter-execute::

        world_atlas.q("countries").q("-10")
