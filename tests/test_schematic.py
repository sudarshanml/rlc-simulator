import unittest

from sim.netlist_export import circuit_to_netlist_text
from sim.parser import parse_netlist_text
from sim.schematic import schematic_to_circuit


class SchematicTests(unittest.TestCase):
    def test_round_trip_rc_step(self):
        text = """R1 in out 1000
C1 out 0 1e-6
V1 in 0 STEP 0 1 0
.probe out
"""
        c0 = parse_netlist_text(text)
        sch = {
            "junctions": [
                {"id": "j1", "net": "in", "x": 0, "y": 0},
                {"id": "j2", "net": "out", "x": 0, "y": 0},
                {"id": "j3", "net": "0", "x": 0, "y": 0},
            ],
            "branches": [
                {"kind": "R", "name": "R1", "jA": "j1", "jB": "j2", "value": 1000},
                {"kind": "C", "name": "C1", "jA": "j2", "jB": "j3", "value": 1e-6},
                {
                    "kind": "V",
                    "name": "V1",
                    "jA": "j1",
                    "jB": "j3",
                    "source": {"kind": "STEP", "params": [0, 1, 0]},
                },
            ],
            "probes": ["out"],
        }
        c1 = schematic_to_circuit(sch)
        self.assertEqual(len(c1.resistors), len(c0.resistors))
        self.assertEqual(len(c1.capacitors), len(c0.capacitors))
        self.assertEqual(len(c1.voltage_sources), len(c0.voltage_sources))
        self.assertEqual(c1.probes, ["out"])

    def test_export_netlist_includes_probe(self):
        sch = {
            "junctions": [
                {"id": "a", "net": "in", "x": 0, "y": 0},
                {"id": "b", "net": "out", "x": 0, "y": 0},
                {"id": "c", "net": "0", "x": 0, "y": 0},
            ],
            "branches": [
                {"kind": "R", "name": "R1", "jA": "a", "jB": "b", "value": 1e3},
                {"kind": "C", "name": "C1", "jA": "b", "jB": "c", "value": 1e-6},
                {
                    "kind": "V",
                    "name": "V1",
                    "jA": "a",
                    "jB": "c",
                    "source": {"kind": "DC", "params": [1]},
                },
            ],
            "probes": ["out"],
        }
        c = schematic_to_circuit(sch)
        nt = circuit_to_netlist_text(c)
        self.assertIn(".probe out", nt)
        self.assertIn("V1", nt)


if __name__ == "__main__":
    unittest.main()
