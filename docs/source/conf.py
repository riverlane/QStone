# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys
from pathlib import Path

sys.path.insert(0, str(Path('..', '..').resolve()))

import importlib.metadata

__version__ = importlib.metadata.version("qstone")


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'QStone'
copyright = '2025, Riverlane'
author = 'Riverlane'
release = __version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [ 'nbsphinx', 'sphinx_copybutton', 'sphinx.ext.autodoc', 'sphinx.ext.viewcode',
    'sphinx.ext.napoleon', 'sphinx_mdinclude']
autodoc_mock_imports = ['django']

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
