import importlib.metadata
import warnings

from tqdm import TqdmExperimentalWarning

# Monkey-patches GeoAxesSubplot for .set_extent()
# Monkey-patches GeoDataFrame for .extent()
from .utils import geoaxes  # noqa: F401

__version__ = importlib.metadata.version("cartes")


# Silence this warning about autonotebook mode for tqdm
warnings.simplefilter("ignore", TqdmExperimentalWarning)
