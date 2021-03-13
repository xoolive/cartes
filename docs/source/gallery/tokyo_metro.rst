Tokyo metro map
===============

This example is obviously inspired by the example of London Tube Lines in the `Altair <https://altair-viz.github.io/gallery/london_tube.html>`_ and `Vega-Lite <https://vega.github.io/vega-lite/examples/geo_layer_line_london.html>`_ documentations.

It can feel a bit frustrating when discovering those libraries not to be able to extend it easily to other cities. We pick Tokyo here, and spice it up with a bilingual map (mostly in Japanese, but English appears with the mouse.)

.. warning::

    - It may happen that the visualisation is rendered before the fonts are downloaded. In case such thing happens, a simple refresh (F5) should be enough to fix things.
    - A close up map is built in the `corresponding section <#zoom-in-to-downtown-tokyo>`_.

.. raw:: html

    <div id="tokyo_global"></div>

    <script type="text/javascript">
      var spec = "../_static/gallery/tokyo_global.json";
      vegaEmbed('#tokyo_global', spec)
      .then(result => console.log(result))
      .catch(console.warn);
    </script>


Data acquisition
----------------

We will take two different datasets from OpenStreetMap: background information (the 23 Tokyo wards) and the subway lines. For people familiar with Tokyo subway systems, this does not include the JR lines (incl. Yamanote line).

.. code:: python

    from cartes.osm import Overpass

    tokyo_wards = Overpass.request(
        area={"name:en": "Tokyo", "admin_level": 4},
        # Level 7 include cities (市) and wards (区)
        rel=dict(admin_level=7, name=dict(regex="区$")),
    )

    tokyo_subway = Overpass.request(
        area={"name:en": "Tokyo", "admin_level": 4, "as_": "tokyo"},
        nwr=[
            dict(railway="subway", area="tokyo"),  # subway lines
            dict(station="subway", area="tokyo"),  # subway stations
        ],
    )


Data preprocessing
------------------

The map background needs to be simplified, we do not need details at very fine resolution, which would also be heavy to download.

.. code:: python

    tokyo_wards = tokyo_wards.simplify(1e3)



There are some glitches in the metadata associated to the line segments, so there are two solutions:

- edit the faulty segments on OpenStreetMap;
- preprocess the data to correct those mistakes.

.. code:: python

    lines = tokyo_subway.data.query("type_ == 'way' and name == name").assign(
        name=lambda df: df.name.str.split(" ", n=1, expand=True)
    )
    lines.loc[lines["name:en"] == "Toei Mita Line", "name"] = "都営地下鉄三田線"
    lines.loc[lines["name:en"] == "Toei Asakusa Line", "name"] = "都営地下鉄浅草線"
    lines.loc[lines["name"] == "京王電鉄京王線", "name:en"] = "Keio Railway Keio Line"

We collect the official colours associated to each lines from segments where the tag is filled:

.. code:: python

    colours = (
        lines[["name", "name:en", "colour"]]
        .query("colour==colour")
        .groupby("name")
        .agg({"name:en": "max", "colour": "max"})
        .reset_index()
    )

.. raw:: html

    <table border="0" class="dataframe">
    <thead>
      <tr style="text-align: right;">
        <th></th>
        <th>name</th>
        <th>name:en</th>
        <th>colour</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <th>0</th>
        <td>東京メトロ丸ノ内線</td>
        <td>Tokyo Metro Marunouchi Line</td>
        <td>#F62E36</td>
      </tr>
      <tr>
        <th>1</th>
        <td>東京メトロ副都心線</td>
        <td>Tokyo Metro Fukutoshin Line</td>
        <td>#B74D17</td>
      </tr>
      <tr>
        <th>2</th>
        <td>東京メトロ千代田線</td>
        <td>Tokyo Metro Chiyoda Line</td>
        <td>#00BB85</td>
      </tr>
      <tr>
        <th>3</th>
        <td>東京メトロ半蔵門線</td>
        <td>Tokyo Metro Hanzomon Line</td>
        <td>#8F76D6</td>
      </tr>
      <tr>
        <th>4</th>
        <td>東京メトロ南北線</td>
        <td>Tokyo Metro Namboku Line</td>
        <td>#00AC9B</td>
      </tr>
      <tr>
        <th>5</th>
        <td>東京メトロ日比谷線</td>
        <td>Tokyo Metro Hibiya Line</td>
        <td>#B5B5AC</td>
      </tr>
      <tr>
        <th>6</th>
        <td>東京メトロ有楽町線</td>
        <td>Tokyo Metro Yurakucho Line</td>
        <td>#C1A470</td>
      </tr>
      <tr>
        <th>7</th>
        <td>東京メトロ東西線</td>
        <td>Tokyo Metro Tōzai Line</td>
        <td>#0CA7ED</td>
      </tr>
      <tr>
        <th>8</th>
        <td>東京メトロ銀座線</td>
        <td>Tokyo Metro Ginza Line</td>
        <td>#FF9500</td>
      </tr>
      <tr>
        <th>9</th>
        <td>都営地下鉄三田線</td>
        <td>Toei Mita Line</td>
        <td>#0079C2</td>
      </tr>
      <tr>
        <th>10</th>
        <td>都営地下鉄大江戸線</td>
        <td>Toei Oedo Line</td>
        <td>#B6007A</td>
      </tr>
      <tr>
        <th>11</th>
        <td>都営地下鉄新宿線</td>
        <td>Toei Shinjuku Line</td>
        <td>#6CBB5A</td>
      </tr>
      <tr>
        <th>12</th>
        <td>都営地下鉄浅草線</td>
        <td>Toei Asakusa Line</td>
        <td>#E85298</td>
      </tr>
    </tbody>
  </table>

