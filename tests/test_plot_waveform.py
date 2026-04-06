import tempfile
import unittest
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from sim.plot_waveform import load_waveform_csv, plot_waveform, save_figure


class PlotWaveformTests(unittest.TestCase):
    def test_plot_saves_png(self):
        csv_text = "time,v(out)\n0,0\n1e-5,0.5\n"
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "w.csv"
            png_path = Path(tmp) / "w.png"
            csv_path.write_text(csv_text)
            df = load_waveform_csv(csv_path)
            fig = plot_waveform(df, title="test")
            save_figure(fig, png_path)
            plt.close(fig)
            self.assertTrue(png_path.is_file())
            self.assertGreater(png_path.stat().st_size, 100)


if __name__ == "__main__":
    unittest.main()
