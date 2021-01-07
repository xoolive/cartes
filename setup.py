import os

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

setup(
    name="cartes",
    version="1.0",
    author="Xavier Olive",
    author_email="git@xoolive.org",
    url="https://github.com/xoolive/cartes/",
    license="MIT",
    description="A generic toolbox for building maps in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    package_data={"cartes": ["py.typed"]},
    python_requires=">=3.6",
    install_requires=[
        "pyproj>=3.0",
        "pandas",
        "Cartopy",
        "Shapely",
        "requests",
        "appdirs",  # proper configuration directories
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
