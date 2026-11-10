"""Compile and execute scenario contracts with LF's Python or C target."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import asdict, replace
from typing import TYPE_CHECKING

from sysmlc.semantics.statemachine.driver import StateMachineDriver
from sysmlc.semantics.statemachine.signals import SignalCatalog
from sysmlc.sysml.foreign_artifact.base import ForeignArtifact
from sysmlc_rosetta.backend import RosettaBackend
from sysmlc_rosetta.builder import RosettaBuilder, finalize
from sysmlc_rosetta.codegen import PreambleNeeds
from sysmlc_rosetta.program import LfProgram, Mode, Reaction, Reactor
from sysmlc_rosetta.serialize import to_lf
from sysmlc_rosetta.targets import TARGETS, CTarget, PythonTarget

from sysmlc_models._validation import command, constraint_violation, load
from sysmlc_models.catalog import model_file
from sysmlc_models.validation import ConstraintViolation, Entry, Result

if TYPE_CHECKING:
    from pathlib import Path

    from sysmlc.semantics.statemachine.facts import StateFact
    from sysmlc_rosetta.targets.base import LfTarget

    from sysmlc_models.validation import Scalar, Scenario


class _ObservedBuilder(RosettaBuilder):
    def _composite_reactor(
        self, scope: str, container: StateFact, *, is_root: bool
    ) -> Reactor:
        # The assembly hook carries the original neutral scope, including
        # parallel regions. Never infer SysML paths from generated names.
        reactor = super()._composite_reactor(scope, container, is_root=is_root)
        return _observe_modes(reactor, scope, self._target)


def _observe_modes(reactor: Reactor, scope: str, target: LfTarget) -> Reactor:
    modes: list[Mode] = []
    for mode in reactor.modes:
        path = f"{scope}::{mode.name}" if scope else mode.name
        entry, *rest = mode.reactions
        (observation,) = target.render((target.observe_entry(path),))
        modes.append(
            replace(
                mode,
                reactions=(
                    replace(entry, body=(observation, *entry.body)),
                    *rest,
                ),
            )
        )
    return replace(reactor, modes=tuple(modes))


def run(scenario: Scenario, work_dir: Path, target: str = "python") -> Result:
    """Compile a generated LF machine and observe its logical-time entries.

    Args:
        scenario: The model execution contract to verify.
        work_dir: Directory containing the generated project.
        target: The LF target language, ``python`` or ``c``.

    Returns:
        Leaf/completion entries and requested final context values.

    Raises:
        ValueError: If the model or configuration cannot be loaded.
        AssertionError: If compilation or execution fails.
        OSError: If LF's compiler or generated executable cannot be launched.
        subprocess.TimeoutExpired: If a command exceeds its safety limit.
    """
    model, paths = load(scenario)
    name = scenario.element.split("::")[-1]
    lang: LfTarget = TARGETS[target]()
    external = _support(scenario, lang)
    if scenario.kind == "part":
        built = RosettaBackend(target).build_part(
            model,
            scenario.element,
            external=external,
            target_options=(
                ("fast", "true"),
                ("timeout", f"{scenario.horizon_ms} msec"),
            ),
        )
        assert isinstance(built, LfProgram) and built.main is not None
        instances = {i.reactor: i.name for i in built.main.instantiations}
        assert len(instances) == len(built.main.instantiations), (
            "part observation requires one instance of each reactor class"
        )
        program = replace(
            built,
            reactors=tuple(
                _observe_modes(r, instances[r.name], lang)
                if r.name in instances
                else r
                for r in built.reactors
            ),
        )
    else:
        needs = PreambleNeeds(
            catalog=SignalCatalog(model, [scenario.element]), target=lang
        )
        needs.types_module = f"{name}_types"
        program = StateMachineDriver(model).run(
            scenario.element,
            _ObservedBuilder(name, needs=needs, source_qn=scenario.element),
        )
        assert isinstance(program, LfProgram)
        program = finalize(program, needs)
    if isinstance(lang, PythonTarget) and (
        scenario.attributes or any(event.fields for event in scenario.inputs)
    ):
        program = replace(program, preamble=(*program.preamble, "import json"))
    if scenario.attributes:
        types = {var.name: var.type for var in program.reactor.state_vars}
        observer = Reaction(
            triggers=("shutdown",),
            body=lang.render(
                tuple(
                    lang.observe_value(attr, types.get(attr))
                    for attr, _ in scenario.attributes
                )
            ),
        )
        root = replace(
            program.reactor,
            reactions=(*program.reactor.reactions, observer),
        )
        program = replace(
            program,
            reactors=(*program.reactors[:-1], root),
        )
    src = work_dir / "src"
    src.mkdir()
    for artifact in external:
        shutil.copy(artifact.path, src / artifact.path.name)
    if program.types_module_name is not None:
        (src / f"{program.types_module_name}.py").write_text(
            "\n".join(program.types_module_lines) + "\n"
        )
    for file_name, text in program.support_files:
        (src / file_name).write_text(text)
    drivers: list[str] = []
    for index, event in enumerate(scenario.inputs):
        signal = program.resolve_signal(event.signal)
        (driver,) = lang.render(
            (
                lang.set_port(
                    f"m.{signal}", _payload(program, lang, signal, event.fields)
                ),
            )
        )
        drivers.extend(
            (
                f"  timer input_{index}({event.time_ms} msec)",
                f"  reaction(input_{index}) -> m.{signal} {{=",
                f"    {driver}",
                "  =}",
            )
        )
    harness = src / "Harness.lf"
    if scenario.kind == "part":
        harness.write_text(to_lf(program))
    else:
        (src / f"{name}.lf").write_text(to_lf(program))
        harness.write_text(
            f"target {lang.lf_name} {{\n  fast: true,\n"
            f"  timeout: {scenario.horizon_ms} msec\n"
            "}\n"
            f'import {name} from "{name}.lf"\n'
            "main reactor {\n"
            f"  m = new {name}()\n" + "\n".join(drivers) + "\n}\n"
        )
    command(["lfc", str(harness)], work_dir, timeout=600)
    process = subprocess.run(
        [str(work_dir / "bin" / "Harness")],
        cwd=work_dir,
        env={**os.environ, "PYTHONPATH": str(src)},
        capture_output=True,
        text=True,
        timeout=120,
    )
    failure = (
        _failure(program, process.stdout + process.stderr)
        if process.returncode != 0
        else None
    )
    entries: list[Entry] = []
    attributes: list[tuple[str, Scalar]] = []
    for line in process.stdout.splitlines():
        if line.startswith("__SYSMLC_ENTRY__ "):
            _, time, state = line.split(" ", 2)
            if scenario.kind == "part" or state in paths:
                entries.append(Entry(int(time), state))
        elif line.startswith("__SYSMLC_VALUE__ "):
            _, attr, value = line.split(" ", 2)
            attributes.append((attr, json.loads(value)))
    return Result(tuple(entries), tuple(attributes), failure)


def _support(scenario: Scenario, lang: LfTarget) -> list[ForeignArtifact]:
    """The scenario's support code: its Python file, or the C port beside it."""
    if scenario.support is None:
        return []
    path = model_file(scenario.support)
    if isinstance(lang, PythonTarget):
        return [ForeignArtifact(path, "python")]
    return [
        ForeignArtifact(path.with_suffix(".c"), "c"),
        ForeignArtifact(path.with_suffix(".h"), "c_h"),
    ]


