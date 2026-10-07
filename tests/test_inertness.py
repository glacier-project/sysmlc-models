from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

from sysmlc_models.catalog import iter_models, model_path
from sysmlc_models.validation import validate_rosetta_inertness

if TYPE_CHECKING:
    from pathlib import Path

SHOWCASE_MODELS = tuple(
    str(directory.relative_to(model_path("showcase")))
    for directory in iter_models("showcase")
)


@pytest.mark.integration
@pytest.mark.parametrize("name", SHOWCASE_MODELS)
def test_showcase_has_no_lf_trigger_collision(
    name: str, tmp_path: Path
) -> None:
    if os.environ.get("SYSMLC_VALIDATION_BACKEND") != "rosetta":
        pytest.skip("LF transition-trigger policy")
    validate_rosetta_inertness(f"showcase/{name}", tmp_path)
