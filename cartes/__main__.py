import logging

import click

from cartes import crs
from cartes.utils.features import countries


@click.command()
@click.argument("projection", type=str, default="Mercator")
@click.option(
    "--scale",
    type=str,
    default="50m",
    show_default=True,
    help="Resolution for country outlines",
)
@click.option("-v", "--verbose", count=True, help="Verbosity level")
def main(projection: str, scale: str, verbose: int):

    logger = logging.getLogger()
    if verbose == 1:
        logger.setLevel(logging.INFO)
    elif verbose > 1:
        logger.setLevel(logging.DEBUG)

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(
        subplot_kw=dict(projection=getattr(crs, projection)())
    )
    ax.add_feature(countries(scale=scale))

    fig.show()
    plt.pause(-1)


if __name__ == "__main__":
    main()
