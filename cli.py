import argparse
from pathlib import Path

from sim.io import write_csv
from sim.parser import parse_netlist_file
from sim.plot_waveform import load_waveform_csv, plot_waveform, save_figure
from sim.solver import run_transient_be


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="RLC transient simulator (MNA + BE): simulate or plot waveforms"
    )
    sub = p.add_subparsers(dest="command", required=True)

    sim = sub.add_parser("simulate", help="Run netlist and write waveform CSV")
    sim.add_argument("--netlist", required=True, help="Path to netlist file")
    sim.add_argument("--tstop", required=True, type=float, help="Stop time (seconds)")
    sim.add_argument("--dt", required=True, type=float, help="Timestep (seconds)")
    sim.add_argument("--output", default="out/waveforms.csv", help="Output CSV path")
    sim.add_argument(
        "--probes",
        default="",
        help="Comma-separated probe node names; defaults to .probe directive or all nodes",
    )

    plot = sub.add_parser("plot", help="Plot waveform CSV from simulate")
    plot.add_argument("-i", "--input", required=True, help="Path to waveform CSV")
    plot.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output PNG path (default: same stem as CSV with .png)",
    )
    plot.add_argument(
        "--columns",
        default="",
        help="Comma-separated CSV column names to plot (default: all v(*) columns)",
    )
    plot.add_argument("--title", default=None, help="Plot title")
    plot.add_argument(
        "--show",
        action="store_true",
        help="Display the figure with matplotlib (interactive)",
    )

    viewer = sub.add_parser(
        "viewer",
        help="Schematic editor and simulation UI (local web app)",
    )
    viewer.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind address (default: 127.0.0.1)",
    )
    viewer.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port (default: 8765)",
    )

    return p


def cmd_simulate(args: argparse.Namespace) -> None:
    circuit = parse_netlist_file(args.netlist)
    probes = [p.strip() for p in args.probes.split(",") if p.strip()] if args.probes else None
    result = run_transient_be(circuit=circuit, tstop=args.tstop, dt=args.dt, probes=probes)
    write_csv(result, args.output)
    print(f"Wrote waveform CSV: {args.output}")


def cmd_plot(args: argparse.Namespace) -> None:
    import matplotlib.pyplot as plt

    df = load_waveform_csv(args.input)
    cols = [c.strip() for c in args.columns.split(",") if c.strip()] if args.columns else None
    fig = plot_waveform(df, columns=cols, title=args.title)
    out_path = args.output
    if out_path is None:
        out_path = str(Path(args.input).with_suffix(".png"))
    save_figure(fig, out_path)
    print(f"Wrote plot: {out_path}")
    if args.show:
        plt.show()
    plt.close(fig)


def cmd_viewer(args: argparse.Namespace) -> None:
    from sim.schematic_viewer.app import create_app

    app = create_app()
    print(f"Schematic viewer: http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "simulate":
        cmd_simulate(args)
    elif args.command == "plot":
        cmd_plot(args)
    elif args.command == "viewer":
        cmd_viewer(args)
    else:
        parser.error("Choose subcommand: simulate, plot, or viewer")


if __name__ == "__main__":
    main()
