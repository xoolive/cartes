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

.. tip::

    See also: `Projections in Altair <altair.html>`_