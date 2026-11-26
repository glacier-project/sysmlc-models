"""Run the bundled PSSM-derived trace scenarios on Rosetta."""

import argparse
import json
import tempfile
from pathlib import Path

from sysmlc_models._validation import rosetta
from sysmlc_models.catalog import model_path
from sysmlc_models.validation import Input, Scenario


def run_case(directory: Path) -> bool:
    """Execute one case and compare its final log with the admitted traces."""
    case = json.loads((directory / "scenario.json").read_text())
    inputs = tuple(
        Input(
            event["time_ms"],
            event["signal"],
            tuple(map(tuple, event["fields"])),
        )
        for event in case["inputs"]
    )
    scenario = Scenario(
        case["id"],
        f"pssm/{directory.name}",
        case["element"],
        max((event.time_ms for event in inputs), default=0) + 1000,
        (),
        inputs=inputs,
        attributes=(("log", ""),),
        backends=("rosetta",),
    )
    with tempfile.TemporaryDirectory() as work:
        result = rosetta.run(scenario, Path(work))
    log = dict(result.attributes).get("log")
    trace = log.removesuffix("::") if isinstance(log, str) else None
    ok = result.failure is None and trace in case["expected_traces"]
    print(f"{directory.name}: {'PASS' if ok else 'FAIL'} {trace!r}", flush=True)
    if not ok:
        print(
            f"Expected {case['expected_traces']}; runtime failure: {result.failure}"
        )
    return ok


def main() -> int:
    """Run a named case or all cases and report any trace mismatch."""
    cases = sorted(p.parent for p in model_path("pssm").glob("*/scenario.json"))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", nargs="?", choices=[p.name for p in cases])
    selected = parser.parse_args().case
    outcomes = [run_case(p) for p in cases if selected in (None, p.name)]
    return int(not all(outcomes))


if __name__ == "__main__":
    raise SystemExit(main())
