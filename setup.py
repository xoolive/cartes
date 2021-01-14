import io
import os
import re

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))
try:
    # Get the long description from the README file
    with open(os.path.join(here, "readme.md"), encoding="utf-8") as f:
        long_description = f.read()
except FileNotFoundError:
    # This exception is a problem when launching tox
    # Could not find a better workaround
    # Forcing the inclusion of the readme in the archive seems overkill
    long_description = ""


def read(path, encoding="utf-8"):
    path = os.path.join(os.path.dirname(__file__), path)
    with io.open(path, encoding=encoding) as fp:
        return fp.read()


def version(path):
    """Obtain the package version from a python file e.g. pkg/__init__.py
    See <https://packaging.python.org/en/latest/single_source_version.html>.
    """
    version_file = read(path)
    version_match = re.search(
        r"""^__version__ = ['"]([^'"]*)['"]""", version_file, re.M
    )
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name="cartes",
    version=version("cartes/__init__.py"),
    author="Xavier Olive",
    author_email="git@xoolive.org",
    url="https://github.com/xoolive/cartes/",
    license="MIT",
    description="A generic toolbox for building maps in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    package_data={
        "cartes": [
            "conftest.py",
            "mypy.ini",
            "py.typed",
            "pyproject.toml",
            "readme.md",
            "setup.cfg",
        ]
    },
    python_requires=">=3.6",
    install_requires=[
        "matplotlib",
        "scipy",  # missing dependency for cartopy
        "pandas",
        "pyproj>=3.0",
        "Cartopy",
        "Shapely",
        "requests",
        "appdirs",  # proper configuration directories
        "tqdm",
        "geopandas",
    ],
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 4 - Beta",
        # Indicate who your project is intended for
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        # Indicate relevant topics
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Software Development :: Libraries",
        # Pick your license as you wish (should match "license" above)
        "License :: OSI Approved :: MIT License",
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Typing :: Typed",
    ],
)
