import math
import unittest

import numpy as np

from sim.parser import parse_netlist_text
from sim.solver import run_transient_be


class TransientTests(unittest.TestCase):
    def test_rc_step_response_matches_first_order_trend(self):
        # RC low-pass with 1V step at t=0: vout(t)=1-exp(-t/RC)
        text = """
R1 in out 1000
C1 out 0 1e-6
V1 in 0 STEP 0 1 0
.probe out
"""
        c = parse_netlist_text(text)
        dt = 1e-5
        tstop = 5e-3
        result = run_transient_be(c, tstop=tstop, dt=dt)

        out = result.probes["out"]
        t = result.times
        tau = 1e-3
        ideal = 1.0 - np.exp(-t / tau)

        # Backward Euler is diffusive; allow bounded numeric error.
        max_abs_err = np.max(np.abs(out - ideal))
        self.assertLess(max_abs_err, 0.05)
        self.assertGreater(out[-1], 0.98)

    def test_rc_ladder_is_monotonic_under_step(self):
        text = """
R1 in n1 1000
R2 n1 n2 1000
C1 n1 0 1e-6
C2 n2 0 1e-6
V1 in 0 STEP 0 1 0
.probe n1 n2
"""
        c = parse_netlist_text(text)
        result = run_transient_be(c, tstop=4e-3, dt=2e-5)
        n2 = result.probes["n2"]

        # For this passive RC ladder and step input, n2 should not decrease materially.
        diffs = np.diff(n2)
        self.assertGreaterEqual(diffs.min(), -1e-4)
        self.assertLessEqual(n2[-1], 1.0 + 1e-6)

    def test_dc_limit_with_current_source(self):
        # R to ground with constant current injection should settle near I*R.
        text = """
R1 out 0 2000
I1 0 out DC 1e-3
.probe out
"""
        c = parse_netlist_text(text)
        result = run_transient_be(c, tstop=2e-3, dt=1e-5)
        out_final = result.probes["out"][-1]
        self.assertAlmostEqual(out_final, 2.0, delta=1e-2)

    def test_rc_follows_pwl_ramp_input(self):
        # Input ramps 0->1 over [0,1ms]; low-pass should track with lag.
        text = """
R1 in out 1000
C1 out 0 1e-6
V1 in 0 PWL 0 0 1e-3 1 2e-3 1
.probe out
"""
        c = parse_netlist_text(text)
        dt = 1e-5
        result = run_transient_be(c, tstop=5e-3, dt=dt)
        out = result.probes["out"]
        self.assertLess(out[len(out) // 8], 0.2)
        self.assertGreater(out[-1], 0.95)


if __name__ == "__main__":
    unittest.main()
