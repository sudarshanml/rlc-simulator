"""Load simulator CSV output and plot waveforms with matplotlib."""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

import matplotlib.pyplot as plt
import pandas as pd

# Match run.py: local matplotlib config for restricted environments
os.environ.setdefault(
    "MPLCONFIGDIR", os.path.join(os.path.dirname(__file__), "..", ".matplotlib")
)


def load_waveform_csv(path: str | Path) -> pd.DataFrame:
    """Load waveform CSV produced by sim.io.write_csv (columns: time, v(node), ...)."""
    return pd.read_csv(path)


def default_voltage_columns(df: pd.DataFrame) -> List[str]:
    """Columns to plot: prefer v(*) names; else any numeric column except time."""
    if "time" not in df.columns:
        raise ValueError("CSV must have a 'time' column")
    cols = [c for c in df.columns if c != "time" and str(c).startswith("v(")]
    if not cols:
        cols = [
            c
            for c in df.columns
            if c != "time" and pd.api.types.is_numeric_dtype(df[c])
        ]
    if not cols:
        raise ValueError("No voltage columns found to plot")
    return cols


def plot_waveform(
    df: pd.DataFrame,
    *,
    columns: Optional[List[str]] = None,
    title: Optional[str] = None,
) -> plt.Figure:
    """Plot selected columns vs time."""
    if "time" not in df.columns:
        raise ValueError("CSV must have a 'time' column")
    t = df["time"].to_numpy()
    cols = columns if columns is not None else default_voltage_columns(df)
    for c in cols:
        if c not in df.columns:
            raise ValueError(f"Column not in CSV: {c}")
    fig, ax = plt.subplots(figsize=(10, 5))
    for c in cols:
        ax.plot(t, df[c], label=c, linewidth=1.2)
    ax.set_xlabel("time (s)")
    ax.set_ylabel("voltage (V)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    if title:
        ax.set_title(title)
    fig.tight_layout()
    return fig


def save_figure(fig: plt.Figure, path: str | Path, dpi: int = 150) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=dpi, bbox_inches="tight")
