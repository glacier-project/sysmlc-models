"""Filesystem access to the bundled SysML model corpora.

The corpora ship as package data under ``sysmlc_models/data/``.  The
accessors here resolve a corpus, a model directory, or a single file to a
real filesystem path, which is what ``syside`` and ``load_model`` require:
they read ``.sysml`` sources from a directory on disk, so the data is always
installed unpacked (editable in development, unzipped in a wheel install).
"""

from __future__ import annotations

from pathlib import Path

_DATA_ROOT = Path(__file__).resolve().parent / "data"


def model_path(name: str) -> Path:
    """Return the directory of a bundled corpus or model.

    Args:
        name: A path relative to the corpora root: either a corpus
            (``"sm-examples"``) or a model directory within one
            (``"sm-examples/sm01-helloworld"``).

    Returns:
        The absolute path to the directory.

    Raises:
        FileNotFoundError: If no such directory is bundled.
    """
    path = _DATA_ROOT / name
    if not path.is_dir():
        raise FileNotFoundError(f"no bundled model directory {name!r}")
    return path


def model_file(name: str) -> Path:
    """Return a single file bundled within a corpus.

    Args:
        name: A path relative to the corpora root pointing at a file,
            e.g. ``"showcase/furuta-pendulum/furuta_physics.py"``.

    Returns:
        The absolute path to the file.

    Raises:
        FileNotFoundError: If no such file is bundled.
    """
    path = _DATA_ROOT / name
    if not path.is_file():
        raise FileNotFoundError(f"no bundled model file {name!r}")
    return path


def iter_models(corpus: str) -> list[Path]:
    """Return the model directories within a corpus, sorted by name.

    Args:
        corpus: A corpus name, e.g. ``"showcase"`` or ``"sm-examples"``.

    Returns:
        The absolute paths of directories that directly contain SysML source
        files. Nested variant groups are traversed recursively.

    Raises:
        FileNotFoundError: If the corpus is not bundled.
    """
    root = model_path(corpus)
    return sorted({source.parent for source in root.rglob("*.sysml")})
