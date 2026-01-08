# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys

# Point to the 'src' directory relative to this conf.py file
sys.path.insert(0, os.path.abspath("../../src"))

project = "PyGuLP"
copyright = (
    "2026, Kshitij Vaidya, Ishan Pandit, Roomani Srivastava, "
    "AIDE Lab - Prof. Kshitij Jadhav"
)
author = (
    "Kshitij Vaidya, Ishan Pandit, Roomani Srivastava, AIDE Lab - Prof. Kshitij Jadhav"
)
release = "0.0.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode", "sphinx.ext.napoleon"]

templates_path = ["_templates"]
# exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
