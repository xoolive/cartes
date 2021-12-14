CRS and projections
===================

Cartopy provides few default projections, documented on their `webpage <https://scitools.org.uk/cartopy/docs/latest/crs/projections.html>`_. Cartes extends these definitions with a full set of projections as defined by the ``libproj`` C library.

Introduction example
--------------------

For instance, the Lambert93 projection is the default official one in France, used for tiles by the National Geographic Institute (IGN).

.. code:: python

    from cartes.crs import Lambert93
    Lambert93()

.. raw:: html
    :file: _static/lambert93.html 

As displayed above, Lambert93 is nothing more than an alias for an EPSG specification. It is possible to obtain the same result with the following code.


.. code:: python

    from cartes.crs import EPSG_2154
    EPSG_2154()

.. warning::

    Classes are generated dynamically based on their description in the ``libproj`` library. A star import would not work here.

Valid projections at a given location
-------------------------------------

A list of valid projections is available with a call to the ``valid_crs`` functioni which accepts a string or any object implementing the ``__geo_interface__`` protocol:

.. code:: python

    from cartes.crs import valid_crs
    valid_crs("Rome, Italy")

.. raw:: html
    :file: _static/crs_rome.html

You can then pick one for your future needs:

.. code:: python

    from cartes.crs import EPSG_3034
    EPSG_3034()

.. raw:: html
    :file: _static/epsg_3034.html 

Adjusting bounds for a projection
---------------------------------

Some definitions in the library set very narrow bounds which are then incompatible with plotting in a larger area. It is possible to set different bounds by subclassing the projection. 


.. code:: python

    from cartes import crs
    crs.EPSG_6674()

.. raw:: html
    :file: _static/epsg_6674.html

.. code:: python

    class Custom(crs.EPSG_6674):
        bbox = {
            "east_longitude": 151,
            "north_latitude": 47,
            "south_latitude": 25,
            "west_longitude": 124,
        }

    Custom()

.. raw:: html
    :file: _static/crs_custom.html

Use custom projection in Altair
-------------------------------

Projections can be passed to the ``.project()`` method with the ``**`` unpacking
operator. Note that not all projections defined in custom have an equivalent in
Altair, in which case an exception could be raised.

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
        .configure_title(font="Fira Sans", fontSize=14, anchor="start")
        .configure_legend(orient="bottom", columns=6)
    )
