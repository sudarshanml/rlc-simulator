#!/usr/bin/env python3
"""
Build demo/rlc_simulator_demo.mp4: CLI + web walkthrough using examples/test2.sp.

Requires: pip install -r demo/requirements-demo.txt

Usage (from repo root):
  python demo/generate_demo_video.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "out"
NETLIST = REPO / "examples" / "test2.sp"
CSV_PATH = OUT_DIR / "demo_test2.csv"
PNG_PATH = OUT_DIR / "demo_test2_plot.png"
VIDEO_PATH = REPO / "demo" / "rlc_simulator_demo.mp4"

W, H = 1280, 720
DPI = 100


def _run(cmd: list[str]) -> tuple[str, str, int]:
    p = subprocess.run(
        cmd,
        cwd=str(REPO),
        capture_output=True,
        text=True,
        env={**os.environ, "MPLCONFIGDIR": str(REPO / ".matplotlib")},
    )
    return p.stdout, p.stderr, p.returncode


def _fig_to_rgb(fig) -> np.ndarray:
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())
    return np.ascontiguousarray(buf[:, :, :3])


def _slide_title(ax, title: str, subtitle: str | None = None) -> None:
    ax.set_facecolor("#0f1419")
    ax.axis("off")
    ax.text(
        0.5,
        0.58,
        title,
        transform=ax.transAxes,
        fontsize=28,
        fontweight="bold",
        ha="center",
        va="center",
        color="#e8eef5",
    )
    if subtitle:
        ax.text(
            0.5,
            0.38,
            subtitle,
            transform=ax.transAxes,
            fontsize=16,
            ha="center",
            va="center",
            color="#8b9cb3",
            wrap=True,
        )


def _slide_code(ax, heading: str, body: str) -> None:
    ax.set_facecolor("#0f1419")
    ax.axis("off")
    ax.text(
        0.05,
        0.92,
        heading,
        transform=ax.transAxes,
        fontsize=20,
        fontweight="bold",
        color="#5b9cf5",
    )
    ax.text(
        0.05,
        0.12,
        body,
        transform=ax.transAxes,
        fontsize=14,
        va="bottom",
        ha="left",
        color="#e8eef5",
        family="monospace",
    )


def main() -> int:
    try:
        import imageio.v3 as iio
    except ImportError:
        print("Install: pip install -r demo/requirements-demo.txt", file=sys.stderr)
        return 1

    os.environ.setdefault("MPLCONFIGDIR", str(REPO / ".matplotlib"))
    (REPO / ".matplotlib").mkdir(parents=True, exist_ok=True)

    import matplotlib.pyplot as plt

    if not NETLIST.is_file():
        print(f"Missing netlist: {NETLIST}", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    vpy = sys.executable
    sim_cmd = [
        vpy,
        str(REPO / "cli.py"),
        "simulate",
        "--netlist",
        str(NETLIST),
        "--tstop",
        "2e-10",
        "--dt",
        "2e-12",
        "--output",
        str(CSV_PATH),
    ]
    sim_out, sim_err, sim_rc = _run(sim_cmd)
    plot_cmd = [
        vpy,
        str(REPO / "cli.py"),
        "plot",
        "-i",
        str(CSV_PATH),
        "-o",
        str(PNG_PATH),
    ]
    plot_out, plot_err, plot_rc = _run(plot_cmd)

    netlist_text = NETLIST.read_text().strip()
    csv_head = ""
    if CSV_PATH.is_file():
        lines = CSV_PATH.read_text().splitlines()[:8]
        csv_head = "\n".join(lines)

    frames: list[np.ndarray] = []
    plt.ioff()

    def add_frame(fig) -> None:
        frames.append(_fig_to_rgb(fig))
        plt.close(fig)

    # 1 — Title
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
    ax = fig.add_subplot(111)
    _slide_title(
        ax,
        "RLC simulator demo",
        "Command line + web schematic viewer · example: examples/test2.sp",
    )
    add_frame(fig)

    # 2 — Netlist
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
    ax = fig.add_subplot(111)
    _slide_code(ax, "Example netlist (examples/test2.sp)", netlist_text)
    add_frame(fig)

    # 3 — Simulate command
    body = (
        "$ cd rlc-simulator\n"
        "$ source venv/bin/activate   # or: python3 -m venv venv\n\n"
        "$ python cli.py simulate \\\n"
        "    --netlist examples/test2.sp \\\n"
        "    --tstop 2e-10 --dt 2e-12 \\\n"
        "    --output out/demo_test2.csv\n\n"
        f"--- exit {sim_rc} ---\n"
        + (sim_out or sim_err)
    )
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
    ax = fig.add_subplot(111)
    _slide_code(ax, "Part A — CLI transient (picosecond-scale PWL)", body[:3500])
    add_frame(fig)

    # 4 — CSV preview
    body = "First rows of out/demo_test2.csv:\n\n" + (csv_head or "(no csv)")
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
    ax = fig.add_subplot(111)
    _slide_code(ax, "Waveform CSV", body)
    add_frame(fig)

    # 5 — Plot command
    body = (
        "$ python cli.py plot \\\n"
        "    -i out/demo_test2.csv \\\n"
        "    -o out/demo_test2_plot.png\n\n"
        f"--- exit {plot_rc} ---\n"
        + (plot_out or plot_err)
    )
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
    ax = fig.add_subplot(111)
    _slide_code(ax, "CLI — PNG plot", body[:3500])
    add_frame(fig)

    # 6 — Plot image
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
    fig.patch.set_facecolor("#0f1419")
    ax = fig.add_subplot(111)
    ax.set_facecolor("#0f1419")
    ax.axis("off")
    ax.set_title("v(out) from test2.sp", color="#e8eef5", fontsize=18, pad=12)
    if PNG_PATH.is_file():
        img = plt.imread(PNG_PATH)
        ax.imshow(img)
    else:
        ax.text(0.5, 0.5, "(plot PNG missing)", ha="center", va="center", color="#8b9cb3")
    add_frame(fig)

    # 7 — Web server
    body = (
        "$ python -m sim.schematic_viewer\n"
        "# or:  python cli.py viewer\n\n"
        "Open in browser:\n"
        "  http://127.0.0.1:8765\n"
    )
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
    ax = fig.add_subplot(111)
    _slide_code(ax, "Part B — Web schematic viewer", body)
    add_frame(fig)

    # 8 — Web usage (test2.sp is netlist-only; web is graphical)
    body = (
        "The browser UI is for drawing circuits on the canvas.\n\n"
        "For examples/test2.sp (netlist file):\n"
        "  • Use the CLI flow shown earlier (simulate + plot).\n\n"
        "In the web app you can:\n"
        "  1. Add nodes (+ Node) and set GND on the ground net.\n"
        "  2. Place R / C / L / V / I between two nodes (tool, then click twice).\n"
        "  3. Match nets to test2: in, out, n4, n5, and 0.\n"
        "  4. Set Probes (e.g. out), tstop ≈ 2e-10 s, dt ≈ 2e-12 s, click Run.\n"
        "  5. Export netlist to compare with the file.\n"
    )
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
    ax = fig.add_subplot(111)
    _slide_code(ax, "Web UI — workflow", body)
    add_frame(fig)

    # 9 — Closing
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
    ax = fig.add_subplot(111)
    _slide_title(
        ax,
        "Done",
        f"Video written to demo/rlc_simulator_demo.mp4\nRepo: rlc-simulator",
    )
    add_frame(fig)

    VIDEO_PATH.parent.mkdir(parents=True, exist_ok=True)
    # ~2.5 s per frame @ fps=0.4
    iio.imwrite(
        VIDEO_PATH,
        np.stack(frames, axis=0),
        fps=0.4,
        codec="libx264",
        ffmpeg_log_level="error",
    )
    print(f"Wrote {VIDEO_PATH} ({len(frames)} frames)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
