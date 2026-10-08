from __future__ import annotations

import os
from dataclasses import replace
from itertools import permutations
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


@pytest.fixture
def parallel_scenario() -> Scenario:
    return next(s for s in SCENARIOS if s.name == "parallel-root")


def test_scenario_catalog_has_unique_names_and_valid_times() -> None:
    assert len({s.name for s in SCENARIOS}) == len(SCENARIOS)
    for scenario in SCENARIOS:
        assert (
            scenario.entries
            or scenario.states
            or scenario.alternative_states
            or scenario.milestones
            or scenario.failure
        )
        assert scenario.horizon_ms > 0
        assert set(scenario.backends) <= set(BACKENDS)
        assert scenario.backends
        assert all(scenario.alternative_states)
        assert scenario.concurrent_entries == bool(scenario.parallel_regions)
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
        parallel_regions=(("left", "right"),),
    )
    entries = (Entry(0, "right"), Entry(0, "left"))
    assert_result(scenario, Result(entries, (("count", 3),)))
    with pytest.raises(AssertionError, match="missing attribute"):
        assert_result(scenario, Result(entries))
    with pytest.raises(AssertionError, match="count=2"):
        assert_result(scenario, Result(entries, (("count", 2),)))


def test_parallel_root_rejects_reversed_region_order(
    parallel_scenario: Scenario,
) -> None:
    with pytest.raises(AssertionError, match="expected entries"):
        assert_result(
            parallel_scenario,
            Result(tuple(reversed(parallel_scenario.entries))),
        )


def test_parallel_root_accepts_exactly_the_valid_interleavings(
    parallel_scenario: Scenario,
) -> None:
    for entries in permutations(parallel_scenario.entries):
        lights_in_order = entries.index(
            Entry(0, "lights::off")
        ) < entries.index(Entry(0, "lights::on"))
        sound_in_order = entries.index(
            Entry(0, "sound::silent")
        ) < entries.index(Entry(0, "sound::beeping"))
        if lights_in_order and sound_in_order:
            assert_result(parallel_scenario, Result(entries))
        else:
            with pytest.raises(AssertionError, match="expected entries"):
                assert_result(parallel_scenario, Result(entries))


@pytest.mark.parametrize(
    ("name", "before", "after"),
    [
        ("parallel-nested", Entry(0, "idle"), Entry(0, "dual::lights::off")),
        (
            "parallel-join-two",
            Entry(200, "working::b::done"),
            Entry(200, "finished"),
        ),
        (
            "microwave-parallel-join",
            Entry(700, "cooking::done"),
            Entry(700, "idle"),
        ),
        (
            "batch-reactor-recipe",
            Entry(2200, "heating"),
            Entry(2200, "reacting::agitation::stirring"),
        ),
    ],
)
def test_concurrent_contract_preserves_sequential_boundaries(
    name: str, before: Entry, after: Entry
) -> None:
    scenario = next(s for s in SCENARIOS if s.name == name)
    entries = list(scenario.entries)
    first, second = entries.index(before), entries.index(after)
    entries[first], entries[second] = entries[second], entries[first]
    with pytest.raises(AssertionError, match="expected entries"):
        assert_result(scenario, Result(tuple(entries), scenario.attributes))


@pytest.mark.parametrize(
    "scenario",
    [s for s in SCENARIOS if s.concurrent_entries],
    ids=lambda s: s.name,
)
def test_concurrent_contract_accepts_its_declared_trace(
    scenario: Scenario,
) -> None:
    assert_result(scenario, Result(scenario.entries, scenario.attributes))


@pytest.mark.parametrize(
    "entries",
    [
        (Entry(0, "lights::off"),),
        (
            Entry(0, "lights::off"),
            Entry(0, "sound::silent"),
            Entry(1, "lights::on"),
            Entry(0, "sound::beeping"),
        ),
        (
            Entry(0, "lights::off"),
            Entry(0, "sound::silent"),
            Entry(0, "lights::on"),
            Entry(0, "sound::beeping"),
            Entry(0, "lights::on"),
        ),
    ],
)
def test_concurrent_contract_checks_times_and_multiplicity(
    parallel_scenario: Scenario, entries: tuple[Entry, ...]
) -> None:
    with pytest.raises(AssertionError, match="expected entries"):
        assert_result(parallel_scenario, Result(entries))


def test_concurrent_contract_preserves_chronological_order(
    parallel_scenario: Scenario,
) -> None:
    scenario = replace(
        parallel_scenario,
        entries=(Entry(0, "lights::off"), Entry(10, "sound::silent")),
    )
    with pytest.raises(AssertionError, match="expected entries"):
        assert_result(scenario, Result(tuple(reversed(scenario.entries))))


def test_concurrent_contract_preserves_order_of_repeated_entries(
    parallel_scenario: Scenario,
) -> None:
    lights = (
        Entry(0, "lights::off"),
        Entry(0, "lights::on"),
        Entry(0, "lights::off"),
        Entry(0, "lights::on"),
    )
    sound = Entry(0, "sound::silent")
    scenario = replace(parallel_scenario, entries=(*lights, sound))
    assert_result(scenario, Result((sound, *lights)))
    reordered = (lights[0], lights[2], lights[1], lights[3], sound)
    with pytest.raises(AssertionError, match="expected entries"):
        assert_result(scenario, Result(reordered))


