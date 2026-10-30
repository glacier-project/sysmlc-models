# SM19: payload construction

Each machine sends one item value to its own port and accepts the same
exact type, so no subtype matching is involved. The accept effect copies the
received fields into `capturedX` and `capturedY`; both start at `-1`, a value
no constructor below produces.

`Data` declares `x` with default `7` and `y` with default `9`. `Child`
specializes `Data` without changes; `Redefined` redefines `x` with default
`11`.

Following KerML 1.0 (8.3.4.8.3, 8.4.4.9.4 and 8.4.4.11), a constructor
binds positional arguments to the public fields in declaration order and
named arguments to the field they name. Every field without an argument
takes its effective default: the default declared on that feature, including
a redefinition's own default.

| Machine | Constructor | x | y |
| --- | --- | --- | --- |
| `MachinePositional` | `new Data(13, 42)` | 13 | 42 |
| `MachineNamedPartial` | `new Data(y = 42)` | 7 | 42 |
| `MachineDefaults` | `new Data()` | 7 | 9 |
| `MachineInheritedDefaults` | `new Child()` | 7 | 9 |
| `MachineInheritedNamed` | `new Child(x = 42)` | 42 | 9 |
| `MachineRedefinedDefault` | `new Redefined()` | 11 | 9 |
| `MachineSendTimeArgument` | `new Data(y = current + 2)` | 7 | 42 |

In `MachineSendTimeArgument`, `current` starts at `1`, becomes `40` when
`idle` is entered and `100` when `armed` is entered after the send. The
argument is evaluated when the send is performed, so the receiver observes
`y = 42`, not `3` (initial value) or `102` (value at delivery).

`MachineMarker` sends `Marker`, a type with no data fields, as a control for
plain signal delivery.
