import unittest

from sim.schematic_viewer.app import create_app


class SchematicViewerAPITests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app()
        self.client = self.app.test_client()

    def test_simulate_rc_step(self):
        payload = {
            "tstop": 1e-4,
            "dt": 1e-5,
            "schematic": {
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
            },
        }
        res = self.client.post("/api/simulate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertIn("out", data["probes"])
        self.assertEqual(len(data["times"]), len(data["probes"]["out"]))

    def test_netlist_endpoint(self):
        payload = {
            "schematic": {
                "junctions": [{"id": "a", "net": "x", "x": 0, "y": 0}],
                "branches": [],
            }
        }
        res = self.client.post("/api/netlist", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["netlist"].strip(), "")


if __name__ == "__main__":
    unittest.main()
