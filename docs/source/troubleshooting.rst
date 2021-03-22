Troubleshooting
===============

HTTP Error 429
--------------

You may be subject to quotas when you send numerous requests to the Overpass API. If you get this error, you will see the result of a call to `<https://overpass-api.de/api/status>`_ with details about your quota and next available slots:

.. code:: text

    Connected as: 866011160
    Current time: 2021-03-15T09:14:16Z
    Rate limit: 2
    Slot available after: 2021-03-15T09:30:24Z, in 968 seconds.
    Currently running queries (pid, space limit, time limit, start time):
    14803	536870912	180	2021-03-15T09:12:33Z

NotImplementedError
-------------------

You may encounter this kind of exception:

.. code:: python

    NotImplementedError: The parser for site is not implemented yet.
    If you feel enthusiastic, you may implement a class Site which inherits from Relation
    and knows how to parse this relation.

This simply means that a parser for the particular type of relation called ``site`` is not yet implemented.
You may have a look at files in the ``osm/overpass/relations`` directory (e.g. ``MultiPolygon`` or ``Waterway``).

An empty class in your code inheriting from ``Relation`` should be enough to bypass the exception, but only a proper implementation will parse the content received from the Overpass API.

.. code:: python

    from cartes.osm.overpass.core import Relation

    class Site(Relation):
        pass

        