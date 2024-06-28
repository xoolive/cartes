License plate codes in Bavaria
==============================

License plates on cars in Germany start with a one, two or three letter codes  corresponding (roughly) to small administrative circonscriptions. The keyword for Wikipedia is `Kfz-Kennzeichen <https://de.wikipedia.org/wiki/Liste_der_Kfz-Kennzeichen_in_Deutschland>`_.

.. warning::

    A more comprehensive map with coats of arms is constructed in the `corresponding section <#coats-of-arms>`_.

.. raw:: html

    <div id="bayern"></div>

    <script type="text/javascript">
      var spec = "../_static/gallery/bayern.json";
      vegaEmbed('#bayern', spec)
      .then(result => console.log(result))
      .catch(console.warn);
    </script>


Data acquisition
----------------

Download all district (`Kreisen`) borders for Bavaria (Bayern in German)

.. code:: python

    from cartes.osm import Overpass

    bayern = Overpass.request(
        # There are other ways to select Bavaria, esp. with name.
        # ISO codes are reliable though
        area={"ISO3166-2": "DE-BY", "admin_level": 4, },
        rel={ "boundary": "administrative", "admin_level": 6}
    )

Data preprocessing
------------------

Simplify the borders for all districts and assign colours so that no two neighbouring districts get the same colour.

.. code:: python

    # 1st step: simplify the borders
    # 2nd step: assign a color using graph coloring
    bayern = bayern.simplify(5e3).coloring()


Data visualisation
------------------

.. code:: python

    import altair as alt

    bayern_chart = alt.Chart(bayern)

    alt.layer(
        bayern_chart.mark_geoshape()
        .encode(alt.Color("coloring:N", legend=None), alt.Tooltip("name:N"))
        .properties(width=500, height=600),
        bayern_chart.mark_text(font="Ubuntu", fontSize=12)
        .encode(
            alt.Latitude("latitude:Q"), alt.Longitude("longitude:Q"),
            alt.Text("license_plate_code:N"), alt.Tooltip("name:N"),
        )
        # do not display empty data
        .transform_filter("datum.license_plate_code != null")
    )

Coats of arms
-------------

.. raw:: html

    <div id="bayern_wappen"></div>

    <script type="text/javascript">
      var spec = "../_static/gallery/bayern_wappen.json";
      vegaEmbed('#bayern_wappen', spec)
      .then(result => console.log(result))
      .catch(console.warn);
    </script>


The first map shows one main issue: only `Landkreis` display a license plate code, not cities outside a `Kreis` (`Kreisfreie Stadt`).

Since the data returned by OpenStreetMap contains a Wikidata identifier, we use it to fill the missing information.  Since the whole process involves many small downloads which can be run in parallel, we use the async framework for that.

Wikidata returns comprehensive information in JSON format, with popular fields encoded with identifiers. We focus here on:

- ``P394``: licence plate code;
- ``P94``: coat of arms (just because it's beautiful).

The following code gets all the necessary complementary information:

.. code:: python

    import aiohttp
    import bs4  # beautifulsoup4

    async def fetch(wikidata, client):
        result = dict()

        r = await client.get(
            f"https://www.wikidata.org/wiki/Special:EntityData/{wikidata}.json"
        )
        json = r.json()

        # The licence plate code
        p395 = [
            elt["mainsnak"]["datavalue"]["value"]
            for elt in json["entities"][wikidata]["claims"]["P395"]
        ]
        # Some districts have several official licence plate codes
        # Then the second looks more natural if we have to pick one
        result["P395"] = p395[0] if len(p395) == 1 else p395[1]

        # The name of the SVG file for the coat of arms
        p94 = next(
            elt["mainsnak"]["datavalue"]["value"]
            for elt in json["entities"][wikidata]["claims"]["P94"]
        )

        # The full path to the SVG file is to be found on that page
        r = await client.get(f"https://commons.wikimedia.org/wiki/File:{p94}")
        page = bs4.BeautifulSoup(await r.text())
        svg_link = page.find("a", href=re.compile("https://.*\.svg$"))
        if svg_link is not None:
            result["P94"] = svg_link.attrs["href"]

        return result


    async def wikidata():
        async with httpx.AsyncClient() as client:
            futures = list(
                fetch(elt.wikidata, client) for _, elt in bayern.data.iterrows()
            )
            return list(result for result in await asyncio.gather(*futures))


    records = await wikidata()  # only valid in notebooks, otherwise asyncio.run(main())

    bayern_complete = bayern.data.merge(
        pd.DataFrame.from_records(records, index=bayern.data.id_),
        left_on="id_",
        right_index=True,
    )

Then we can build the full map:

.. code:: python

    bayern_chart = alt.Chart(bayern_complete)
    selector = alt.selection_single(on="mouseover", nearest=True, empty="none")

    alt.layer(
        # Same background map
        bayern_chart.mark_geoshape()
        .encode(alt.Color("coloring:N", legend=None), alt.Tooltip("name:N"))
        .properties(width=500, height=600),
        # The text is now taken from P395 when not available
        bayern_chart.mark_text(font="Ubuntu", fontSize=12)
        .encode(
            alt.Text("display:N"), alt.Tooltip("name:N"),
            alt.Latitude("latitude:Q"), alt.Longitude("longitude:Q"),
        )
        .transform_calculate(
            # The switch happens here
            display=(
                "if(isValid(datum.license_plate_code), "
                "datum.license_plate_code, datum.P395)"
            )
        )
        .add_selection(selector),
        # We place a map on the top right corner, according to the selected text
        bayern_chart.mark_image(width=100, height=150, align="right", baseline="line-top")
        .encode(alt.Url("P94:N"))
        .transform_filter(selector),
    )
