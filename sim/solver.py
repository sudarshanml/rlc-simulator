from dataclasses import dataclass
from typing import Dict, List

import numpy as np
from scipy.sparse import csc_matrix
from scipy.sparse.linalg import SuperLU, splu

from sim.model import Circuit
from sim.stamp import MatrixSystem, build_mna_system


class SolveError(RuntimeError):
    pass

# Sources evaluated at this time for DC OP pick the “initial” level for STEP/PWL
# (e.g. STEP 0 1 0 uses v0 because t_step is not crossed yet).
DEFAULT_DC_OP_TIME = -1e-12


def solve_dc_operating_point(system: MatrixSystem, t: float = DEFAULT_DC_OP_TIME) -> np.ndarray:
    """
    Solve G @ x = b(t) for the DC (static) operating point.

    Capacitors are open (not in G); inductors are shorts (algebraic KVL in G).
    Sources use value_at(t). Default ``t`` is slightly negative so STEP/PWL use
    their value before the first breakpoint (see ``DEFAULT_DC_OP_TIME``).
    """
    b = system.source_fn(t)
    try:
        lu = splu(csc_matrix(system.G, dtype=np.float64))
        x = lu.solve(b)
    except (RuntimeError, ValueError, np.linalg.LinAlgError) as exc:
        raise SolveError(
            "DC analysis failed (singular G? floating nodes or inconsistent sources)"
        ) from exc
    return x


@dataclass(frozen=True)
class SimulationResult:
    times: np.ndarray
    node_names: List[str]
    voltages: np.ndarray  # shape (n_steps+1, n_nodes)
    probes: Dict[str, np.ndarray]


def _factorize_superlu(A: np.ndarray) -> SuperLU:
    try:
        return splu(csc_matrix(A, dtype=np.float64))
    except (RuntimeError, ValueError, np.linalg.LinAlgError) as exc:
        raise SolveError("System matrix is singular; check grounding and source setup") from exc


def run_transient_be(
    circuit: Circuit,
    tstop: float,
    dt: float,
    probes: List[str] | None = None,
    *,
    dc_initial: bool = True,
    dc_time: float = DEFAULT_DC_OP_TIME,
) -> SimulationResult:
    """
    Transient with Backward Euler.

    If ``dc_initial`` is True (default), the initial state is the DC operating
    point (solve ``G x = b(dc_time)``). Default ``dc_time`` is just before
    ``t=0`` so ``STEP``/``PWL`` sources use their pre-transition value; pass
    ``dc_time=0`` if you need OP at the breakpoint. Capacitors are open in
    ``G``; inductors are shorts. ``.ic`` still overrides node voltages after
    the DC solve.

    If ``dc_initial`` is False, purely zero initial state is used before
    applying ``.ic`` overrides (legacy behavior).
    """
    if dt <= 0 or tstop <= 0:
        raise ValueError("dt and tstop must be > 0")

    system: MatrixSystem = build_mna_system(circuit)
    n_voltage = system.node_map.n_voltage
    size = system.size

    t_arr = np.arange(0.0, tstop + 0.5 * dt, dt)
    n_steps = len(t_arr) - 1

    if dc_initial:
        x = solve_dc_operating_point(system, t=dc_time)
    else:
        x = np.zeros(size, dtype=float)
    # .ic overrides node voltages only (indices < n_voltage)
    for node, v0 in circuit.initial_conditions.items():
        idx = system.node_map.get(node)
        if idx is not None:
            x[idx] = float(v0)

    A = system.G + system.C / dt
    lu = _factorize_superlu(A)

    all_v = np.zeros((n_steps + 1, n_voltage), dtype=float)
    all_v[0, :] = x[:n_voltage]

    for k in range(1, n_steps + 1):
        t = t_arr[k]
        rhs = system.source_fn(t) + (system.C / dt) @ x
        x = lu.solve(rhs)
        all_v[k, :] = x[:n_voltage]

    node_names = [system.node_map.idx_to_node[i] for i in range(n_voltage)]

    selected = probes if probes else circuit.probes
    if not selected:
        selected = node_names
    probe_map: Dict[str, np.ndarray] = {}
    for p in selected:
        idx = system.node_map.get(p)
        if idx is None:
            probe_map[p] = np.zeros_like(t_arr)
        else:
            probe_map[p] = all_v[:, idx]

    return SimulationResult(times=t_arr, node_names=node_names, voltages=all_v, probes=probe_map)
