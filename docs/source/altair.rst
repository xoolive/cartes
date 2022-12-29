Altair
======


How to use projections in Altair?
---------------------------------

A set of predetermined projection is available in Vega (`documentation
<https://vega.github.io/vega/docs/projections/>`_, therefore in Altair, but
they can be lacking, especially for local scales.

`Projections <projections.html>`_ can be passed to the ``.project()`` method
with the ``**`` unpacking operator. Note that not all projections defined in
custom have an equivalent in Altair, in which case an exception could be raised.

.. jupyter-execute::

    import altair as alt
    from vega_datasets import data

    from cartes.crs import (
        Orthographic,
        GeoscienceAustraliaLambert,
        EPSG_3348,
        UTM,
    )

    world = alt.topo_feature(data.world_110m.url, "countries")
    base = alt.Chart(world).mark_geoshape(stroke="white").properties(width=200, height=200)

    (
        alt.concat(
            base.project("mercator").properties(title="Mercator"),
            base.project(**Orthographic()).properties(title="Orthographic"),
            base.project(**Orthographic(110, 35)).properties(title="Orthographic(110, 35)"),
            base.project(**GeoscienceAustraliaLambert())
            .properties(title="Geoscience Australia Lambert")
            # https://en.wikipedia.org/wiki/ISO_3166-1_numeric
            .transform_filter("datum.id == 36"),
            base.project(**EPSG_3348())
            .properties(title="EPSG:3348")
            .transform_filter("datum.id == 124"),
            base.project(**UTM(47))
            .properties(title="UTM(47)")
            .transform_filter("datum.id == 356"),
            columns=3,
        )
        .configure_view(stroke=None)
        .configure_title(font="Fira Sans, Lato, sans-serif", fontSize=14, anchor="start")
        .configure_legend(orient="bottom", columns=6)
    )

How to clip data to a bounding box?
-----------------------------------

Such support is very limited. To my knowledge, such computation is not available
in Altair.

However, we can explore different possibilities with Geopandas.
But first, the data, together with the definition of a bounding box.

.. jupyter-execute::

    from cartes.crs import EuroPP, Orthographic
    from cartes.atlas import world
    from shapely.geometry import box
    import altair as alt

    data = world.countries.sans_.data
    projection = EuroPP()

    west, east, south, north = extent = (-20, 40, 30, 80)
    bounding_box = box(west, south, east, north)
    graticule = alt.graticule(extent=((west, south), (east + .01, north + .01)))

    alt.layer(
        alt.Chart(world.countries.sans_.topo_feature)
        .mark_geoshape(stroke="white")
        .project(**Orthographic(10, 55)),
        alt.Chart(bounding_box).mark_geoshape(color="#bab0ac99"),
    ).configure_view(stroke=None)

A first naive (necessary) approach would be to filter out all features not
intersecting the bounding box:

.. jupyter-execute::

    alt.layer(
        alt.Chart(data.loc[data.intersects(bounding_box)])
        .mark_geoshape(stroke="white")
        .project(**projection),
        alt.Chart(graticule).mark_geoshape(color="#bab0ac"),
    ).configure_view(stroke=None)

This is obviously not ideal, even putting Russia aside.

.. tip::

    Another option would be to compute the intersections of all features with
    the bounding box: that is what the ``.extent()`` method is for. This method
    is monkey-patched to Geopandas dataframe upon loading of the cartes library.


.. jupyter-execute::

    (
        alt.hconcat(
            alt.layer(
                alt.Chart(data.extent(extent))
                .mark_geoshape(stroke="white")
                .project(**projection)
                .properties(title="data.extent(extent)"),
                alt.Chart(graticule).mark_geoshape(color="#bab0ac"),
            ),
            alt.layer(
                alt.Chart(data.extent(extent, projection))
                .mark_geoshape(stroke="white")
                .properties(width=300, title="data.extent(extent, projection)"),
                alt.Chart(graticule).mark_geoshape(color="#bab0ac"),
            ),
        )
        .configure_view(stroke=None)
        .configure_title(
            font="Inconsolata, Liberation Mono, Monaco, monospace", fontSize=16
        )
    )


.. warning::

    Compare the two maps: it is important to reinject the projection to the
    ``.extent()`` method so as the bounding box is recomputed in the projected
    space, and ported back to a lat/lon shape.

.. tip::

    The ``.extent()`` method accepts any extent tuple, shape or text to be
    passed to the `Nominatim <osm.html#nominatim-api>`_ API. A ``buffer``
    argument helps adjusting those bounds.


.. jupyter-execute::

    import geopandas as gpd

    # Not ideal... for now!
    github_url = "https://raw.githubusercontent.com/{user}/{repo}/master/{path}"
    communes = gpd.GeoDataFrame.from_file(
        github_url.format(
            user="gregoiredavid",
            repo="france-geojson",
            path="communes.geojson",
        )
    )

    (
        alt.layer(
            alt.Chart(communes.extent("Hyères", projection, buffer=0.2))
            .mark_geoshape(stroke="white", strokeWidth=1.5, opacity=0.9)
            .encode(
                color=alt.condition(
                    "datum.nom == 'Hyères'", alt.value("#f58518"), alt.value("#bab0ac")
                ),
                tooltip=alt.Tooltip("nom:N"),
            )
            .project(**projection),
            alt.Chart(
                communes.query('nom == "Hyères"').assign(
                    lat=lambda df: df.centroid.y, lon=lambda df: df.centroid.x
                )
            )
            .mark_text()
            .encode(alt.Text("nom"), alt.Latitude("lat"), alt.Longitude("lon")),
        )
        .configure_view(stroke=None)
        .configure_text(font="Fira Sans, Lato, sans-serif", size=18)
        .properties(width=600, height=500)
    )
