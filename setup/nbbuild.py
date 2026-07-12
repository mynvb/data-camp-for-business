"""
Tiny helper to build valid Jupyter/Databricks .ipynb notebooks from a simple
list of (kind, text) cells. Guarantees valid nbformat 4 JSON.

    from nbbuild import md, code, write_notebook
    write_notebook("labs/Lab 0.ipynb", [
        md("# Title"),
        code("print('hi')"),
    ])
"""

import json


def md(text):
    return ("markdown", text)


def code(text):
    return ("code", text)


def _lines(text):
    # nbformat stores source as a list of lines, each keeping its trailing \n
    # except the last. Splitting this way round-trips cleanly.
    text = text.rstrip("\n")
    parts = text.split("\n")
    return [p + "\n" for p in parts[:-1]] + [parts[-1]] if parts else [""]


def write_notebook(path, cells, language="python"):
    nb_cells = []
    for kind, text in cells:
        if kind == "markdown":
            nb_cells.append({
                "cell_type": "markdown",
                "metadata": {},
                "source": _lines(text),
            })
        else:
            nb_cells.append({
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": _lines(text),
            })
    nb = {
        "cells": nb_cells,
        "metadata": {
            "application/vnd.databricks.v1+notebook": {
                "language": language,
                "notebookName": path.split("/")[-1].replace(".ipynb", ""),
            },
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": language},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    with open(path, "w") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    # basic validation
    with open(path) as f:
        json.load(f)
    return path
