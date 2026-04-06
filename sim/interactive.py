"""Interactive Python API: Waveform containers, simulate(), plot_waveforms()."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt

from sim.parser import parse_netlist_file
from sim.solver import run_transient_be

os.environ.setdefault(
    "MPLCONFIGDIR", os.path.join(os.path.dirname(__file__), "..", ".matplotlib")
)


@dataclass
class Waveform:
    """Aligned time series: probe node voltage vs simulation time."""

    times: List[float]
    values: List[float]

    @property
    def pairs(self) -> List[Tuple[float, float]]:
        return list(zip(self.times, self.values))


def simulate(
    netlist: str | Path,
    duration: float,
    timestep: float,
    *,
    probes: List[str] | None = None,
) -> Dict[str, Waveform]:
    """
    Run transient simulation and return probe node name -> Waveform.

    Keys match .probe nodes (e.g. "out"), not CSV column names like "v(out)".
    """
    circuit = parse_netlist_file(netlist)
    result = run_transient_be(circuit, tstop=duration, dt=timestep, probes=probes)
    t_list = result.times.tolist()
    return {
        name: Waveform(times=t_list, values=arr.tolist())
        for name, arr in result.probes.items()
    }


def plot_waveforms(
    waveforms: Dict[str, Waveform],
    *,
    title: str | None = None,
    figsize: Tuple[float, float] = (10, 5),
) -> plt.Figure:
    """Plot all waveforms on one axes; legend labels are dict keys."""
    fig, ax = plt.subplots(figsize=figsize)
    for label, w in waveforms.items():
        ax.plot(w.times, w.values, label=label, linewidth=1.2)
    ax.set_xlabel("time (s)")
    ax.set_ylabel("voltage (V)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    if title:
        ax.set_title(title)
    fig.tight_layout()
    fig.show()
    return fig
