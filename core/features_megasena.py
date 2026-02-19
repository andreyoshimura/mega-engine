import pandas as pd
import numpy as np
from pathlib import Path

RESULTS_PATH = Path("data/results/megasena.csv")
OUT_PATH = Path("data/features/dezenas.csv")

WINDOW = 100


def generate_features():
    df = pd.read_csv(RESULTS_PATH)
    freq = np.zeros(61)

    for _, row in df.tail(WINDOW).iterrows():
        for i in range(1, 7):
            freq[int(row[f"d{i}"])] += 1

    features = []
    for n in range(1, 61):
        features.append(
            {
                "dezena": n,
                "freq_100": freq[n],
            }
        )

    out = pd.DataFrame(features)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_PATH, index=False)


if __name__ == "__main__":
    generate_features()
