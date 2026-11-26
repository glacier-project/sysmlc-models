# PSSM-derived scenarios

The 24 models under `sysmlc_models/data/pssm/` translate state machines from
[OMG PSSM 1.0](https://www.omg.org/spec/PSSM/1.0/) into SysML v2. In each
folder, `scenario.json` identifies the SemanticTest and specification clause,
the property and its SysML mapping, timed inputs, and admitted trace strings.
Some formulations preserve a property for the specified inputs through
explicit state or data. History 001 A remembers the last visited leaf in a
Boolean, for example.

The [OMG suite XMI](https://www.omg.org/spec/PSSM/20181101/PSSM_TestSuite.xmi)
has SHA-256 `c355b249c356774377a46b60345019d827af1ce417bde88e533aa5f39206ae07`.

## Running the examples

Install this checkout editable with the `validation-rosetta` extra. The runner
requires licensed Syside and the LF Python target toolchain, with `lfc` on
PATH. From this repository, run one scenario or all of them:

```sh
python scripts/run_pssm.py 030-event-017-a
python scripts/run_pssm.py
```

The driver compiles each machine, delivers the listed inputs at logical times
in milliseconds, and reads the machine's `log` attribute at shutdown one
second after the last input. A case passes when execution succeeds and the
observed action markers match one of its admitted SysML traces. A single
execution covers the observed ordering and the specified inputs.

The validation baseline uses core `824e5772a7a9`, Rosetta `0ff85db1bd39`
(including the state identifier and nested attribute changes), and LF 0.13.0.
The models package does not pin those compiler revisions.

## Capabilities identified across the 103 scenarios

These counts refer to the assessed formulations. A case can require multiple
features. A sole blocker identifies a candidate for execution once support
exists. It does not predict the resulting trace.

| Capability                                                        | Example              | Owning layer                 | Cases requiring it |  Sole known blocker |
| ----------------------------------------------------------------- | -------------------- | ---------------------------- | -----------------: | ------------------: |
| Observe concurrent actions without a shared writable log          | Exiting 005          | Scenario adapter             |                 15 |                   9 |
| Validate downstream guards before committing the source exit      | Junction paths       | Core and backend             |                 12 |                   4 |
| Enter an explicitly targeted nested state                         | Entering 005         | Core and backend             |                 12 |                   3 |
| Retain and later release deferred events                          | Deferred 001         | Profile and runtime          |                 11 |                   5 |
| Suspend a do activity on accept, resume it, and cancel it on exit | Behavior 003 A/B     | Action semantics and backend |                  8 |                   3 |
| Resolve inherited members and extract the effective source graph  | Redefinition 001–006 | Core and source extraction   |                  6 | 5 with both changes |

The assessment found 24 matching cases with the standard scenario adapter
and five additional matches with an experimental observer. This corpus covers
the standard adapter cases. Ten other cases had a proposed mapping with no
identified blocker and still required execution.
