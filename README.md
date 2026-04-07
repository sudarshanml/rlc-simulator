# rlc-simulator

A correctness-first RLC transient simulator using Modified Nodal Analysis (MNA) and Backward Euler (BE).

## Features

- Line-based RLC netlist parser
- Deterministic node indexing (`0`/`gnd` as ground)
- MNA matrix stamping for `G`, `C`, and source vector `b(t)`
- Backward Euler transient solve (optional **DC operating point** for initial `x`, with `.ic` overriding node voltages)
- CSV waveform export
- Matplotlib PNG plots from waveform CSV
- Interactive `simulate()` / `plot_waveforms()` API
- Browser **schematic viewer** (draw nodes/branches, set probes, run transient, export netlist)
- Unit tests for parser and transient behavior

## Netlist format

- `Rname n1 n2 value` resistor in Ohms
- `Cname n1 n2 value` capacitor in Farads
- `Lname n1 n2 value` inductor in Henries
- `Iname n+ n- DC value` current source
- `Iname n+ n- STEP v0 v1 t_step` current source step
- `Vname n+ n- DC value` voltage source
- `Vname n+ n- STEP v0 v1 t_step` voltage source step
- `.probe node1 node2 ...` output probes
- `.ic node value [node value ...]` initial conditions

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

**Schematic viewer** (local web UI):

```bash
python -m sim.schematic_viewer
# or: python cli.py viewer
```

Then open http://127.0.0.1:8765 — use the toolbar to add nodes and `R` / `C` / `L` / `V` / `I`, connect two nodes per branch, set **GND** on the ground node, edit net names so branches share nets as needed, and click **Run**.

Simulate and write CSV:

```bash
python cli.py simulate --netlist examples/rc_step.cir --tstop 0.005 --dt 1e-5 --output out/waveforms.csv
```

Plot waveforms (default PNG path: same stem as CSV):

```bash
python cli.py plot --input out/waveforms.csv --output out/waveforms.png
```

Optional: `--columns "v(out)"`, `--title "Title"`, `--show` for an interactive window.

## Python API (interactive)

```python
from sim import simulate, plot_waveforms

waveforms = simulate("examples/test.sp", duration=200e-12, timestep=1e-12)
fig = plot_waveforms(waveforms, title="RLC transient")
```

`waveforms` maps probe **node name** (e.g. `"out"`) → `Waveform` with `.times`, `.values`, and `.pairs` as `list[(t, v), ...]`.

Optional probes: `simulate(..., probes=["out"])`.

## Test

```bash
python -m unittest discover -s tests -v
```

## Demo video

A short MP4 tour of the CLI (using `examples/test2.sp`) and the web viewer is in **`demo/rlc_simulator_demo.mp4`**. To rebuild it after edits, see **`demo/README.md`**.
