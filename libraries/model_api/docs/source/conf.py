# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys
from pathlib import Path

# Define the path to your module using Path
module_path = Path(__file__).resolve().parents[2] / "src"

# Insert the path to sys.path
sys.path.insert(0, str(module_path.resolve()))

project = "ModelAPI"
copyright = "2025, Intel"
author = "Intel"
release = "2025"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "breathe",
    "sphinx.ext.autodoc",
    "sphinx.ext.mathjax",
    "sphinx_design",
    "myst_parser",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "sphinx.ext.graphviz",
]

myst_enable_extensions = [
    "colon_fence",
    # other MyST extensions...
]

templates_path = ["_templates"]
exclude_patterns: list[str] = []

# Automatic exclusion of prompts from the copies
# https://sphinx-copybutton.readthedocs.io/en/latest/use.html#automatic-exclusion-of-prompts-from-the-copies
copybutton_exclude = ".linenos, .gp, .go"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]

breathe_projects = {"InferenceSDK": Path(__file__).parent.parent / "build_cpp" / "xml"}
breathe_default_project = "InferenceSDK"
breathe_default_members = ("members", "undoc-members", "private-members")

autodoc_docstring_signature = True
autodoc_member_order = "bysource"
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
}
autodoc_member_order = "groupwise"
autodoc_default_options = {
    "members": True,
    "methods": True,
    "special-members": "__call__",
    "exclude-members": "_abc_impl",
    "show-inheritance": True,
}

autoclass_content = "both"

autosummary_generate = True  # Turn on sphinx.ext.autosummary
