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
