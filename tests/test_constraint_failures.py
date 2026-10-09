from __future__ import annotations

import json
import os
from dataclasses import asdict
from typing import TYPE_CHECKING

import pytest

from sysmlc_models.validation import (
    ConstraintViolation,
    Result,
    Scenario,
    assert_result,
)

if TYPE_CHECKING:
    from sysmlc_rosetta.program import LfProgram

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.environ.get("SYSMLC_VALIDATION_BACKEND") != "rosetta",
        reason="Rosetta adapter checks require the Rosetta validation extra",
    ),
]


def _program() -> LfProgram:
    from sysmlc_rosetta.program import LfConstraint, LfProgram, Reactor

    return LfProgram(
        (Reactor("Machine"),),
        constraints=(
            LfConstraint(
                "Machine", 0, "", "setpointPositive", "Package::Machine"
            ),
            LfConstraint("Machine", 1, "", "tempBand", "Package::Machine"),
        ),
    )


def test_assertion_identity_is_decoded_independently_of_traceback_text() -> (
    None
):
    from sysmlc_models._validation.rosetta import _failure

    program = _program()
    report = "AssertionError: SysML constraint violated: " + json.dumps(
        asdict(program.constraints[0])
    )
    observed = _failure(
        program, "Traceback (most recent call last):\n" + report
    )
    assert observed == ConstraintViolation(
        "setpointPositive", "Package::Machine"
    )
    assert _failure(program, report + "\n" + report) == observed


def test_part_failure_keeps_the_behavior_scope_instead_of_the_system() -> None:
    from sysmlc_models._validation.rosetta import _failure

    expected = ConstraintViolation("setpointPositive", "Package::Machine")
    scenario = Scenario(
        "bad-part",
        "model",
        "Package::system",
        1000,
        (),
        kind="part",
        failure=expected,
    )
    program = _program()
    report = "AssertionError: SysML constraint violated: " + json.dumps(
        asdict(program.constraints[0])
    )
    assert_result(scenario, Result((), failure=_failure(program, report)))


@pytest.mark.parametrize(
    "diagnostic",
    [
        "ModuleNotFoundError: setpointPositive",
        "AssertionError: unrelated failure mentioning setpointPositive",
        '  assert False, "SysML constraint violated: setpointPositive"',
        "SC_STATUS_CONSTRAINT_VIOLATED setpointPositive",
    ],
)
def test_diagnostic_mentions_do_not_become_constraint_observations(
    diagnostic: str,
) -> None:
    from sysmlc_models._validation.rosetta import _failure

    assert _failure(_program(), diagnostic) == diagnostic


@pytest.mark.parametrize(
    "payload",
    [
        "{",
        "[]",
        "{}",
        '{"reactor":"Machine","check_id":false}',
        '{"reactor":"Machine","check_id":8,"scope":"","name":"setpointPositive","behavior":"Package::Machine"}',
        '{"reactor":"Machine","check_id":0,"scope":"","name":"tempBand","behavior":"Package::Machine"}',
        '{"reactor":"Other","check_id":0,"scope":"","name":"setpointPositive","behavior":"Package::Machine"}',
        '{"reactor":"Machine","check_id":0,"scope":"","name":"setpointPositive","behavior":"Package::Other"}',
    ],
)
def test_malformed_or_unknown_check_identities_are_rejected(
    payload: str,
) -> None:
    from sysmlc_models._validation.rosetta import _failure

    diagnostic = "AssertionError: SysML constraint violated: " + payload
    with pytest.raises(AssertionError):
        _failure(_program(), diagnostic)


def test_different_failed_constraints_are_not_silently_collapsed() -> None:
    from sysmlc_models._validation.rosetta import _failure

    program = _program()
    diagnostic = "\n".join(
        "AssertionError: SysML constraint violated: " + json.dumps(asdict(c))
        for c in program.constraints
    )
    with pytest.raises(AssertionError, match="multiple different"):
        _failure(program, diagnostic)