def test_concurrent_contract_matches_complete_region_paths(
    parallel_scenario: Scenario,
) -> None:
    scenario = replace(
        parallel_scenario,
        entries=(
            Entry(0, "working::a::idle"),
            Entry(0, "working::alarm::idle"),
            Entry(0, "working::b::idle"),
        ),
        parallel_regions=(("working::a", "working::b"),),
    )
    first, alarm, second = scenario.entries
    with pytest.raises(AssertionError, match="expected entries"):
        assert_result(scenario, Result((first, second, alarm)))


def test_concurrent_contract_handles_nested_parallel_regions(
    parallel_scenario: Scenario,
) -> None:
    first = Entry(0, "outer::left::x::off")
    second = Entry(0, "outer::left::x::on")
    inner_peer = Entry(0, "outer::left::y::idle")
    outer_peer = Entry(0, "outer::right::idle")
    scenario = replace(
        parallel_scenario,
        entries=(first, inner_peer, outer_peer, second),
        parallel_regions=(
            ("outer::left", "outer::right"),
            ("outer::left::x", "outer::left::y"),
        ),
    )
    assert_result(scenario, Result((outer_peer, first, second, inner_peer)))
    with pytest.raises(AssertionError, match="expected entries"):
        assert_result(scenario, Result((outer_peer, second, first, inner_peer)))


def test_concurrent_contract_keeps_separate_parallel_groups_ordered(
    parallel_scenario: Scenario,
) -> None:
    first = (Entry(0, "first::a::idle"), Entry(0, "first::b::idle"))
    second = (Entry(0, "second::a::idle"), Entry(0, "second::b::idle"))
    scenario = replace(
        parallel_scenario,
        entries=(*first, *second),
        parallel_regions=(
            ("first::a", "first::b"),
            ("second::a", "second::b"),
        ),
    )
    assert_result(scenario, Result((*reversed(first), *reversed(second))))
    with pytest.raises(AssertionError, match="expected entries"):
        assert_result(scenario, Result((*second, *first)))


@pytest.mark.parametrize(
    ("regions", "message"),
    [
        ((), "requires explicit parallel_regions"),
        ((("lights",),), "distinct sibling paths"),
        ((("lights", "lights"),), "distinct sibling paths"),
        ((("", "sound"),), "distinct sibling paths"),
        ((("lights", "lights::nested"),), "distinct sibling paths"),
    ],
)
def test_concurrent_contract_requires_unambiguous_regions(
    parallel_scenario: Scenario,
    regions: tuple[tuple[str, ...], ...],
    message: str,
) -> None:
    scenario = replace(parallel_scenario, parallel_regions=regions)
    with pytest.raises(AssertionError, match=message):
        assert_result(scenario, Result(scenario.entries))


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


@pytest.mark.parametrize(
    ("bulk_exit", "accepted"),
    [
        (("cooling", "cooling", "bulk", "topOff", "finishing", "idle"), True),
        (("topOff", "finishing", "idle"), True),
        (("cooling", "bulk", "topOff", "finishing", "idle"), False),
        (("topOff", "cooling", "finishing", "idle"), False),
        (("finishing", "topOff", "idle"), False),
        (("topOff", "topOff", "finishing", "idle"), False),
    ],
)
def test_charging_contract_checks_complete_paths(
    bulk_exit: tuple[str, ...], accepted: bool
) -> None:
    scenario = next(
        s for s in SCENARIOS if s.name == "charging-session-thermal-detour"
    )
    prefix = (
        "idle",
        "handshake::checkCable",
        "handshake::lockConnector",
        "handshake::done",
        "authorizing",
        "authRetry",
        "authorizing",
        "rampUp",
        "rampUp",
        "rampUp",
        "bulk",
        "bulk",
        "bulk",
    )
    result = Result(
        tuple(Entry(0, state) for state in (*prefix, *bulk_exit)),
        (("sessions", 1),),
    )
    if accepted:
        assert_result(scenario, result)
    else:
        with pytest.raises(AssertionError, match="expected states"):
            assert_result(scenario, result)


def test_state_alternative_keeps_final_value_checks() -> None:
    scenario = Scenario(
        "choice",
        "model",
        "Machine",
        1000,
        (),
        states=("idle", "a"),
        alternative_states=(("idle", "b"),),
        attributes=(("count", 1),),
    )
    entries = (Entry(0, "idle"), Entry(100, "b"))
    for attributes in ((), (("count", 0),)):
        with pytest.raises(AssertionError, match=r"attribute|count="):
            assert_result(scenario, Result(entries, attributes))


def test_alternative_sequences_can_define_a_contract() -> None:
    scenario = Scenario(
        "choice",
        "model",
        "Machine",
        1000,
        (),
        alternative_states=(("idle", "a"), ("idle", "b")),
    )
    assert_result(scenario, Result((Entry(0, "idle"), Entry(100, "b"))))
    with pytest.raises(AssertionError, match="expected states"):
        assert_result(scenario, Result(()))


def test_state_sequence_rejects_an_empty_alternative() -> None:
    scenario = Scenario(
        "choice",
        "model",
        "Machine",
        1000,
        (),
        states=("idle",),
        alternative_states=((),),
    )
    with pytest.raises(AssertionError, match="must not be empty"):
        assert_result(scenario, Result(()))


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
