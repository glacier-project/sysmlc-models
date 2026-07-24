# sysmlc-models

SysML v2 model corpora and a small catalog API for the
[sysmlc](https://github.com/glacier-project/sysmlc) toolchain.

The corpora ship as package data under `sysmlc_models/data/`:

- `sm-examples/` : the SysML state-machine example corpus
- `showcase/` : end-to-end showcase models
- `ice-lab/` : the industrial ICE-lab plant model

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
`sysmlc_models.sm_examples` (`SM_EXAMPLES`, `SM_EXAMPLES_BY_DIR`).
