# rc-simualtor

A correctness-first RC transient simulator using Modified Nodal Analysis (MNA) and Backward Euler (BE).

## Features

- Line-based RC netlist parser
- Deterministic node indexing (`0`/`gnd` as ground)
- MNA matrix stamping for `G`, `C`, and source vector `b(t)`
- Backward Euler transient solve
- CSV waveform export
- Unit tests for parser and transient behavior

## Netlist format

- `Rname n1 n2 value` resistor in Ohms
- `Cname n1 n2 value` capacitor in Farads
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

```bash
python cli.py --netlist examples/rc_step.cir --tstop 0.005 --dt 1e-5 --output out/waveforms.csv
```

## Test

```bash
python -m unittest discover -s tests -v
```
