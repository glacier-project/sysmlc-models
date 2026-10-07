# 📚 sysmlc-models

SysML v2 model corpora and a small catalog API for the
[sysmlc](https://github.com/glacier-project/sysmlc-core) toolchain.

**Status:** in development.

## Overview

This package carries no compiler code: it ships the SysML v2 models the
toolchain is developed and tested against, plus the catalog API that resolves
them by name. The core's CLI uses that catalog, which is what lets any command
take `sm-examples/sm01-helloworld` in place of a filesystem path.

The corpora ship as package data under `sysmlc_models/data/`:

| Corpus         | Models | Contents                                                                                                                  |
| -------------- | -----: | ------------------------------------------------------------------------------------------------------------------------- |
| `sm-examples/` |     25 | the SysML state-machine example corpus, `sm01-helloworld` onward, plus the `part*` multi-machine fixtures                 |
| `showcase/`    |     11 | end-to-end showcase models and variants (Furuta pendulum, thermostat, milling workcell, …)                                |
| `ice-lab/`     |      6 | the industrial ICE-lab plant: plant definition, recipes, domain models, equipment state machines, OPC-UA service metadata |

## Installation

The core and the backends pull this package in through their `dev` and
`models` extras, so a normal `uv sync --extra dev` in any of them installs it.
To install it on its own:

```bash
uv pip install git+https://github.com/glacier-project/sysmlc-models@main
```

## Usage

```python
from sysmlc_models.catalog import model_path, model_file, iter_models

# a corpus or a model directory
model_path("sm-examples/sm01-helloworld")
model_path("showcase/furuta-pendulum/deterministic")
# a single file within a corpus
model_file("showcase/furuta-pendulum/furuta_physics.py")
# every directory containing SysML sources, including nested variants
iter_models("sm-examples")
```

The curated single-machine example list is exposed by
`sysmlc_models.sm_examples` (`SM_EXAMPLES`, `SM_EXAMPLES_BY_DIR`,
`SM_EXAMPLES_DIR`); the showcase root by `sysmlc_models.showcase`
(`SHOWCASE_DIR`).

## Model validation

Execution scenarios and their expectations live in
`sysmlc_models.scenarios.SCENARIOS`. Each scenario names its model and
element, input occurrences, logical-time horizon, and either an exact
state-entry trace, ordered state sequence, required completion milestones,
or a named runtime failure. Inputs can carry scalar payload fields.
Scalar overrides and
final values are part of the same contract. A successful compile or an
exit code of zero cannot replace these observations.

The optional adapters compile and execute Quake statecharts, Rosetta LF
programs, or Statix C projects. The base catalog still has no dependencies.
Select a backend with an option or `SYSMLC_VALIDATION_BACKEND`:

```bash
uv sync --extra dev --extra validation-quake
uv run --extra validation-quake python -m sysmlc_models.validation \
  --backend quake --work-dir /tmp/model-validation

# Parameterized pytest results, one report for each scenario.
SYSMLC_VALIDATION_BACKEND=quake uv run --extra dev \
  --extra validation-quake pytest -m integration tests
```

Use `validation-rosetta` or `validation-statix` for the other targets.
Rosetta requires Java and `lfc` (the model CI uses LF 0.11); Statix requires
`cc` and CMake. Compiler-dependent checks require `SYSIDE_LICENSE_KEY`.
Use a fresh work directory for each run to retain failed build artifacts.

Model PRs run a Quake/Rosetta/Statix matrix; each backend's existing native
suite imports this catalog and invokes the same validator against that
backend. Unsupported scenarios are explicitly scoped in `backends`, such
as the parallel-join case excluded from Quake. Expected behavior is defined
by the model, rather than inferred from another backend's output.

Furuta physics is checked here against simple structural data classes.
The external implementation runs in the default unit suite; the embedded
implementation is extracted by core in the compiler suite:

```bash
uv run --extra dev --extra compiler pytest -m compiler tests
```

The catalog covers assignment and effect values, nested and parallel states,
completion joins and restart, absolute deadlines, and the showcase behavior
and fault paths. Paired showcase testbenches must reach `tb::done` before
their failure deadline and never enter `tb::fail`; a clean timeout cannot
satisfy that contract. The Rosetta matrix also retains the full showcase
transition-trigger collision check. Shipped YAML configurations are checked
against their documented neutral values in the compiler suite.

The deterministic Furuta part also runs on Quake and Rosetta. Its monitor
must complete within 15 logical seconds, and its failure state must never
be entered. Small state-machine tests in the backend repositories verify
their different policies for competing enabled transitions.

| Test responsibility                                           | Repository   |
| ------------------------------------------------------------- | ------------ |
| Shared semantics, YAML configuration and override diagnostics | core         |
| Model trajectories, physics, verdicts and logical deadlines   | models       |
| Generated types, target code, runtime ABI and target policy   | each backend |

Showcase cases keep the backend support of the migrated tests. Quake's
library rejects absolute `at` triggers, and Statix's host runner accepts
payload-free inputs; those cases explicitly select their supported targets.

Keep target-specific tests when their purpose is a generated artifact or
native runtime contract. Remove a duplicated model execution only after
the shared scenario verifies its behavior. Merge this API first, followed
by core's test relocation and then the backend consumers; backend CI pins
models to `main` until that first PR lands.

## Adding a model

1. Create the model directory under the right corpus in `sysmlc_models/data/`.
1. Validate it with `syside check` from the model directory.
1. For `sm-examples`, add the entry to the curated list in
   `sysmlc_models/sm_examples.py`.

Package data is matched by glob, so a new directory ships without any
packaging change. `uv run tox run -e build` verifies that the built wheel
actually contains it.

## Layout

```
sysmlc_models/
├── catalog.py       # model_path, model_file, iter_models
├── sm_examples.py   # the curated state-machine example list
├── showcase.py      # the showcase corpus root
└── data/            # the corpora themselves, shipped as package data
    ├── sm-examples/
    ├── showcase/
    └── ice-lab/
```

## Development

```bash
uv run tox                       # tests, type checking, formatting, packaging
uv run pytest tests              # tests only
uv run pyrefly check             # type checking
uv run tox run -e formatter      # ruff check --fix and ruff format
uv run tox run -e build          # build the wheel and check its contents
uv run pre-commit install        # once after cloning
```

Validating the SysML itself needs the `syside` CLI and a
[Syside Automator](https://docs.sensmetry.com/automator/index.html) license
key (`SYSIDE_LICENSE_KEY`); the Python test suite does not.
