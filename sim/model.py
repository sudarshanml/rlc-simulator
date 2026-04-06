from dataclasses import dataclass, field
from typing import Dict, List, Tuple


GROUND_NAMES = {"0", "gnd", "GND"}


@dataclass(frozen=True)
class Resistor:
    name: str
    n1: str
    n2: str
    value: float


@dataclass(frozen=True)
class Capacitor:
    name: str
    n1: str
    n2: str
    value: float


@dataclass(frozen=True)
class SourceSpec:
    kind: str  # DC, STEP, or PWL
    params: Tuple[float, ...]

    def value_at(self, t: float) -> float:
        if self.kind == "DC":
            return float(self.params[0])
        if self.kind == "STEP":
            v0, v1, t_step = self.params
            return float(v0 if t < t_step else v1)
        if self.kind == "PWL":
            p = self.params
            n = len(p) // 2
            pts = [(p[2 * i], p[2 * i + 1]) for i in range(n)]
            t0, v0 = pts[0]
            if t <= t0:
                return float(v0)
            i = 0
            while i < n - 1:
                ta, va = pts[i]
                tb, vb = pts[i + 1]
                if ta < tb:
                    if t < tb:
                        return float(va + (vb - va) * (t - ta) / (tb - ta))
                    if t == tb:
                        j = i + 1
                        last = vb
                        while j < n and pts[j][0] == tb:
                            last = pts[j][1]
                            j += 1
                        return float(last)
                    i += 1
                else:
                    # ta == tb: vertical step; left approach uses segment ending at (ta, va)
                    if t < ta:
                        if i == 0:
                            return float(va)
                        t_prev, v_prev = pts[i - 1]
                        if t_prev < ta:
                            return float(
                                v_prev + (va - v_prev) * (t - t_prev) / (ta - t_prev)
                            )
                        return float(va)
                    if t == ta:
                        j = i + 1
                        last = vb
                        while j < n and pts[j][0] == ta:
                            last = pts[j][1]
                            j += 1
                        return float(last)
                    i += 1
            return float(pts[-1][1])
        raise ValueError(f"Unsupported source kind: {self.kind}")


@dataclass(frozen=True)
class CurrentSource:
    name: str
    n_plus: str
    n_minus: str
    spec: SourceSpec


@dataclass(frozen=True)
class VoltageSource:
    name: str
    n_plus: str
    n_minus: str
    spec: SourceSpec


@dataclass
class Circuit:
    resistors: List[Resistor] = field(default_factory=list)
    capacitors: List[Capacitor] = field(default_factory=list)
    current_sources: List[CurrentSource] = field(default_factory=list)
    voltage_sources: List[VoltageSource] = field(default_factory=list)
    probes: List[str] = field(default_factory=list)
    initial_conditions: Dict[str, float] = field(default_factory=dict)

    def all_nodes(self) -> List[str]:
        nodes = set()
        for r in self.resistors:
            nodes.update([r.n1, r.n2])
        for c in self.capacitors:
            nodes.update([c.n1, c.n2])
        for i in self.current_sources:
            nodes.update([i.n_plus, i.n_minus])
        for v in self.voltage_sources:
            nodes.update([v.n_plus, v.n_minus])
        nodes.update(self.probes)
        nodes.update(self.initial_conditions.keys())
        return sorted(nodes)


@dataclass(frozen=True)
class NodeMap:
    # Voltage unknown indices for non-ground nodes
    node_to_idx: Dict[str, int]
    idx_to_node: Dict[int, str]

    @property
    def n_voltage(self) -> int:
        return len(self.node_to_idx)

    def get(self, node: str):
        n = normalize_node(node)
        if n == "0":
            return None
        return self.node_to_idx[n]


def normalize_node(node: str) -> str:
    return "0" if node in GROUND_NAMES else node


def build_node_map(circuit: Circuit) -> NodeMap:
    normalized = sorted(
        {normalize_node(n) for n in circuit.all_nodes() if normalize_node(n) != "0"}
    )
    node_to_idx = {n: i for i, n in enumerate(normalized)}
    idx_to_node = {i: n for n, i in node_to_idx.items()}
    return NodeMap(node_to_idx=node_to_idx, idx_to_node=idx_to_node)
