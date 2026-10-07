from __future__ import annotations

import os

import pytest

from sysmlc_models.sm_examples import SM_EXAMPLES, SmExample
from sysmlc_models.validation import validate_quake_initialization


@pytest.mark.integration
@pytest.mark.parametrize("example", SM_EXAMPLES, ids=lambda e: e.dir_name)
def test_quake_initialization(example: SmExample) -> None:
    if os.environ.get("SYSMLC_VALIDATION_BACKEND") != "quake":
        pytest.skip("the initialization sweep uses Quake's interpreter")
    validate_quake_initialization(f"sm-examples/{example.dir_name}")
