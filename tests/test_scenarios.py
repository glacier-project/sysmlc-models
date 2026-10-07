from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

from sysmlc_models.scenarios import SCENARIOS
from sysmlc_models.validation import (
    BACKENDS,
    Entry,
    Milestone,
    Result,
    Scenario,
    assert_result,
    validate_scenario,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_scenario_catalog_has_unique_names_and_valid_times() -> None:
    assert len({s.name for s in SCENARIOS}) == len(SCENARIOS)
    for scenario in SCENARIOS:
        assert (
            scenario.entries
            or scenario.states
            or scenario.milestones
            or scenario.failure
        )
        assert scenario.horizon_ms > 0
        assert set(scenario.backends) <= set(BACKENDS)
        assert scenario.backends
        times = (
            *scenario.ticks_ms,
            *(event.time_ms for event in scenario.inputs),
            *(entry.time_ms for entry in scenario.entries),
            *(m.latest_ms for m in scenario.milestones),
            *(m.earliest_ms for m in scenario.milestones),
        )
        assert all(0 <= time <= scenario.horizon_ms for time in times)


@pytest.mark.parametrize(
    "entries",
    [
        (),
        (Entry(0, "idle"),),
        (Entry(0, "idle"), Entry(4999, "running")),
        (Entry(0, "idle"), Entry(5000, "running"), Entry(5000, "running")),
        (Entry(0, "idle"), Entry(5000, "running"), Entry(6000, "fail")),
    ],
)
def test_contract_rejects_missing_mistimed_or_extra_entries(
    entries: tuple[Entry, ...],
) -> None:
    scenario = Scenario(
        "deadline",
        "model",
        "Machine",
        6000,
        (Entry(0, "idle"), Entry(5000, "running")),
    )
    with pytest.raises(AssertionError, match="expected entries"):
        assert_result(scenario, Result(entries))


def test_contract_accepts_concurrent_order_but_checks_values() -> None:
    scenario = Scenario(
        "parallel",
        "model",
        "Machine",
        1000,
        (Entry(0, "left"), Entry(0, "right")),
        attributes=(("count", 3),),
        concurrent_entries=True,
    )
    entries = (Entry(0, "right"), Entry(0, "left"))
    assert_result(scenario, Result(entries, (("count", 3),)))
    with pytest.raises(AssertionError, match="missing attribute"):
        assert_result(scenario, Result(entries))
    with pytest.raises(AssertionError, match="count=2"):
        assert_result(scenario, Result(entries, (("count", 2),)))


def test_contract_rejects_reordered_sequential_entries() -> None:
    scenario = Scenario(
        "sequential",
        "model",
        "Machine",
        1000,
        (Entry(0, "idle"), Entry(0, "running")),
    )
    with pytest.raises(AssertionError, match="expected entries"):
        assert_result(scenario, Result(tuple(reversed(scenario.entries))))


def test_state_sequence_checks_order_and_multiplicity() -> None:
    scenario = Scenario(
        "loop",
        "model",
        "Machine",
        4000,
        (),
        states=("idle", "running", "running", "done"),
    )
    entries = tuple(
        Entry(i * 1000, state) for i, state in enumerate(scenario.states)
    )
    assert_result(scenario, Result(entries))
    for wrong in (
        entries[:-1],
        entries[:2] + entries[3:],
        tuple(reversed(entries)),
    ):
        with pytest.raises(AssertionError, match="expected states"):
            assert_result(scenario, Result(wrong))


def test_negative_scenario_requires_its_runtime_diagnostic() -> None:
    scenario = Scenario(
        "bad-setpoint",
        "model",
        "Machine",
        1000,
        (),
        backends=("rosetta",),
        failure="setpointPositive",
    )
    assert_result(
        scenario, Result((), failure="constraint setpointPositive violated")
    )
    for failure in (
        None,
        "ModuleNotFoundError",
        "constraint tempBand violated",
    ):
        with pytest.raises(AssertionError, match="expected failure"):
            assert_result(scenario, Result((), failure=failure))


def test_positive_scenario_rejects_a_runtime_failure() -> None:
    scenario = Scenario("ok", "model", "Machine", 1000, (Entry(0, "done"),))
    with pytest.raises(AssertionError, match="unexpected runtime failure"):
        assert_result(scenario, Result(scenario.entries, failure="crashed"))


@pytest.mark.parametrize("entries", [(), (Entry(15001, "monitor::done"),)])
def test_contract_requires_completion_before_timeout(
    entries: tuple[Entry, ...],
) -> None:
    scenario = Scenario(
        "monitor",
        "model",
        "System",
        16000,
        (),
        kind="part",
        milestones=(Milestone("monitor::done", 0, 15000),),
    )
    with pytest.raises(AssertionError, match="missing milestone"):
        assert_result(scenario, Result(entries))


@pytest.mark.integration
@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.name)
def test_model_scenario(scenario: Scenario, tmp_path: Path) -> None:
    backend = os.environ.get("SYSMLC_VALIDATION_BACKEND")
    if backend not in BACKENDS:
        pytest.fail("set SYSMLC_VALIDATION_BACKEND to select the target")
    if backend not in scenario.backends:
        pytest.skip(f"{scenario.name} is not supported by {backend}")
    validate_scenario(scenario, backend, tmp_path)
