import argparse

from sim.io import write_csv
from sim.parser import parse_netlist_file
from sim.solver import run_transient_be


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Distributed RC transient simulator (MNA + BE)")
    p.add_argument("--netlist", required=True, help="Path to netlist file")
    p.add_argument("--tstop", required=True, type=float, help="Stop time (seconds)")
    p.add_argument("--dt", required=True, type=float, help="Timestep (seconds)")
    p.add_argument("--output", default="out/waveforms.csv", help="Output CSV path")
    p.add_argument(
        "--probes",
        default="",
        help="Comma-separated probe node names; defaults to .probe directive or all nodes",
    )
    return p


def main() -> None:
    args = build_arg_parser().parse_args()
    circuit = parse_netlist_file(args.netlist)
    probes = [p.strip() for p in args.probes.split(",") if p.strip()] if args.probes else None
    result = run_transient_be(circuit=circuit, tstop=args.tstop, dt=args.dt, probes=probes)
    write_csv(result, args.output)
    print(f"Wrote waveform CSV: {args.output}")


if __name__ == "__main__":
    main()
