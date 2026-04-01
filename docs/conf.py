# Configuration file for the Sphinx documentation builder.

import datetime

# -- Project information -----------------------------------------------------

project = "pjkm"
author = "pr1m8"
copyright = f"{datetime.datetime.now().year}, {author}"
release = "0.1.0"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "autoapi.extension",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinxcontrib.mermaid",
    "myst_parser",
]

# -- AutoAPI settings --------------------------------------------------------

autoapi_type = "python"
autoapi_dirs = ["../src/pjkm"]
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
    "imported-members",
]
autoapi_keep_files = True

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# -- Napoleon settings -------------------------------------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True

# -- Autodoc settings --------------------------------------------------------

autodoc_member_order = "bysource"
autodoc_typehints = "description"

# -- Intersphinx settings ----------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3.13", None),
}

# -- MyST settings -----------------------------------------------------------

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "tasklist",
]

# -- HTML output -------------------------------------------------------------

html_theme = "furo"
html_title = "pjkm"
html_theme_options = {
    "source_repository": "https://github.com/pr1m8/pjkm",
    "source_branch": "main",
    "source_directory": "docs/",
}
html_static_path = ["_static"]
