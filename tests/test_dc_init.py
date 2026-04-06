import unittest

from sim.parser import parse_netlist_text
from sim.solver import run_transient_be, solve_dc_operating_point
from sim.stamp import build_mna_system


class DcInitTests(unittest.TestCase):
    def test_current_source_first_sample_near_dc(self):
        text = """
R1 out 0 2000
I1 0 out DC 1e-3
.probe out
"""
        c = parse_netlist_text(text)
        result = run_transient_be(c, tstop=2e-3, dt=1e-5, dc_initial=True)
        out0 = result.probes["out"][0]
        self.assertAlmostEqual(out0, 2.0, delta=1e-8)

    def test_legacy_zero_start_without_dc(self):
        text = """
R1 out 0 2000
I1 0 out DC 1e-3
.probe out
"""
        c = parse_netlist_text(text)
        result = run_transient_be(c, tstop=2e-3, dt=1e-5, dc_initial=False)
        self.assertAlmostEqual(result.probes["out"][0], 0.0, delta=1e-15)

    def test_ic_overrides_dc_node(self):
        text = """
R1 out 0 2000
I1 0 out DC 1e-3
.probe out
.ic out 0.5
"""
        c = parse_netlist_text(text)
        result = run_transient_be(c, tstop=1e-4, dt=1e-5, dc_initial=True)
        self.assertAlmostEqual(result.probes["out"][0], 0.5, delta=1e-10)

    def test_solve_dc_step_matches_t0_source(self):
        text = """
R1 in out 1000
C1 out 0 1e-6
V1 in 0 STEP 0 1 0
.probe out
"""
        c = parse_netlist_text(text)
        system = build_mna_system(c)
        x = solve_dc_operating_point(system)
        idx = system.node_map.get("out")
        self.assertIsNotNone(idx)
        self.assertAlmostEqual(x[idx], 0.0, delta=1e-12)

    def test_dc_op_at_zero_can_use_stepped_value(self):
        text = """
R1 in out 1000
C1 out 0 1e-6
V1 in 0 STEP 0 1 0
.probe out
"""
        c = parse_netlist_text(text)
        system = build_mna_system(c)
        x = solve_dc_operating_point(system, t=0.0)
        idx = system.node_map.get("out")
        self.assertIsNotNone(idx)
        self.assertAlmostEqual(x[idx], 1.0, delta=1e-12)


if __name__ == "__main__":
    unittest.main()
