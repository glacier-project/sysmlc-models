"""The root directory of the showcase corpus.

Consumers address individual showcase models by joining folder names onto
:data:`SHOWCASE_DIR`, mirroring how :mod:`sysmlc_models.sm_examples`
exposes the sm-examples corpus root.
"""

from __future__ import annotations

from sysmlc_models.catalog import model_path

SHOWCASE_DIR = model_path("showcase")
