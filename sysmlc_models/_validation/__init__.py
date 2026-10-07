"""Optional compiler-dependent execution adapters for the scenario catalog."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from sysmlc.semantics.statemachine.driver import StateMachineDriver
from sysmlc.semantics.statemachine.facts import CompletionTarget, StateKind
from sysmlc.sysml.loading import load_model
from sysmlc.values import configure_model

from sysmlc_models.catalog import model_path

if TYPE_CHECKING:
    from pathlib import Path

    import syside
    from sysmlc.semantics.statemachine.facts import (
        AttributeBinding,
        StateFact,
        TransitionFact,
    )

    from sysmlc_models.validation import Scenario


class _LeafPaths:
    def __init__(self) -> None:
        self.paths: set[str] = set()

    def bind_attribute(self, binding: AttributeBinding) -> None:
        pass

    def add_state(self, state: StateFact) -> None:
        if state.kind is StateKind.LEAF:
            self.paths.add(state.name)

    def add_transition(self, transition: TransitionFact) -> None:
        if isinstance(transition.target, CompletionTarget):
            scope = transition.target.scope
            self.paths.add(f"{scope}::done" if scope else "done")

    def result(self) -> object:
        return self.paths


def load(scenario: Scenario) -> tuple[syside.Model, set[str]]:
    """Load configured sources and derive observed paths from neutral facts.

    Args:
        scenario: The model execution contract to verify.

    Returns:
        The configured model and its leaf/completion paths.

    Raises:
        ValueError: If sources, configuration or state semantics are invalid.
    """
    model = load_model(model_path(scenario.model))
    if scenario.kind == "part":
        return model, set()
    configure_model(model, scenario.element, dict(scenario.overrides))
    observer = _LeafPaths()
    StateMachineDriver(model).run(scenario.element, observer)
    return model, observer.paths


def command(args: list[str], work_dir: Path, timeout: int = 120) -> str:
    """Run a build/runtime command and retain its diagnostics on failure.

    Args:
        args: Executable and arguments to run without a shell.
        work_dir: Directory containing the generated project.
        timeout: Wall-clock safety limit in seconds.

    Returns:
        The command's standard output.

    Raises:
        AssertionError: If the command exits with a failure status.
        OSError: If the executable cannot be launched.
        subprocess.TimeoutExpired: If the command exceeds the safety limit.
    """
    result = subprocess.run(
        args, cwd=work_dir, capture_output=True, text=True, timeout=timeout
    )
    assert result.returncode == 0, (
        f"{args[0]} exited {result.returncode}:\n"
        f"{result.stdout}\n{result.stderr}"
    )
    return result.stdout
