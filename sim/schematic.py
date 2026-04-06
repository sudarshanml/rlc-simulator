"""Schematic editor document → sim.model.Circuit."""

from __future__ import annotations

from typing import Any, Dict, Mapping

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


class SchematicError(ValueError):
    pass


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise SchematicError(msg)


def _parse_source(obj: Mapping[str, Any]) -> SourceSpec:
    _require(isinstance(obj, dict), "source must be an object")
    kind = str(obj.get("kind", "")).upper()
    params = obj.get("params")
    _require(isinstance(params, list), "source.params must be a list")
    tup = tuple(float(x) for x in params)
    if kind == "DC":
        _require(len(tup) == 1, "DC source needs one param")
    elif kind == "STEP":
        _require(len(tup) == 3, "STEP source needs v0, v1, t_step")
    elif kind == "PWL":
        _require(len(tup) >= 2 and len(tup) % 2 == 0, "PWL needs t v pairs")
    else:
        raise SchematicError(f"Unsupported source kind {kind}")
    return SourceSpec(kind=kind, params=tup)


def schematic_to_circuit(data: Mapping[str, Any]) -> Circuit:
    """
    Build a Circuit from a schematic dict (from JSON).

    Expected shape:
      junctions: [{ "id": str, "net": str, "x"?: number, "y"?: number }]
      branches: [{
        "kind": "R"|"C"|"L"|"V"|"I",
        "name": str,
        "jA": str, "jB": str,
        "value"?: number,  # R, C, L
        "source"?: { "kind", "params" }  # V, I
      }]
      probes?: [str]
      initial_conditions?: { node: value, ... }
    """
    _require("junctions" in data and "branches" in data, "missing junctions or branches")
    raw_junctions = data["junctions"]
    raw_branches = data["branches"]
    _require(isinstance(raw_junctions, list), "junctions must be a list")
    _require(isinstance(raw_branches, list), "branches must be a list")

    junctions: Dict[str, Dict[str, Any]] = {}
    for j in raw_junctions:
        _require(isinstance(j, dict), "junction must be an object")
        jid = str(j["id"])
        _require(jid not in junctions, f"duplicate junction id {jid}")
        _require("net" in j, f"junction {jid} missing net")
        junctions[jid] = j

    circuit = Circuit()
    seen_names: set[str] = set()

    for b in raw_branches:
        _require(isinstance(b, dict), "branch must be an object")
        kind = str(b.get("kind", "")).upper()
        name = str(b["name"])
        _require(name not in seen_names, f"duplicate element name {name}")
        seen_names.add(name)
        ja, jb = str(b["jA"]), str(b["jB"])
        _require(ja in junctions and jb in junctions, "unknown junction in branch")
        net_a = normalize_node(str(junctions[ja]["net"]))
        net_b = normalize_node(str(junctions[jb]["net"]))

        if kind == "R":
            val = float(b["value"])
            _require(val > 0, "resistor value must be > 0")
            circuit.resistors.append(
                Resistor(name=name, n1=net_a, n2=net_b, value=val)
            )
        elif kind == "C":
            val = float(b["value"])
            _require(val >= 0, "capacitor value must be >= 0")
            circuit.capacitors.append(
                Capacitor(name=name, n1=net_a, n2=net_b, value=val)
            )
        elif kind == "L":
            val = float(b["value"])
            _require(val > 0, "inductor value must be > 0")
            circuit.inductors.append(
                Inductor(name=name, n1=net_a, n2=net_b, value=val)
            )
        elif kind == "V":
            spec = _parse_source(b["source"])
            circuit.voltage_sources.append(
                VoltageSource(name=name, n_plus=net_a, n_minus=net_b, spec=spec)
            )
        elif kind == "I":
            spec = _parse_source(b["source"])
            circuit.current_sources.append(
                CurrentSource(name=name, n_plus=net_a, n_minus=net_b, spec=spec)
            )
        else:
            raise SchematicError(f"Unsupported branch kind {kind}")

    probes_raw = data.get("probes")
    if probes_raw is not None:
        _require(isinstance(probes_raw, list), "probes must be a list")
        circuit.probes = [normalize_node(str(p)) for p in probes_raw]

    ic_raw = data.get("initial_conditions")
    if ic_raw is not None:
        _require(isinstance(ic_raw, dict), "initial_conditions must be an object")
        for k, v in ic_raw.items():
            circuit.initial_conditions[normalize_node(str(k))] = float(v)

    return circuit