"""Tests for the mujoco tool's physics. The sim currently lives inside the
render-coupled command handlers, so these step the MJCF models directly (no
Renderer, headless-safe) to check the dynamics the tool relies on."""

import mujoco
import numpy as np

from core.mujoco.tool import CARTPOLE_XML, DOUBLE_PENDULUM_XML


def _step(xml, setup, n):
    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)
    setup(data)
    for _ in range(n):
        mujoco.mj_step(model, data)
    return data


def test_cartpole_pole_falls():
    data = _step(CARTPOLE_XML, lambda d: d.qpos.__setitem__(1, 0.15), 2000)
    assert abs(data.qpos[1]) > np.pi / 3  # fallen past the 60° threshold


def test_cartpole_is_deterministic():
    a = _step(CARTPOLE_XML, lambda d: d.qpos.__setitem__(1, 0.15), 500).qpos[1]
    b = _step(CARTPOLE_XML, lambda d: d.qpos.__setitem__(1, 0.15), 500).qpos[1]
    assert a == b


def test_double_pendulum_diverges_from_tiny_offset():
    def setup(d):
        d.qpos[0], d.qpos[1] = 2.0, 2.0            # pendulum A
        d.qpos[2], d.qpos[3] = 2.0 + 1e-3, 2.0     # pendulum B, 1e-3 offset

    data = _step(DOUBLE_PENDULUM_XML, setup, 3000)
    separation = abs(data.qpos[0] - data.qpos[2]) + abs(data.qpos[1] - data.qpos[3])
    assert separation > 0.1  # chaotic divergence from a near-identical start
