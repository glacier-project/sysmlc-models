"""Compile and execute scenario contracts with Statix's native C runner."""

from __future__ import annotations

import json
import re
import subprocess
from typing import TYPE_CHECKING

from sysmlc.backends.base import OutputOptions
from sysmlc_statix.backend import StatixBackend
from sysmlc_statix.builder import build_statix

from sysmlc_models._validation import command, constraint_violation, load
from sysmlc_models.validation import Entry, Result

if TYPE_CHECKING:
    from pathlib import Path

    from sysmlc_models.validation import Scalar, Scenario


def run(scenario: Scenario, work_dir: Path) -> Result:
    """Execute explicit clock updates and inputs with the generated C runner.

    Runner trace lines precede each command's status line. The corresponding
    command supplies their time; Statix timers fire when that tick is posted.

    Args:
        scenario: The model execution contract to verify.
        work_dir: Directory containing the generated project.

    Returns:
        Leaf/completion entries and requested final context values.

    Raises:
        ValueError: If the model or configuration cannot be loaded.
        AssertionError: If compilation, execution or trace decoding fails.
        OSError: If a required native tool cannot be launched.
        subprocess.TimeoutExpired: If a command exceeds its safety limit.
    """
    model, paths = load(scenario)
    program = build_statix(model, scenario.element)
    StatixBackend().write(program, OutputOptions(output_dir=work_dir))
    build = work_dir / "build"
    command(["cmake", "-S", str(work_dir), "-B", str(build)], work_dir)
    command(["cmake", "--build", str(build)], work_dir)
    times = sorted(
        {scenario.horizon_ms, *scenario.ticks_ms}
        | {event.time_ms for event in scenario.inputs}
    )
    arguments: list[str] = []
    command_times = [0]
    for time_ms in times:
        if program.has_timer:
            arguments.extend(("--tick", str(time_ms)))
            command_times.append(time_ms)
        for event in scenario.inputs:
            if event.time_ms == time_ms:
                arguments.append(event.signal)
                command_times.append(time_ms)
    process = subprocess.run(
        [str(build / f"{program.prefix}_runner"), *arguments],
        cwd=work_dir,
        capture_output=True,
        text=True,
        timeout=120,
    )
    output = process.stdout
    entries: list[Entry] = []
    pending: list[str] = []
    statuses: list[str] = []
    failure = None
    last_guard: tuple[str, str, str] | None = None
    for line in output.splitlines():
        guard = re.fullmatch(
            r"  trace: guard=(\S+) state=(\S+) result=(true|false)", line
        )
        if guard is not None:
            last_guard = (guard[1], guard[2], guard[3])
            continue
        match = re.fullmatch(r"  trace: enter state=(\S+) slot=\d+", line)
        if match is not None and match[1] in paths:
            pending.append(match[1])
        elif "status=" in line:
            status = re.search(r"\bstatus=(\S+)", line)
            assert status is not None, line
            assert failure is None, "runner continued after a violation"
            if status[1] == "SC_STATUS_CONSTRAINT_VIOLATED":
                assert process.returncode == 1, output + process.stderr
                assert last_guard is not None and last_guard[2] == "false", (
                    "constraint violation has no failed check identity"
                )
                matching = tuple(
                    invariant
                    for invariant in program.invariants
                    if invariant.guard == last_guard[0]
                    and (invariant.scope or "SC_STATE_INVALID") == last_guard[1]
                )
                assert len(matching) == 1, "unknown constraint check identity"
                invariant = matching[0]
                assert invariant.check_id is not None
                failure = constraint_violation(
                    scenario.element,
                    invariant.scope or "",
                    invariant.name,
                    invariant.check_id,
                )
            else:
                assert status[1] in {
                    "SC_STATUS_OK",
                    "SC_STATUS_NO_TRANSITION",
                }, line
            assert len(statuses) < len(command_times), output
            time_ms = command_times[len(statuses)]
            entries.extend(Entry(time_ms, state) for state in pending)
            pending.clear()
            statuses.append(line)
            last_guard = None
    if failure is None:
        assert process.returncode == 0, output + process.stderr
        assert len(statuses) == len(command_times), output
    assert not pending, output
    attributes: list[tuple[str, Scalar]] = []
    for name, _ in scenario.attributes:
        match = re.search(rf"\bctx\.{re.escape(name)}=(\S+)", statuses[-1])
        assert match is not None, f"missing context value {name}: {output}"
        attributes.append((name, json.loads(match[1])))
    return Result(tuple(entries), tuple(attributes), failure)
