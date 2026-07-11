"""Runner for exp000 — Monte Carlo estimate of pi.

Throw N random points at the unit square, count how many land inside the quarter
circle of radius 1, and estimate pi = 4 * inside / N. Computed inline here (no tool):
this is one self-contained experiment, not a model reused across several (RULES §4).
Figures are rendered here from the sampled points and staged into
artifacts/data/exp000/ alongside numbers.json.
"""
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from helpers import provenance  # inline runner: stamp() records which code produced the run
from helpers import style as _style  # shared figure style (HOUSESTYLE H10-H16)

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data" / "exp000"

# Every parameter of the experiment lives here — the one place to vary the run.
CONFIG = {
    "n": 100_000,   # number of random points thrown at the unit square
    "seed": 0,      # RNG seed, so the estimate is reproducible bit-for-bit
}

# How many points to draw in the scatter figure — a readable subsample of the full run.
SCATTER_POINTS = 2_000


def sample(n: int, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Draw n points uniformly in the unit square; return their x, y, and an
    inside-the-quarter-circle mask (x^2 + y^2 <= 1)."""
    rng = np.random.default_rng(seed)
    xy = rng.random((n, 2))
    x, y = xy[:, 0], xy[:, 1]
    inside = (x * x + y * y) <= 1.0
    return x, y, inside


def plot_scatter(x: np.ndarray, y: np.ndarray, inside: np.ndarray, dst: Path) -> None:
    # Points inside the quarter circle (INK) vs outside (BAND grey), with the arc in
    # ACCENT — two categories sharing one axis, exactly the case H13 allows colour for.
    k = min(SCATTER_POINTS, len(x))
    xs, ys, ins = x[:k], y[:k], inside[:k]
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    ax.scatter(xs[~ins], ys[~ins], s=4, color=_style.BAND, label="outside")
    ax.scatter(xs[ins], ys[ins], s=4, color=_style.INK, label="inside")
    theta = np.linspace(0, math.pi / 2, 200)
    ax.plot(np.cos(theta), np.sin(theta), color=_style.ACCENT, linewidth=2)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_aspect("equal")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(loc="upper right", markerscale=2)
    fig.savefig(dst)
    plt.close(fig)


def plot_convergence(inside: np.ndarray, dst: Path) -> None:
    # Running estimate as points accumulate: it wanders, then settles toward pi
    # (ACCENT reference line). Line plot -> SVG (H10).
    n = np.arange(1, len(inside) + 1)
    running = 4.0 * np.cumsum(inside) / n
    fig, ax = plt.subplots()
    ax.plot(n, running, color=_style.INK)
    ax.axhline(math.pi, color=_style.ACCENT, linestyle="--", linewidth=1.2)
    ax.set_xscale("log")
    ax.set_xlabel("Number of points")
    ax.set_ylabel("Estimate of π")
    ax.set_ylim(2.6, 3.6)
    fig.savefig(dst)
    plt.close(fig)


def collect_numbers(inside_count: int, n: int, estimate: float) -> dict:
    return {
        "pi": {
            "config": provenance.stamp(CONFIG),
            "pi_estimate": estimate,
            "true_pi": math.pi,
            "absolute_error": abs(estimate - math.pi),
            "inside_count": inside_count,
        }
    }


def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    x, y, inside = sample(CONFIG["n"], CONFIG["seed"])
    inside_count = int(inside.sum())
    estimate = 4.0 * inside_count / CONFIG["n"]

    plot_scatter(x, y, inside, ARTIFACTS / "scatter.png")
    plot_convergence(inside, ARTIFACTS / "convergence.svg")
    print(f"rendered scatter.png, convergence.svg -> {ARTIFACTS}")

    numbers_path = ARTIFACTS / "numbers.json"
    numbers_path.write_text(
        json.dumps(collect_numbers(inside_count, CONFIG["n"], estimate), indent=2) + "\n"
    )
    print(f"wrote {numbers_path}  (pi ~ {estimate:.5f})")

    provenance.write_run_sh(ARTIFACTS)


if __name__ == "__main__":
    main()
