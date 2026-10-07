"""Check LF transition-trigger collisions in the showcase corpus."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from collections import defaultdict
from typing import TYPE_CHECKING

from sysmlc_models.catalog import model_file, model_path

if TYPE_CHECKING:
    from pathlib import Path

_REACTOR = re.compile(r"^reactor (\w+) \{")
_MODE = re.compile(r"^\s*(?:initial )?mode (\w+) \{")
_REACTION = re.compile(r"^(\s*)reaction\((.*?)\)")


def _inject(source: str) -> str:
    """Record each non-entry reaction with its runtime instance and tag."""
    output: list[str] = []
    reactor, mode = "main", "(rl)"
    for line in source.splitlines():
        if match := _REACTOR.match(line):
            reactor, mode = match[1], "(rl)"
        elif line.strip() == "main reactor {":
            reactor, mode = "main", "(rl)"
        if match := _MODE.match(line):
            mode = match[1]
        output.append(line)
        if (match := _REACTION.match(line)) and line.rstrip().endswith("{="):
            trigger = match[2].strip()
            if "reset" in trigger and "startup" in trigger:
                continue
            head = f"FIRE|{reactor}|{mode}|{trigger}|"
            output.append(
                f'{match[1]}  print("{head}" + str(id(self)) + " @ " '
                "+ str(lf.tag()), flush=True)"
            )
    return "\n".join(output) + "\n"


def check(model_name: str, work_dir: Path) -> None:
    """Compile and run one showcase part and reject trigger collisions.

    Args:
        model_name: Bundled catalog path of one showcase model directory.
        work_dir: Fresh directory for generated sources and build artifacts.

    Raises:
        AssertionError: If build, execution or collision checks fail.
        OSError: If a required compiler or executable cannot be launched.
        subprocess.TimeoutExpired: If compilation or execution times out.
    """
    from sysmlc_models._validation import command

    directory = model_path(model_name)
    src = work_dir / "src"
    src.mkdir(parents=True)
    arguments = [
        sys.executable,
        "-m",
        "sysmlc.cli",
        "rosetta",
        "build",
        str(directory),
        "-o",
        str(src),
        "--fast",
        "--timeout",
        "30 sec",
    ]
    support = sorted(directory.glob("*.py"))
    if len(support) == 1:
        arguments.extend(("--python", str(support[0])))
    elif model_name == "showcase/furuta-pendulum/deterministic":
        arguments.extend(
            (
                "--python",
                str(model_file("showcase/furuta-pendulum/furuta_physics.py")),
            )
        )
    command(arguments, work_dir)
    sources = list(src.glob("*.lf"))
    assert len(sources) == 1, sources
    source = sources[0].read_text()
    main = src / "Main.lf"
    sources[0].rename(main)
    main.write_text(_inject(source))
    command(["lfc", str(main)], work_dir, timeout=600)
    process = subprocess.run(
        [str(work_dir / "bin" / "Main")],
        cwd=work_dir,
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, "PYTHONPATH": str(src)},
    )
    assert process.returncode == 0, process.stdout + process.stderr
    fires: dict[tuple[str, str, str, str], set[str]] = defaultdict(set)
    for line in process.stdout.splitlines():
        if line.startswith("FIRE|"):
            head, _, tag = line.partition(" @ ")
            _, reactor, mode, trigger, instance = head.split("|", 4)
            if "." not in trigger and trigger not in {
                "reset, startup",
                "startup",
                "reset",
                "current_state",
            }:
                fires[(instance, reactor, mode, tag)].add(trigger)
    assert fires, "no transition reaction observations"
    collisions = {
        key: sorted(triggers)
        for key, triggers in fires.items()
        if len(triggers) >= 2
    }
    assert not collisions, f"{model_name}: trigger collisions {collisions}"
