"""Shared, observable execution contracts for the bundled model scenarios."""

from __future__ import annotations

import argparse
import importlib
import os
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

if TYPE_CHECKING:
    from collections.abc import Callable

type Scalar = bool | int | float | str

BACKENDS = ("quake", "rosetta", "statix")


@dataclass(frozen=True, order=True)
class Entry:
    """Entry into a leaf or completion state at a logical millisecond."""

    time_ms: int
    state: str


@dataclass(frozen=True)
class Input:
    """One payload-free input occurrence at a logical millisecond."""

    time_ms: int
    signal: str


@dataclass(frozen=True)
class Milestone:
    """A required state entry within an inclusive logical-time interval."""

    state: str
    earliest_ms: int
    latest_ms: int


@dataclass(frozen=True)
class Scenario:
    """A model execution with independently specified expected behavior.

    Attributes:
        ticks_ms: Absolute logical clock updates for the manually clocked
            targets. Include timer deadlines and observations before them.
        entries: Exact expected leaf/completion entries in execution order.
        concurrent_entries: Allow different region ordering at the same
            time. Entry times and multiplicity must still match exactly.
        attributes: Expected scalar values at the end of execution.
        overrides: Scalar model configuration applied before compilation.
        backends: Targets supporting this scenario's constructs.
        milestones: Required states for executions whose physical dynamics
            allow a time interval rather than one exact trace.
        forbidden_states: States that must never be entered during the run.
        support: Optional Python support file within the bundled catalog.
    """

    name: str
    model: str
    element: str
    horizon_ms: int
    entries: tuple[Entry, ...]
    ticks_ms: tuple[int, ...] = ()
    inputs: tuple[Input, ...] = ()
    attributes: tuple[tuple[str, Scalar], ...] = ()
    overrides: tuple[tuple[str, Scalar], ...] = ()
    backends: tuple[str, ...] = BACKENDS
    kind: Literal["state", "part"] = "state"
    milestones: tuple[Milestone, ...] = ()
    forbidden_states: tuple[str, ...] = ()
    support: str | None = None
    concurrent_entries: bool = False


@dataclass(frozen=True)
class Result:
    """Observed state entries and final scalar values from an actual run."""

    entries: tuple[Entry, ...]
    attributes: tuple[tuple[str, Scalar], ...] = ()


def assert_result(scenario: Scenario, result: Result) -> None:
    """Check the complete trace and requested final values against a contract.

    Args:
        scenario: The model execution contract to verify.
        result: Observations produced by the target runtime.

    Raises:
        AssertionError: If an entry is missing, unexpected or mistimed, or
            a requested attribute does not have its expected final value.
    """
    assert scenario.entries or scenario.milestones, (
        f"{scenario.name}: no observable success criterion"
    )
    if scenario.entries:
        matches = (
            Counter(result.entries) == Counter(scenario.entries)
            if scenario.concurrent_entries
            else result.entries == scenario.entries
        )
        assert matches, (
            f"{scenario.name}: expected entries {scenario.entries!r}, "
            f"observed {result.entries!r}"
        )
    for milestone in scenario.milestones:
        assert any(
            entry.state == milestone.state
            and milestone.earliest_ms <= entry.time_ms <= milestone.latest_ms
            for entry in result.entries
        ), f"{scenario.name}: missing milestone {milestone!r}"
    assert not {entry.state for entry in result.entries} & set(
        scenario.forbidden_states
    ), f"{scenario.name}: entered a failure state"
    actual = dict(result.attributes)
    for name, expected in scenario.attributes:
        assert name in actual, f"{scenario.name}: missing attribute {name!r}"
        assert actual[name] == expected, (
            f"{scenario.name}: {name}={actual[name]!r}, expected {expected!r}"
        )


def validate_scenario(
    scenario: Scenario, backend: str, work_dir: Path
) -> Result:
    """Compile, execute and verify one scenario on an installed target.

    Only the selected adapter is imported. The model catalog and execution
    contracts remain usable without any compiler or backend installation.

    Args:
        scenario: The model execution contract to verify.
        backend: One of ``quake``, ``rosetta`` or ``statix``.
        work_dir: Fresh directory for generated sources and build artifacts.

    Returns:
        The verified runtime observations.

    Raises:
        ValueError: If the target is unknown or unsupported by the scenario.
        AssertionError: If compilation, execution or contract checks fail.
        ImportError: If the selected compiler/backend is not installed.
        OSError: If a required native tool cannot be executed.
        subprocess.TimeoutExpired: If compilation or execution times out.
    """
    if backend not in BACKENDS or backend not in scenario.backends:
        raise ValueError(f"{scenario.name}: unsupported backend {backend!r}")
    if scenario.kind == "part" and (
        scenario.inputs or scenario.overrides or scenario.attributes
    ):
        raise ValueError("part scenarios use their model's built-in testbench")
    if scenario.kind == "state" and scenario.support is not None:
        raise ValueError("external support is configured for part scenarios")
    adapter = importlib.import_module(f"sysmlc_models._validation.{backend}")
    run = cast("Callable[[Scenario, Path], Result]", adapter.run)
    work_dir.mkdir(parents=True, exist_ok=True)
    result = run(scenario, work_dir)
    assert_result(scenario, result)
    return result


def validate_quake_initialization(model_name: str) -> None:
    """Verify initial quiescence for every state definition in one model.

    This complements the behavioral contracts with the corpus-wide check
    that generated guards, actions and invariants can evaluate on startup.

    Args:
        model_name: Bundled catalog path of one model directory.

    Raises:
        ValueError: If the sources or state semantics are invalid.
        ImportError: If Quake and its compiler dependencies are not installed.
        sismic.exceptions.SismicError: If generated expressions cannot run.
        AssertionError: If initialization exhausts the macrostep safety limit.
    """
    from sysmlc_models._validation.quake import check_initialization

    check_initialization(model_name)


def main() -> None:
    """Run the shared catalog with a command-line or environment target."""
    from sysmlc_models.scenarios import SCENARIOS

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backend",
        choices=BACKENDS,
        default=os.environ.get("SYSMLC_VALIDATION_BACKEND"),
    )
    parser.add_argument("--scenario", choices=[s.name for s in SCENARIOS])
    parser.add_argument("--work-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.backend not in BACKENDS:
        parser.error("set --backend or SYSMLC_VALIDATION_BACKEND")
    selected = [
        s
        for s in SCENARIOS
        if args.backend in s.backends
        and (args.scenario is None or args.scenario == s.name)
    ]
    if not selected:
        parser.error("the requested scenario does not support this backend")
    for scenario in selected:
        validate_scenario(scenario, args.backend, args.work_dir / scenario.name)
        print(f"PASS {args.backend}: {scenario.name}")


if __name__ == "__main__":
    main()
