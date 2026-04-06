"""Serialize a Circuit to netlist text (round-trip friendly with parse_netlist_text)."""

from sim.model import (
    Circuit,
    CurrentSource,
    SourceSpec,
    VoltageSource,
)


def _fmt_float(x: float) -> str:
    return f"{x:.10g}".rstrip("0").rstrip(".") if "." in f"{x:.10g}" else f"{x:.10g}"


def _source_tokens(spec: SourceSpec) -> str:
    if spec.kind == "DC":
        return f"DC {_fmt_float(float(spec.params[0]))}"
    if spec.kind == "STEP":
        v0, v1, ts = spec.params
        return f"STEP {_fmt_float(float(v0))} {_fmt_float(float(v1))} {_fmt_float(float(ts))}"
    if spec.kind == "PWL":
        parts = " ".join(_fmt_float(float(x)) for x in spec.params)
        return f"PWL {parts}"
    raise ValueError(f"Unsupported source kind {spec.kind}")


def circuit_to_netlist_text(circuit: Circuit) -> str:
    lines: list[str] = []
    for r in circuit.resistors:
        lines.append(f"{r.name} {r.n1} {r.n2} {_fmt_float(r.value)}")
    for c in circuit.capacitors:
        lines.append(f"{c.name} {c.n1} {c.n2} {_fmt_float(c.value)}")
    for ind in circuit.inductors:
        lines.append(f"{ind.name} {ind.n1} {ind.n2} {_fmt_float(ind.value)}")
    for i in circuit.current_sources:
        lines.append(
            f"{i.name} {i.n_plus} {i.n_minus} {_source_tokens(i.spec)}"
        )
    for v in circuit.voltage_sources:
        lines.append(
            f"{v.name} {v.n_plus} {v.n_minus} {_source_tokens(v.spec)}"
        )
    if circuit.initial_conditions:
        ic = []
        for node in sorted(circuit.initial_conditions.keys()):
            ic.extend([node, _fmt_float(circuit.initial_conditions[node])])
        lines.append(".ic " + " ".join(ic))
    if circuit.probes:
        lines.append(".probe " + " ".join(circuit.probes))
    return "\n".join(lines) + ("\n" if lines else "")
