"""Shared, observable execution contracts for the bundled model scenarios."""

from __future__ import annotations

import argparse
import importlib
import os
from collections import Counter
from dataclasses import dataclass
from itertools import permutations
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
    """One input occurrence with optional scalar payload fields."""

    time_ms: int
    signal: str
    fields: tuple[tuple[str, Scalar], ...] = ()


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
        concurrent_entries: Allow interleaving between declared parallel
            regions at the same time, preserving all other entry ordering.
        parallel_regions: Groups of state paths naming sibling parallel
            regions. Entries in different regions of a group can interleave;
            entries inside one region or outside the group remain ordered.
        attributes: Expected scalar values at the end of execution.
        overrides: Scalar model configuration applied before compilation.
        backends: Targets supporting this scenario's constructs.
        milestones: Required states for executions whose physical dynamics
            allow a time interval rather than one exact trace.
        forbidden_states: States that must never be entered during the run.
        support: Optional Python support file within the bundled catalog.
        states: Exact leaf/completion sequence when only ordering is asserted.
        alternative_states: Additional permitted complete state sequences.
        failure: Required runtime diagnostic for a negative model scenario.
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
    states: tuple[str, ...] = ()
    failure: str | None = None
    alternative_states: tuple[tuple[str, ...], ...] = ()
    parallel_regions: tuple[tuple[str, ...], ...] = ()


@dataclass(frozen=True)
class Result:
    """Observed state entries and final scalar values from an actual run."""

    entries: tuple[Entry, ...]
    attributes: tuple[tuple[str, Scalar], ...] = ()
    failure: str | None = None


def assert_result(scenario: Scenario, result: Result) -> None:
    """Check the complete trace and requested final values against a contract.

    Args:
        scenario: The model execution contract to verify.
        result: Observations produced by the target runtime.

    Raises:
        AssertionError: If parallel regions are missing or ambiguous, an
            alternative sequence is empty, an entry is missing, unexpected,
            mistimed or out of order, or a requested attribute does not have
            its expected final value.
    """
    assert (
        scenario.entries
        or scenario.states
        or scenario.alternative_states
        or scenario.milestones
        or scenario.failure
    ), f"{scenario.name}: no observable success criterion"
    assert all(scenario.alternative_states), (
        f"{scenario.name}: alternative state sequences must not be empty"
    )
    assert scenario.concurrent_entries == bool(scenario.parallel_regions), (
        f"{scenario.name}: concurrent_entries requires explicit parallel_regions"
    )
    for regions in scenario.parallel_regions:
        assert (
            len(regions) >= 2
            and all(regions)
            and len(set(regions)) == len(regions)
            and all(
                not first.startswith(f"{second}::")
                for first, second in permutations(regions, 2)
            )
        ), f"{scenario.name}: parallel regions must be distinct sibling paths"
    if scenario.failure is None:
        assert result.failure is None, (
            f"{scenario.name}: unexpected runtime failure {result.failure!r}"
        )
    else:
        assert (
            result.failure is not None and scenario.failure in result.failure
        ), (
            f"{scenario.name}: expected failure {scenario.failure!r}, "
            f"observed {result.failure!r}"
        )
    if scenario.states or scenario.alternative_states:
        expected_sequences = (
            (scenario.states,) if scenario.states else ()
        ) + scenario.alternative_states
        actual_states = tuple(entry.state for entry in result.entries)
        assert actual_states in expected_sequences, (
            f"{scenario.name}: expected states matching one complete sequence "
            f"in {expected_sequences!r}, "
            f"observed {actual_states!r}"
        )
    if scenario.entries:
        matches = (
            _matches_concurrent_entries(
                scenario.entries, result.entries, scenario.parallel_regions
            )
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


def _matches_concurrent_entries(
    expected: tuple[Entry, ...],
    actual: tuple[Entry, ...],
    parallel_regions: tuple[tuple[str, ...], ...],
) -> bool:
    """Match a trace allowing only independent same-time entries to move.

    Args:
        expected: One permitted complete trace in execution order.
        actual: Observed entries in execution order.
        parallel_regions: Groups of paths naming sibling parallel regions.

    Returns:
        Whether the observed trace preserves every required ordering.
    """
    if Counter(actual) != Counter(expected):
        return False
    pending = list(expected)
    for entry in actual:
        position = pending.index(entry)
        if any(
            not _can_interleave(entry, previous, parallel_regions)
            for previous in pending[:position]
        ):
            return False
        pending.pop(position)
    return True


def _can_interleave(
    first: Entry,
    second: Entry,
    parallel_regions: tuple[tuple[str, ...], ...],
) -> bool:
    """Return whether two entries belong to independent regions at one time."""
    if first.time_ms != second.time_ms:
        return False
    for regions in parallel_regions:
        first_region = _region(first.state, regions)
        second_region = _region(second.state, regions)
        if (
            first_region is not None
            and second_region is not None
            and first_region != second_region
        ):
            return True
    return False


def _region(state: str, regions: tuple[str, ...]) -> str | None:
    """Return the declared region containing a state path, if any."""
    return next(
        (
            region
            for region in regions
            if state == region or state.startswith(f"{region}::")
        ),
        None,
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
    if backend == "statix" and any(event.fields for event in scenario.inputs):
        raise ValueError("Statix's host runner accepts payload-free inputs")
    if scenario.failure is not None and backend != "rosetta":
        raise ValueError("runtime failure scenarios require the LF adapter")
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


def validate_rosetta_inertness(model_name: str, work_dir: Path) -> None:
    """Check that a showcase run has no competing LF transition triggers.

    Args:
        model_name: Bundled catalog path of one showcase model directory.
        work_dir: Fresh directory for generated sources and build artifacts.

    Raises:
        ImportError: If Rosetta and its compiler dependencies are absent.
        AssertionError: If build, execution or collision checks fail.
        OSError: If a required compiler or executable cannot be launched.
        subprocess.TimeoutExpired: If compilation or execution times out.
    """
    from sysmlc_models._validation.inertness import check

    check(model_name, work_dir)


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
