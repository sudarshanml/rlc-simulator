from dataclasses import dataclass
from typing import Callable, List, Optional

import numpy as np
import warnings

from sim.model import Circuit, Inductor, NodeMap, build_node_map


@dataclass(frozen=True)
class MatrixSystem:
    node_map: NodeMap
    vsrc_names: List[str]
    G: np.ndarray
    C: np.ndarray
    source_fn: Callable[[float], np.ndarray]

    @property
    def size(self) -> int:
        return self.G.shape[0]


class StampError(ValueError):
    pass


def _stamp_conductance(M: np.ndarray, a: Optional[int], b: Optional[int], g: float) -> None:
    if a is not None:
        M[a, a] += g
    if b is not None:
        M[b, b] += g
    if a is not None and b is not None:
        M[a, b] -= g
        M[b, a] -= g


def _has_dc_path_to_ground(circuit: Circuit, node_map: NodeMap) -> bool:
    # Simple guard: every node should touch at least one resistor or voltage source path.
    connected = {n: False for n in node_map.node_to_idx.keys()}
    for r in circuit.resistors:
        if r.n1 != "0":
            connected[r.n1] = True
        if r.n2 != "0":
            connected[r.n2] = True
    for v in circuit.voltage_sources:
        if v.n_plus != "0":
            connected[v.n_plus] = True
        if v.n_minus != "0":
            connected[v.n_minus] = True
    for ind in circuit.inductors:
        if ind.n1 != "0":
            connected[ind.n1] = True
        if ind.n2 != "0":
            connected[ind.n2] = True
    return all(connected.values()) if connected else True


def _stamp_vtype_branch(
    G: np.ndarray,
    C: np.ndarray,
    node_map: NodeMap,
    row: int,
    n_plus: str,
    n_minus: str,
    ind: Optional[Inductor],
) -> None:
    """
    Stamp MNA for a branch with auxiliary current.

    KCL: current leaves n+ and enters n- (same as voltage source).
    KVL row: v_plus - v_minus = ... for a voltage source;
    for an inductor, L di/dt = v_plus - v_minus  =>  -v_plus + v_minus + L di/dt = 0.
    """
    a = node_map.get(n_plus)
    b = node_map.get(n_minus)
    row_va = -1.0 if ind is not None else 1.0
    row_vb = 1.0 if ind is not None else -1.0
    if a is not None:
        G[a, row] += 1.0
        G[row, a] += row_va
    if b is not None:
        G[b, row] -= 1.0
        G[row, b] += row_vb
    if ind is not None:
        C[row, row] += ind.value


def build_mna_system(circuit: Circuit) -> MatrixSystem:
    node_map = build_node_map(circuit)
    n = node_map.n_voltage
    m = len(circuit.voltage_sources)
    m_l = len(circuit.inductors)
    size = n + m + m_l

    if size == 0:
        raise StampError("Circuit has no unknowns")

    G = np.zeros((size, size), dtype=float)
    C = np.zeros((size, size), dtype=float)

    # Resistors -> G
    for r in circuit.resistors:
        if r.value < 1e-9:
            warnings.warn(
                f"Very small resistor {r.name}={r.value} Ohm may cause stiff/singular systems",
                RuntimeWarning,
            )
        a = node_map.get(r.n1)
        b = node_map.get(r.n2)
        _stamp_conductance(G, a, b, 1.0 / r.value)

    # Capacitors -> C
    for c in circuit.capacitors:
        if c.value > 1e-1:
            warnings.warn(
                f"Large capacitor {c.name}={c.value} F detected; check units (F expected)",
                RuntimeWarning,
            )
        a = node_map.get(c.n1)
        b = node_map.get(c.n2)
        _stamp_conductance(C, a, b, c.value)

    # Voltage sources -> MNA B and B^T in G (algebraic KVL row)
    vsrc_names = []
    for k, v in enumerate(circuit.voltage_sources):
        row = n + k
        vsrc_names.append(v.name)
        _stamp_vtype_branch(G, C, node_map, row, v.n_plus, v.n_minus, None)

    # Inductors -> same KCL coupling as V; dynamic term L di/dt in C[row,row]
    for k, ind in enumerate(circuit.inductors):
        if ind.value > 1.0:
            warnings.warn(
                f"Large inductor {ind.name}={ind.value} H detected; check units (H expected)",
                RuntimeWarning,
            )
        row = n + m + k
        _stamp_vtype_branch(G, C, node_map, row, ind.n1, ind.n2, ind)

    if not _has_dc_path_to_ground(circuit, node_map):
        raise StampError(
            "Potential floating node detected: ensure each non-ground node has a DC path"
        )

    # Build source vector function b(t)
    def source_fn(t: float) -> np.ndarray:
        bvec = np.zeros(size, dtype=float)
        # Current source from n+ to n- means draw from n+, inject into n-
        for src in circuit.current_sources:
            i_val = src.spec.value_at(t)
            p = node_map.get(src.n_plus)
            n_ = node_map.get(src.n_minus)
            if p is not None:
                bvec[p] -= i_val
            if n_ is not None:
                bvec[n_] += i_val

        # Voltage source equations rhs
        for k, src in enumerate(circuit.voltage_sources):
            bvec[n + k] = src.spec.value_at(t)

        return bvec

    return MatrixSystem(node_map=node_map, vsrc_names=vsrc_names, G=G, C=C, source_fn=source_fn)
