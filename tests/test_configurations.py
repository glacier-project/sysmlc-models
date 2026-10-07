from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sysmlc_models.catalog import model_file, model_path

if TYPE_CHECKING:
    from sysmlc_models.validation import Scalar

pytestmark = pytest.mark.compiler


@pytest.mark.parametrize(
    ("name", "qn", "expected"),
    [
        (
            "thermostat",
            "Thermostat::ThermostatBehavior",
            {
                "setpoint": 23.0,
                "hysteresis": 1.0,
                "temperature": 25.5,
            },
        ),
        (
            "milling-workcell",
            "MillingWorkcell::MillingWorkcellBehavior",
            {
                "batchSize": 2,
                "toolWearLimit": 30.0,
                "retryDelay": 1.0,
            },
        ),
        (
            "batch-reactor",
            "BatchReactor::BatchReactorBehavior",
            {
                "batchTarget": 1,
                "inflowRate": 60.0,
                "heatRate": 65.0,
                "coolRate": 60.0,
                "drainRate": 60.0,
                "sampleTime": 0.5,
            },
        ),
        (
            "charging-station",
            "ChargingStation::ChargingStationBehavior",
            {
                "tempLimit": 45.0,
                "coolThreshold": 40.0,
                "authTimeout": 1.5,
            },
        ),
        (
            "level-crossing",
            "LevelCrossing::LevelCrossingBehavior",
            {"maxFaults": 5},
        ),
    ],
)
def test_shipped_configuration_binds_its_documented_values(
    name: str,
    qn: str,
    expected: dict[str, Scalar],
) -> None:
    import syside

    # Verify values on the neutral facts, before any target renders them.
    from sysmlc.semantics.statemachine.attributes import (
        bind_value,
        scope_attributes,
    )
    from sysmlc.sysml.loading import load_model
    from sysmlc.sysml.queries import resolve
    from sysmlc.values import configure_model, load_values, select_values

    path = f"showcase/{name}"
    model = load_model(model_path(path))
    overrides = select_values(
        load_values(model_file(f"{path}/values.yaml")), qn
    )
    assert set(overrides) == set(expected)
    configured = configure_model(model, qn, overrides)
    machine = resolve(configured, syside.StateDefinition, qn)
    compiler = syside.Compiler()
    stdlib = syside.Stdlib(configured.index)
    actual = {}
    for attr in scope_attributes(machine):
        if attr.name in expected:
            value = bind_value(attr, compiler, stdlib)
            actual[attr.name] = (
                compiler.evaluate(value, stdlib=stdlib)[0]
                if isinstance(value, syside.Expression)
                else value
            )
    assert actual == expected
