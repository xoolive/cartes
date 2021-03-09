import warnings

import importlib_metadata
from tqdm import TqdmExperimentalWarning

# Monkey-patches GeoAxesSubplot for .set_extent()
from .utils import geoaxes  # noqa: F401

__version__ = importlib_metadata.version("cartes")


# Silence this warning about autonotebook mode for tqdm
warnings.simplefilter("ignore", TqdmExperimentalWarning)
