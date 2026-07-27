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
| `sm-examples/` |     26 | the SysML state-machine example corpus, `sm01-helloworld` onward, plus the `part*` multi-machine fixtures                 |
| `showcase/`    |     11 | end-to-end showcase systems (furuta-pendulum, thermostat, milling-workcell, …)                                            |
| `ice-lab/`     |      6 | the industrial ICE-lab plant: plant definition, recipes, domain models, equipment state machines, OPC-UA service metadata |

## Installation

The core and the backends pull this package in through their `dev` and
`models` extras, so a normal `uv sync --extra dev` in any of them installs it.
To install it on its own:

```bash
uv pip install git+https://github.com/glacier-project/sysmlc-models@dev
```

## Usage

```python
from sysmlc_models.catalog import model_path, model_file, iter_models

# a corpus or a model directory
model_path("sm-examples/sm01-helloworld")
# a single file within a corpus
model_file("showcase/furuta-pendulum/furuta_physics.py")
# every model directory in a corpus
iter_models("sm-examples")
```

The curated single-machine example list is exposed by
`sysmlc_models.sm_examples` (`SM_EXAMPLES`, `SM_EXAMPLES_BY_DIR`,
`SM_EXAMPLES_DIR`); the showcase root by `sysmlc_models.showcase`
(`SHOWCASE_DIR`).

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
