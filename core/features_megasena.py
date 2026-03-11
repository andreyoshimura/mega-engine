from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = REPO_ROOT / "data" / "results" / "megasena.csv"
OUT_PATH = REPO_ROOT / "data" / "features" / "dezenas.csv"

WINDOW = 100
DRAW_COLUMNS = [f"d{i}" for i in range(1, 7)]


def build_features(df: pd.DataFrame, window: int = WINDOW) -> pd.DataFrame:
    if df.empty:
        freq = np.zeros(61)
    else:
        recent = df.tail(window)
        freq = np.zeros(61)

        for _, row in recent.iterrows():
            for col in DRAW_COLUMNS:
                freq[int(row[col])] += 1

    features = [
        {
            "dezena": n,
            "freq_100": float(freq[n]),
        }
        for n in range(1, 61)
    ]
    return pd.DataFrame(features)


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
