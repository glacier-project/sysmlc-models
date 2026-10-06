# Furuta pendulum variants

This showcase has two state-machine variants and one shared external Python
implementation:

| Variant | Transition semantics | Python implementation |
| --- | --- | --- |
| `deterministic/` | Complementary controller guards; suitable for Quake and Rosetta | `../furuta_physics.py` |
| `nondeterministic/` | Reference declaration-order model; suitable for Rosetta/LF | Embedded textual representations, or `../furuta_physics.py` as an explicit override |

The nondeterministic variant intentionally has overlapping same-source
transitions. LF gives those reactions declaration-order priority, whereas
SysML does not define that tie-break. The deterministic variant encodes the
same priority with complementary guards, so at most one transition accepts a
reading.

`furuta_physics.py` is backend-neutral. It reconstructs `type(x)` rather than
importing a backend-specific companion module, so the same file works with
Rosetta's `furutaSystem_types` and Quake's
`FurutaPendulum_furutaSystem_types`.

Examples:

```bash
sysmlc quake run showcase/furuta-pendulum/deterministic \
  --python showcase/furuta-pendulum/furuta_physics.py \
  --until 2

sysmlc rosetta build showcase/furuta-pendulum/nondeterministic \
  --fast --timeout "30 sec"
```

The second command uses the nondeterministic model's embedded Python textual
representations. Supplying `--python showcase/furuta-pendulum/furuta_physics.py`
instead exercises the external-module path. `furuta_physics.c` is retained as
the reference C implementation; it is not consumed by the Python backends.
