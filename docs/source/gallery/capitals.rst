European (major) capitals
=========================

.. raw:: html

    <div id="capitals"></div>

    <script type="text/javascript">
      var spec = "../_static/gallery/capitals.json";
      vegaEmbed('#capitals', spec)
      .then(result => console.log(result))
      .catch(console.warn);
    </script>

Data acquisition
----------------

Download nodes from capital cities in a given bounding box (west, south, east, north)

.. code:: python

    from cartes.osm import Overpass

    capitals = Overpass.request(
        bounds=(-30, 33, 35, 70),
        node={"capital": "yes"}
    )

Data preprocessing
------------------

None

Data visualisation
------------------

.. code:: python

    import altair as alt
    from vega_datasets import data

    # Capital cities information
    base = alt.Chart(capitals).encode(
        alt.Tooltip(["name:N", "population:Q"]),
        alt.Text("name:en:N"),
    )

    # Data generators for the background
    sphere = alt.sphere()
    graticule = alt.graticule()

    # Source of land data
    source = alt.topo_feature(data.world_110m.url, "countries")


    alt.layer(
        # First the graticule for the projection
        alt.Chart(alt.graticule()).mark_geoshape(stroke="lightgray"),
        # The map
        alt.Chart(source).mark_geoshape(fill="lightgray", stroke="black"),
        # The points for locating the cities
        base.mark_geoshape().encode(alt.Color("population:Q")),
        # City names if population is above 300k
        base.mark_text(font="Ubuntu", fontSize=12, dy=10, align="center")
        .encode(alt.Latitude("latitude:Q"), alt.Longitude("longitude:Q"))
        .transform_filter("datum.population > 300000"),
    ).properties(
        width=500, height=400, title="European (major) Capitals"
    ).configure_title(
        font="Fira Sans", fontSize=16, anchor="start"
    ).project(
        # The projection (coming soon as crs)
        "conicConformal",
        rotate=[-15, -52, 0],
        parallels=[35, 65],
        scale=400,
    )
