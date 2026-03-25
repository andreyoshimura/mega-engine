from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from core.config import DEFAULT_WINDOW, FEATURES_PATH as OUT_PATH, RESULTS_PATH

WINDOW = DEFAULT_WINDOW
DRAW_COLUMNS = [f"d{i}" for i in range(1, 7)]


def build_features(df: pd.DataFrame, window: int = WINDOW) -> pd.DataFrame:
    if window <= 0:
        raise ValueError("window deve ser maior que zero")

    freq = np.zeros(61, dtype=float)

    if not df.empty:
        recent = df.tail(window)
        flattened = recent[DRAW_COLUMNS].to_numpy(dtype=int).ravel()
        counts = np.bincount(flattened, minlength=61)
        freq[: len(counts)] = counts

    return pd.DataFrame(
        {
            "dezena": np.arange(1, 61, dtype=int),
            "freq_100": freq[1:61],
        }
    )



def generate_features(
    results_path: Path = RESULTS_PATH,
    out_path: Path = OUT_PATH,
    window: int = WINDOW,
) -> pd.DataFrame:
    df = pd.read_csv(results_path)
    features = build_features(df, window=window)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    features.to_csv(out_path, index=False)
    return features


if __name__ == "__main__":
    generate_features()
