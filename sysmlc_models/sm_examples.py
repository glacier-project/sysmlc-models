"""The curated catalogue of single-machine SysML state-machine examples.

Backend test suites parametrize over this list, so it lives in the model
package rather than in any one backend's tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sysmlc_models.catalog import model_path

if TYPE_CHECKING:
    from pathlib import Path

SM_EXAMPLES_DIR = model_path("sm-examples")


@dataclass(frozen=True)
class SmExample:
    """One entry in the SysML state-machine examples collection.

    Attributes:
        dir_name: Folder under the ``sm-examples`` corpus holding the
            example's ``.sysml`` sources.
    """

    dir_name: str

    @property
    def model_dir(self) -> Path:
        """Return the directory holding this example's sources."""
        return SM_EXAMPLES_DIR / self.dir_name


SM_EXAMPLES: list[SmExample] = [
    SmExample("sm01-helloworld"),
    SmExample("sm02-event-trigger"),
    SmExample("sm03-guard"),
    SmExample("sm04-assignment"),
    SmExample("sm05-chained-references"),
    SmExample("sm06-transition-effect"),
    SmExample("sm07-firing-order"),
    SmExample("sm08-nested-composite"),
    SmExample("sm09-parallel"),
    SmExample("sm10-done"),
    SmExample("sm11-send-effect"),
    SmExample("sm12-do-action"),
    SmExample("sm13-time-trigger"),
    SmExample("sm16-change-trigger"),
    SmExample("sm17-assert-constraints"),
    SmExample("sm18-enum-literals"),
]

SM_EXAMPLES_BY_DIR: dict[str, SmExample] = {e.dir_name: e for e in SM_EXAMPLES}
