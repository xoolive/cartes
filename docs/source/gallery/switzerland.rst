Swiss cantons
=============

A simple Swiss maps, to be further improved with arms when ``.mark_image()`` is
compatible with latitude and longitude channels in Altair.

.. jupyter-execute::

    import altair as alt

    from cartes.crs import GaussKrueger
    from cartes.atlas import germany  # Switzerland and Australia are with this Germany data

    sans_serif = "Fira Sans, Lato, sans-serif"
    base = alt.Chart(germany.dach.topo_feature)

    (
        alt.layer(
            base.mark_geoshape(stroke="white", strokeWidth=1.5, opacity=0.9)
            .encode(
                alt.Color("properties.NAME_1:N", title="Canton | Kanton"),
                alt.Tooltip("properties.NAME_1:N"),
            )
            .transform_filter("datum.properties.TYPE_1 != 'Water body'"),
            base.mark_geoshape(
                stroke="white", strokeWidth=1.5, color="steelblue", opacity=0.5
            )
            .transform_filter("datum.properties.TYPE_1 == 'Water body'")
        )
        .project(**GaussKrueger())  # CH1903p projection is not compatible with Altair
        .transform_filter("datum.properties.ISO == 'CHE'")
        .configure_view(stroke=None)
        .configure_text(font=sans_serif, size=15)
        .configure_legend(
            orient="bottom",
            columns=6,
            labelFont=sans_serif,
            labelFontSize=12,
            titleFont=sans_serif,
            titleFontSize=14,
        )
        .properties(width=600, height=500)
    )
