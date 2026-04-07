# Demo video

**`rlc_simulator_demo.mp4`** walks through:

1. **CLI** — `examples/test2.sp`: `cli.py simulate` (with `tstop=2e-10`, `dt=2e-12` to match the picosecond PWL), CSV preview, then `cli.py plot` and the resulting PNG.
2. **Web** — starting `python -m sim.schematic_viewer` / `cli.py viewer` and how the schematic UI relates to the same netlist (drawn in the browser; the file itself is run from the CLI).

## Regenerate

From the repository root:

```bash
pip install -r demo/requirements-demo.txt
python demo/generate_demo_video.py
```

Output is written to `demo/rlc_simulator_demo.mp4` (overwrites).
