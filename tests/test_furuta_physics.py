from __future__ import annotations

import importlib.util
import math
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest

from sysmlc_models.catalog import model_file, model_path

if TYPE_CHECKING:
    from pathlib import Path
    from types import ModuleType


@dataclass(frozen=True)
class PendulumState:
    theta: float
    d_theta: float
    phi: float
    d_phi: float


@dataclass(frozen=True)
class AngleReading:
    theta: float
    d_theta: float
    phi: float
    d_phi: float


@pytest.fixture(
    scope="session",
    params=["external", pytest.param("inline", marks=pytest.mark.compiler)],
)
def physics_module(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
) -> ModuleType:
    if request.param == "external":
        path = model_file("showcase/furuta-pendulum/furuta_physics.py")
    else:
        from sysmlc.sysml.foreign_artifact.text_rep import (
            extract_text_rep,
            write_file,
        )
        from sysmlc.sysml.loading import load_model

        model = load_model(
            model_path("showcase/furuta-pendulum/nondeterministic")
        )
        result = extract_text_rep(
            model, "furuta::physics", module_name="furuta_physics_inline"
        )
        assert result is not None
        stem, lines = result
        path = write_file(lines, tmp_path_factory.mktemp("furuta_inline"), stem)
    return _load_module(path, f"_validated_furuta_{request.param}")


def _load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_step_is_deterministic_and_pure(physics_module: ModuleType) -> None:
    state = PendulumState(0.1, 0.02, 0.5, -0.01)
    first = physics_module.step(state, 0.3, 0.005)
    second = physics_module.step(state, 0.3, 0.005)
    assert first == second
    assert state == PendulumState(0.1, 0.02, 0.5, -0.01)
    assert first is not state
    assert isinstance(first, PendulumState)


def test_stabilizer_holds_inverted_equilibrium(
    physics_module: ModuleType,
) -> None:
    state = PendulumState(0.05, 0.0, 0.0, 0.0)
    max_theta = 0.0
    for _ in range(2000):
        reading = AngleReading(
            state.theta, state.d_theta, state.phi, state.d_phi
        )
        torque = physics_module.stabilize_torque(reading)
        state = physics_module.step(state, torque, 0.005)
        max_theta = max(max_theta, abs(state.theta))
    assert max_theta < 0.3
    assert abs(physics_module.restrict_angle(state.theta)) < 0.05


def test_swingup_adds_energy(physics_module: ModuleType) -> None:
    state = PendulumState(math.pi, 0.0, 0.0, 0.0)
    for _ in range(500):
        reading = AngleReading(
            state.theta, state.d_theta, state.phi, state.d_phi
        )
        torque = physics_module.swingup_torque(reading)
        state = physics_module.step(state, torque, 0.005)
    assert abs(physics_module.restrict_angle(state.theta)) < math.pi - 0.05
    assert abs(state.d_theta) > 0.01


@pytest.mark.parametrize(
    "theta,expected",
    [
        (0.0, 0.0),
        (math.pi, -math.pi),
        (-math.pi, math.pi),
        (2 * math.pi, 0.0),
        (3 * math.pi / 2, -math.pi / 2),
        (-3 * math.pi / 2, math.pi / 2),
    ],
)
def test_restrict_angle(
    physics_module: ModuleType, theta: float, expected: float
) -> None:
    assert physics_module.restrict_angle(theta) == pytest.approx(
        expected, abs=1e-9
    )