Then we merge the lines into single elements, also in order to reduce the size of resulting JSON. Line simplification does not really work well here if we want subway lines to still go through the stations.

.. code:: python

    from shapely.ops import linemerge

    def merge_line(elt):
        return pd.Series(
            {
                "geometry": linemerge(elt.geometry.tolist()),
                "name:en": elt["name:en"].max(),
            }
        )

    lines = (
        lines[["name", "name:en", "geometry"]]
        .groupby("name").apply(merge_line).reset_index()
    )


Data visualisation
------------------

.. code:: python

    import altair as alt

    # First the colors
    line_scale = alt.Scale(
        domain=colours["name:en"].tolist(),
        range=colours["colour"].tolist()
    )

    wards = alt.Chart(tokyo_wards)

    basemap = alt.layer(
        # The background
        wards.mark_geoshape(color="gainsboro", stroke="white", strokeWidth=1.5),
        # The names of the wards: in Japanese, the in English under the mouse pointer
        wards.mark_text(fontSize=16, font="Noto Sans JP", fontWeight=100).encode(
            alt.Text("name:N"), alt.Tooltip("name:ja-Latn:N"),
            alt.Latitude("latitude:Q"), alt.Longitude("longitude:Q"),
        ),
        # The subway lines: in English in the legend, bilingual under the mouse pointer
        alt.Chart(lines).mark_geoshape(filled=False, strokeWidth=2)
        .encode(
            alt.Color(
                "name:en:N", scale=line_scale,
                legend=alt.Legend(
                    title=None, orient="bottom-left", offset=0, columns=2,
                    labelFont="Ubuntu", labelFontSize=12,
                ),
            ),
            alt.Tooltip(["name:N", "name:en:N"]),
        ),
        # Subway stations positions
        alt.Chart(tokyo_subway.query("station == station"))
        .mark_circle(size=30, color="darkslategray")
        .encode(
            alt.Latitude("latitude:Q"), alt.Longitude("longitude:Q"),
            alt.Tooltip(["name:N", "name:en:N"]),
        ),
    ).properties(width=600, height=600)

    basemap

Zoom in to downtown Tokyo
-------------------------

.. raw:: html

    <div id="tokyo_central"></div>

    <script type="text/javascript">
      var spec = "../_static/gallery/tokyo_central.json";
      vegaEmbed('#tokyo_central', spec)
      .then(result => console.log(result))
      .catch(console.warn);
    </script>


On this map, we choose to:

- specify a projection centered on the central wards in order to be able to zoom in;
- display the station names in small characters;
- add the Yamanote line (in pale green).

.. code:: python

    # Collect the Yamonote line
    tokyo_yamanote = Overpass.request(
        area={"name:en": "Tokyo", "admin_level": 4},
        way=dict(railway=True, name=dict(regex="山手線$")),
    )

    # The geometry will be enough here
    yamanote = linemerge(tokyo_yamanote.data.geometry.to_list())

    alt.layer(
        # Recall previous visualisation
        default,  
        # Some stations appear several times (once per exit?)
        alt.Chart(tokyo_stations.data.drop_duplicates("name"))
        .mark_text(fontSize=12, font="Noto Sans JP", fontWeight=100)
        .encode(
            alt.Text("name:N"), alt.Tooltip(["name:N", "name:en:N"]),
            alt.Latitude("latitude:Q"), alt.Longitude("longitude:Q"),
        ),
        # Yamanote line
        alt.Chart(yamanote).mark_geoshape(
            strokeWidth=10, opacity=0.3, color="#B1CB39", filled=False
        )
    ).project(
        # based on the coordinates of the map center
        "conicConformal", rotate=[-139.77, -35.68], scale=450000
    ).configure_legend(
        # there is not much space for the legend, so hide what's behind
        fillColor="gainsboro", padding=10
    )
