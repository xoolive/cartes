# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

import cartes

# import stanford_theme

# -- Project information -----------------------------------------------------

project = "Cartes"
copyright = "2021, Xavier Olive"
author = "Xavier Olive"

# The full version, including alpha/beta/rc tags
release = cartes.__version__


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ["jupyter_sphinx"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []  # type: ignore


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]


def setup(app):
    # <!-- Import Vega & Vega-Lite -->
    app.add_js_file("https://cdn.jsdelivr.net/npm/vega@5")
    app.add_js_file("https://cdn.jsdelivr.net/npm/vega-lite@5")
    app.add_js_file("https://cdn.jsdelivr.net/npm/vega-embed@6")

    # <!-- Necessary to include jupyter widgets -->
    app.add_js_file(
        "https://cdnjs.cloudflare.com/ajax/libs/require.js/2.3.4/require.min.js"
    )
    app.add_js_file(
        "https://unpkg.com/@jupyter-widgets/html-manager/dist/embed-amd.js"
    )

    # Specific stylesheet
    app.add_css_file(
        "https://fonts.googleapis.com/css?family=Fira Sans|Ubuntu"
        ":regular,bold&subset=Latin&display=swap"
    )
    app.add_css_file(
        "https://fonts.googleapis.com/css?family=Noto Sans JP"
        ":thin,regular,bold&display=swap"
    )
    app.add_css_file("main_stylesheet.css")
