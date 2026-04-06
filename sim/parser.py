from pathlib import Path
from typing import Iterable, List, Tuple

from sim.model import (
    Capacitor,
    Circuit,
    CurrentSource,
    Inductor,
    Resistor,
    SourceSpec,
    VoltageSource,
    normalize_node,
)


def _pwl_times_non_decreasing(pairs: Tuple[float, ...]) -> bool:
    n = len(pairs) // 2
    for i in range(1, n):
        if pairs[2 * i] < pairs[2 * i - 2]:
            return False
    return True


class NetlistParseError(ValueError):
    pass


def _parse_float(tok: str, line_no: int) -> float:
    try:
        return float(tok)
    except ValueError as exc:
        raise NetlistParseError(f"Line {line_no}: invalid number '{tok}'") from exc


def _parse_source_spec(tokens: List[str], line_no: int) -> SourceSpec:
    if not tokens:
        raise NetlistParseError(f"Line {line_no}: missing source specification")
    mode = tokens[0].upper()
    if mode == "DC":
        if len(tokens) != 2:
            raise NetlistParseError(f"Line {line_no}: DC expects one value")
        return SourceSpec(kind="DC", params=(_parse_float(tokens[1], line_no),))
    if mode == "STEP":
        if len(tokens) != 4:
            raise NetlistParseError(f"Line {line_no}: STEP expects v0 v1 t_step")
        return SourceSpec(
            kind="STEP",
            params=(
                _parse_float(tokens[1], line_no),
                _parse_float(tokens[2], line_no),
                _parse_float(tokens[3], line_no),
            ),
        )
    if mode == "PWL":
        rest = tokens[1:]
        if len(rest) < 2 or len(rest) % 2 != 0:
            raise NetlistParseError(
                f"Line {line_no}: PWL expects pairs t1 v1 t2 v2 ..."
            )
        parsed = tuple(_parse_float(x, line_no) for x in rest)
        if not _pwl_times_non_decreasing(parsed):
            raise NetlistParseError(
                f"Line {line_no}: PWL time values must be non-decreasing"
            )
        return SourceSpec(kind="PWL", params=parsed)
    raise NetlistParseError(f"Line {line_no}: unsupported source mode '{mode}'")


def _iter_clean_lines(lines: Iterable[str]):
    for i, raw in enumerate(lines, start=1):
        line = raw.split("#", 1)[0].strip()
        if line:
            yield i, line


def parse_netlist_text(text: str) -> Circuit:
    circuit = Circuit()
    seen_names = set()

    for line_no, line in _iter_clean_lines(text.splitlines()):
        toks = line.split()
        head = toks[0]

        if head.startswith("."):
            directive = head.lower()
            if directive == ".probe":
                if len(toks) < 2:
                    raise NetlistParseError(
                        f"Line {line_no}: .probe expects at least one node"
                    )
                circuit.probes.extend([normalize_node(n) for n in toks[1:]])
            elif directive == ".ic":
                if len(toks) < 3 or len(toks[1:]) % 2 != 0:
                    raise NetlistParseError(
                        f"Line {line_no}: .ic expects pairs: <node> <value> ..."
                    )
                for j in range(1, len(toks), 2):
                    node = normalize_node(toks[j])
                    val = _parse_float(toks[j + 1], line_no)
                    circuit.initial_conditions[node] = val
            else:
                raise NetlistParseError(
                    f"Line {line_no}: unsupported directive '{head}'"
                )
            continue

        name = toks[0]
        if name in seen_names:
            raise NetlistParseError(f"Line {line_no}: duplicate element name '{name}'")
        seen_names.add(name)

        kind = name[0].upper()
        if kind == "R":
            if len(toks) != 4:
                raise NetlistParseError(
                    f"Line {line_no}: resistor format: Rname n1 n2 value"
                )
            n1, n2 = normalize_node(toks[1]), normalize_node(toks[2])
            val = _parse_float(toks[3], line_no)
            if val <= 0:
                raise NetlistParseError(f"Line {line_no}: resistor value must be > 0")
            circuit.resistors.append(Resistor(name=name, n1=n1, n2=n2, value=val))
        elif kind == "C":
            if len(toks) != 4:
                raise NetlistParseError(
                    f"Line {line_no}: capacitor format: Cname n1 n2 value"
                )
            n1, n2 = normalize_node(toks[1]), normalize_node(toks[2])
            val = _parse_float(toks[3], line_no)
            if val < 0:
                raise NetlistParseError(
                    f"Line {line_no}: capacitor value must be >= 0"
                )
            circuit.capacitors.append(Capacitor(name=name, n1=n1, n2=n2, value=val))
        elif kind == "L":
            if len(toks) != 4:
                raise NetlistParseError(
                    f"Line {line_no}: inductor format: Lname n1 n2 value"
                )
            n1, n2 = normalize_node(toks[1]), normalize_node(toks[2])
            val = _parse_float(toks[3], line_no)
            if val <= 0:
                raise NetlistParseError(
                    f"Line {line_no}: inductor value must be > 0"
                )
            circuit.inductors.append(Inductor(name=name, n1=n1, n2=n2, value=val))
        elif kind == "I":
            if len(toks) < 5:
                raise NetlistParseError(
                    f"Line {line_no}: current source format: "
                    "Iname n+ n- (DC v | STEP v0 v1 t | PWL t1 v1 ...)"
                )
            n_plus, n_minus = normalize_node(toks[1]), normalize_node(toks[2])
            spec = _parse_source_spec(toks[3:], line_no)
            circuit.current_sources.append(
                CurrentSource(name=name, n_plus=n_plus, n_minus=n_minus, spec=spec)
            )
        elif kind == "V":
            if len(toks) < 5:
                raise NetlistParseError(
                    f"Line {line_no}: voltage source format: "
                    "Vname n+ n- (DC v | STEP v0 v1 t | PWL t1 v1 ...)"
                )
            n_plus, n_minus = normalize_node(toks[1]), normalize_node(toks[2])
            spec = _parse_source_spec(toks[3:], line_no)
            circuit.voltage_sources.append(
                VoltageSource(name=name, n_plus=n_plus, n_minus=n_minus, spec=spec)
            )
        else:
            raise NetlistParseError(f"Line {line_no}: unsupported element '{name}'")

    return circuit


def parse_netlist_file(path: str | Path) -> Circuit:
    p = Path(path)
    return parse_netlist_text(p.read_text())
