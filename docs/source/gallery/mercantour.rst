Peaks in Mercantour National Park
=================================

.. raw:: html

    <div id="mercantour"></div>

    <script type="text/javascript">
      var spec = "../_static/gallery/mercantour.json";
      vegaEmbed('#mercantour', spec)
      .then(result => console.log(result))
      .catch(console.warn);
    </script>

Data acquisition
----------------

- Get the administrative boundaries and major rivers (see `here <osm.html#distances-and-areas>`_)

- Get the peaks inside the Mercantour National Park

.. code:: python

    from cartes.osm import Overpass

    riviera = Overpass.request(
        area={"name": "Alpes-Maritimes", "as_": "a"},
        rel=[
            dict(area="a"),  # the administrative region
            dict(waterway="river", area="a")  # the rivers
        ],
    ).simplify(5e2)


    mercantour = Overpass.request(
        area=dict(
            boundary="protected_area",
            name=dict(regex="Mercantour"),
            as_="a",
        ),
        # The area
        rel=dict(area="a"),
        # The peaks
        node=dict(natural="peak", area="a"),
    )


Data visualisation
------------------

.. code:: python

    import altair as alt

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
        # The National park (simplified)
        alt.Chart(
            mercantour.query('boundary == "protected_area"').simplify(5e2)
        ).mark_geoshape(
            fill="darkseagreen",
            opacity=0.5,
            stroke="darkseagreen",
            strokeWidth=1.5,
        ),
        # The peaks
        alt.Chart(mercantour.query('natural == "peak"'))
        .encode(
            alt.Latitude("latitude:Q"), alt.Longitude("longitude:Q"),
            alt.Tooltip("name:N"),
            alt.Color(
                "ele:Q", title="Altitude (m)",
                scale=alt.Scale(scheme="darkmulti", domain=(1000, 3000), type="log"),
            ),
        )
        .mark_point(size=50, shape="triangle-up"),
    ).properties(
        width=400, height=400, title="Sommets du Massif du Mercantour"
    ).configure_title(
        font="Fira Sans", fontSize=16, anchor="start"
    )