"""Execute scenario contracts with Quake's generated Sismic statecharts."""

from __future__ import annotations

import importlib.util
import sys
from typing import TYPE_CHECKING

from sismic.clock import SimulatedClock
from sismic.interpreter import Interpreter
from sysmlc.sysml.foreign_artifact.base import ForeignArtifact
from sysmlc.sysml.loading import load_model
from sysmlc.sysml.queries import state_definitions
from sysmlc_quake.builder import build_statechart_artifact
from sysmlc_quake.runner import run_part_system

from sysmlc_models._validation import load
from sysmlc_models.catalog import model_file, model_path
from sysmlc_models.validation import Entry, Result

if TYPE_CHECKING:
    from pathlib import Path

    from sysmlc_models.validation import Scenario


def run(scenario: Scenario, work_dir: Path) -> Result:
    """Execute a manually clocked scenario and return runtime observations.

    Args:
        scenario: The model execution contract to verify.
        work_dir: Directory containing the generated project.

    Returns:
        Leaf/completion entries and requested final context values.

    Raises:
        ValueError: If the model or configuration cannot be loaded.
        sismic.exceptions.SismicError: If execution violates the target policy.
        AssertionError: If execution exhausts the macrostep safety limit.
    """
    model, paths = load(scenario)
    if scenario.kind == "part":
        external = (
            [ForeignArtifact(model_file(scenario.support), "python")]
            if scenario.support is not None
            else []
        )
        stem = external[0].path.stem if external else None
        previous = sys.modules.get(stem) if stem is not None else None

        def load_external() -> None:
            for artifact in external:
                spec = importlib.util.spec_from_file_location(
                    artifact.path.stem, artifact.path
                )
                assert spec is not None and spec.loader is not None
                module = importlib.util.module_from_spec(spec)
                sys.modules[artifact.path.stem] = module
                spec.loader.exec_module(module)

        try:
            report = run_part_system(
                model,
                scenario.element,
                until=scenario.horizon_ms / 1000,
                max_steps=100000,
                external=external,
                load_external=load_external,
            )
        finally:
            if stem is not None:
                if previous is None:
                    sys.modules.pop(stem, None)
                else:
                    sys.modules[stem] = previous
        assert not report.hit_step_cap, report.render()
        part_entries = tuple(
            Entry(round(step.step.time * 1000), f"{step.instance}::{state}")
            for step in report.trace
            for state in step.step.entered_states
        )
        return Result(part_entries)
    artifact = build_statechart_artifact(model, scenario.element)
    if artifact.types_module is not None:
        artifact.types_module.install()
    clock = SimulatedClock()
    interpreter = Interpreter(artifact.statechart, clock=clock)
    times = sorted(
        {0, scenario.horizon_ms, *scenario.ticks_ms}
        | {event.time_ms for event in scenario.inputs}
    )
    entries: list[Entry] = []
    for time_ms in times:
        clock.time = time_ms / 1000
        for event in scenario.inputs:
            if event.time_ms == time_ms:
                interpreter.queue(event.signal)
        steps = interpreter.execute(max_steps=1000)
        assert len(steps) < 1000, "scenario exhausted its macrostep limit"
        entries.extend(
            Entry(round(step.time * 1000), state)
            for step in steps
            for state in step.entered_states
            if state in paths
        )
    attributes = tuple(
        (name, interpreter.context[name]) for name, _ in scenario.attributes
    )
    return Result(tuple(entries), attributes)


def check_initialization(model_name: str) -> None:
    """Verify that every state definition initializes without runtime errors.

    Args:
        model_name: Bundled catalog path of one model directory.

    Raises:
        ValueError: If the sources or state semantics are invalid.
        sismic.exceptions.SismicError: If generated expressions cannot run.
        AssertionError: If initialization exhausts the macrostep safety limit.
    """
    model = load_model(model_path(model_name))
    for state in state_definitions(model):
        name = str(state.qualified_name)
        artifact = build_statechart_artifact(model, name)
        if artifact.types_module is not None:
            artifact.types_module.install()
        steps = Interpreter(artifact.statechart).execute(max_steps=1000)
        assert len(steps) < 1000, f"{name}: startup exceeded the step limit"
