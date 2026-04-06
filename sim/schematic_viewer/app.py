"""Flask app: schematic canvas + transient simulation API."""

from __future__ import annotations

import os
from flask import Flask, jsonify, render_template, request

from sim.netlist_export import circuit_to_netlist_text
from sim.schematic import SchematicError, schematic_to_circuit
from sim.solver import SolveError, run_transient_be


def create_app() -> Flask:
    root = os.path.dirname(os.path.abspath(__file__))
    app = Flask(
        __name__,
        static_folder=os.path.join(root, "static"),
        template_folder=os.path.join(root, "templates"),
    )

    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.post("/api/simulate")
    def api_simulate():
        try:
            payload = request.get_json(force=True, silent=False)
            if not isinstance(payload, dict):
                return jsonify({"ok": False, "error": "JSON object expected"}), 400
            schematic = payload.get("schematic")
            if not isinstance(schematic, dict):
                return jsonify({"ok": False, "error": "schematic object required"}), 400
            tstop = float(payload.get("tstop", 0.0))
            dt = float(payload.get("dt", 0.0))
            if tstop <= 0 or dt <= 0:
                return jsonify({"ok": False, "error": "tstop and dt must be positive"}), 400
            circuit = schematic_to_circuit(schematic)
            result = run_transient_be(circuit, tstop=tstop, dt=dt, probes=None)
            times = result.times.tolist()
            probes_out = {k: v.tolist() for k, v in result.probes.items()}
            return jsonify({"ok": True, "times": times, "probes": probes_out})
        except SchematicError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        except SolveError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.post("/api/netlist")
    def api_netlist():
        try:
            payload = request.get_json(force=True, silent=False)
            if not isinstance(payload, dict):
                return jsonify({"ok": False, "error": "JSON object expected"}), 400
            schematic = payload.get("schematic")
            if not isinstance(schematic, dict):
                return jsonify({"ok": False, "error": "schematic object required"}), 400
            circuit = schematic_to_circuit(schematic)
            text = circuit_to_netlist_text(circuit)
            return jsonify({"ok": True, "netlist": text})
        except SchematicError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    return app
