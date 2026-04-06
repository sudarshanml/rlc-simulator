import tempfile
import unittest
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from sim.interactive import Waveform, plot_waveforms, simulate


class InteractiveTests(unittest.TestCase):
    def test_simulate_returns_waveforms_matching_probes(self):
        netlist = """
R1 in out 1000
C1 out 0 1e-6
V1 in 0 STEP 0 1 0
.probe out
"""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "rc.cir"
            p.write_text(netlist)
            duration = 5e-4
            timestep = 1e-5
            wv = simulate(p, duration, timestep)

        self.assertIn("out", wv)
        w = wv["out"]
        n_steps = int(round(duration / timestep)) + 1
        self.assertEqual(len(w.times), n_steps)
        self.assertEqual(len(w.values), n_steps)
        self.assertEqual(len(w.pairs), n_steps)
        self.assertAlmostEqual(w.times[0], 0.0)
        self.assertAlmostEqual(w.times[-1], duration, places=5)

    def test_waveform_pairs_zip(self):
        w = Waveform(times=[0.0, 1.0], values=[2.0, 3.0])
        self.assertEqual(w.pairs, [(0.0, 2.0), (1.0, 3.0)])

    def test_plot_waveforms_smoke(self):
        wv = {
            "a": Waveform(times=[0.0, 1.0], values=[0.0, 1.0]),
            "b": Waveform(times=[0.0, 1.0], values=[0.0, 0.5]),
        }
        fig = plot_waveforms(wv, title="smoke")
        self.assertIsNotNone(fig)
        plt.close(fig)


if __name__ == "__main__":
    unittest.main()
