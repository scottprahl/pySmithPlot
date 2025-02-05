# pylint: disable=invalid-name

"""
This file is intended to be the target of a pytest run.

It recursively finds all .ipynb files in the docs directory, ignoring
directories that start with a dot and any files matching patterns found in the
.testignore file.

The .testignore file should list patterns (one per line) for notebooks to skip,
for example:

    under_construction/*

Sample invocations of pytest with verbose output and duration reporting:

    pytest --verbose --durations=5 test_all_notebooks.py

If you install pytest-xdist, you can run tests in parallel with:

    pytest --verbose --durations=5 -n 4 test_all_notebooks.py

Original version is licensed under GPL 3.0 so this one is too.
The original can be located at:
    https://github.com/alchemyst/Dynamics-and-Control/test_all_notebooks.py
"""

from pathlib import Path

import pytest
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor


def load_ignore_patterns(ignore_file: Path) -> list:
    """
    Load ignore patterns from a file.

    Parameters:
        ignore_file: Path to the ignore file.

    Returns:
        A list of non-empty stripped patterns.
    """
    if ignore_file.exists():
        with ignore_file.open(encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return []


def collect_notebooks(search_path: Path, ignore_patterns: list) -> list:
    """
    Recursively collect all Jupyter notebooks in the search_path.

    Avoid files in hidden directories and do not match any ignore patterns.

    Parameters:
        search_path: Path in which to search for .ipynb files.
        ignore_patterns: List of patterns to ignore.

    Returns:
        A sorted list of Path objects pointing to the notebooks.
    """
    notebooks = []
    # Using rglob to recursively search for .ipynb files
    for notebook in search_path.rglob("*.ipynb"):
        # Skip if any parent directory is hidden (starts with '.')
        if any(part.startswith(".") for part in notebook.parts):
            continue
        # Skip if the notebook matches any of the ignore patterns
        if any(notebook.match(pattern) for pattern in ignore_patterns):
            continue
        notebooks.append(notebook)
    return sorted(notebooks)


# Define the search path for notebooks (assumes notebooks are under the docs directory)
SEARCH_PATH = Path("docs")
IGNORE_FILE = Path(".testignore")
IGNORE_PATTERNS = load_ignore_patterns(IGNORE_FILE)
NOTEBOOKS = collect_notebooks(SEARCH_PATH, IGNORE_PATTERNS)

# Generate ids for the notebooks based on their posix path for pytest reporting.
NOTEBOOK_IDS = [nb.as_posix() for nb in NOTEBOOKS]

# Uncomment the following line if you want to print out the notebooks collected for debugging.
# print("Found notebooks:", NOTEBOOKS)


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=NOTEBOOK_IDS)
def test_run_notebook(notebook: Path):
    """
    Test that a notebook runs without errors.

    This test reads a Jupyter notebook, executes it using the ExecutePreprocessor
    from nbconvert, and will raise an exception if any cell fails.

    Any errors during execution will be caught by pytest.
    """
    with notebook.open(encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    # Set a generous timeout to account for long-running notebooks.
    exec_preprocessor = ExecutePreprocessor(timeout=600, kernel_name="python3")
    # Execute the notebook, setting the working directory to the notebook's parent.
    exec_preprocessor.preprocess(nb, {"metadata": {"path": notebook.parent}})
