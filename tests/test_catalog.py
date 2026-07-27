from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from sysmlc_models.catalog import (
    iter_models,
    model_dirs_under,
    model_file,
    model_path,
)
from sysmlc_models.sm_examples import SM_EXAMPLES, SM_EXAMPLES_BY_DIR


def test_model_path_returns_a_bundled_directory() -> None:
    path = model_path("sm-examples/sm01-helloworld")
    assert path.is_dir()
    assert path.name == "sm01-helloworld"


def test_model_path_rejects_a_missing_directory() -> None:
    with pytest.raises(FileNotFoundError):
        model_path("sm-examples/does-not-exist")


def test_model_file_returns_a_bundled_file() -> None:
    path = model_file("showcase/furuta-pendulum/furuta_physics.py")
    assert path.is_file()


def test_model_file_rejects_a_directory() -> None:
    with pytest.raises(FileNotFoundError):
        model_file("sm-examples/sm01-helloworld")


def test_iter_models_lists_corpus_directories() -> None:
    dirs = iter_models("sm-examples")
    assert dirs
    assert all(path.is_dir() for path in dirs)
    assert "sm01-helloworld" in {path.name for path in dirs}


def test_iter_models_discovers_nested_showcase_variants() -> None:
    root = model_path("showcase")
    relative = {
        path.relative_to(root).as_posix() for path in iter_models("showcase")
    }
    assert "furuta-pendulum/deterministic" in relative
    assert "furuta-pendulum/nondeterministic" in relative
    assert "furuta-pendulum" not in relative


def test_curated_examples_resolve_to_directories() -> None:
    assert SM_EXAMPLES
    for example in SM_EXAMPLES:
        assert example.model_dir.is_dir()
    assert "sm11-send-effect" in SM_EXAMPLES_BY_DIR


def test_model_dirs_under_discovers_nested_dirs(tmp_path: Path) -> None:
    flat = tmp_path / "flat"
    flat.mkdir()
    (flat / "m.sysml").touch()
    nested = tmp_path / "group" / "variant"
    nested.mkdir(parents=True)
    (nested / "m.sysml").touch()
    assert model_dirs_under(tmp_path) == [flat, nested]