def _payload(
    program: LfProgram,
    lang: LfTarget,
    signal: str,
    fields: tuple[tuple[str, Scalar], ...],
) -> str:
    """A driver's payload: a bare signal, or the scenario's field values."""
    if not fields:
        return lang.boolean(True)
    if isinstance(lang, CTarget):
        ctype = dict(program.reactor.port_types)[signal]
        values = ", ".join(
            f".{field} = {lang.types.field_literal(ctype, field, value)}"
            for field, value in fields
        )
        return f"({ctype}){{ {values} }}"
    return (
        'sys.modules["types"].SimpleNamespace(**json.loads('
        + json.dumps(json.dumps(dict(fields)))
        + "))"
    )


def _failure(program: LfProgram, diagnostic: str) -> ConstraintViolation | str:
    """Decode a generated assertion's check identity or retain a crash.

    Args:
        program: Compiled LF program containing source identities.
        diagnostic: Captured diagnostics from the failed executable.

    Returns:
        A verified constraint identity, or the generic runtime diagnostic.

    Raises:
        AssertionError: If assertion identities are malformed, unknown or
            refer to multiple different violated constraints.
    """
    payloads = re.findall(
        r"^AssertionError: SysML constraint violated: (.+)$",
        diagnostic,
        re.MULTILINE,
    )
    if not payloads:
        return diagnostic
    known = {
        (constraint.reactor, constraint.check_id): constraint
        for constraint in program.constraints
    }
    failures: set[ConstraintViolation] = set()
    for text in payloads:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as error:
            raise AssertionError("malformed constraint identity") from error
        assert isinstance(payload, dict), "malformed constraint identity"
        assert (
            isinstance(payload.get("reactor"), str)
            and type(payload.get("check_id")) is int
        ), "malformed constraint identity"
        key = (payload["reactor"], payload["check_id"])
        constraint = known.get(key)
        assert constraint is not None and payload == asdict(constraint), (
            f"unknown constraint identity: {payload!r}"
        )
        failures.add(
            constraint_violation(
                constraint.behavior,
                constraint.scope,
                constraint.name,
                constraint.check_id,
            )
        )
    assert len(failures) == 1, "multiple different violated constraints"
    return next(iter(failures))
