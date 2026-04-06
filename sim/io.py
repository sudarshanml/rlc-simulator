from pathlib import Path

import pandas as pd

from sim.solver import SimulationResult


def result_to_dataframe(result: SimulationResult) -> pd.DataFrame:
    data = {"time": result.times}
    for node, wave in result.probes.items():
        data[f"v({node})"] = wave
    return pd.DataFrame(data)


def write_csv(result: SimulationResult, output_path: str) -> None:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    result_to_dataframe(result).to_csv(out, index=False)
