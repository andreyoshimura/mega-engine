from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from core.bayes_megasena import build_beta_binomial_posterior
from core.config import DEFAULT_WINDOW, FEATURES_PATH as OUT_PATH, RESULTS_PATH, get_bayesian, get_parameters, load_config

WINDOW = DEFAULT_WINDOW
DRAW_COLUMNS = [f"d{i}" for i in range(1, 7)]


def _count_frequency(recent: pd.DataFrame) -> np.ndarray:
    freq = np.zeros(61, dtype=float)
    if recent.empty:
        return freq

    flattened = recent[DRAW_COLUMNS].to_numpy(dtype=int).ravel()
    counts = np.bincount(flattened, minlength=61)
    freq[: len(counts)] = counts
    return freq


def _build_atraso(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    atraso_draws = np.full(61, len(df), dtype=float)
    if df.empty:
        return atraso_draws, np.zeros(61, dtype=float)

    for number in range(1, 61):
        mask = (df[DRAW_COLUMNS] == number).any(axis=1)
        positions = np.flatnonzero(mask.to_numpy())
        if len(positions) > 0:
            atraso_draws[number] = float((len(df) - 1) - positions[-1])

    atraso_slice = atraso_draws[1:61]
    scale = float(max(atraso_slice.max(), 1.0))
    atraso_score = np.zeros(61, dtype=float)
    atraso_score[1:61] = atraso_slice / scale
    return atraso_draws, atraso_score


def build_features(
    df: pd.DataFrame,
    window: int = WINDOW,
    *,
    alpha_prior: float = 1.0,
    beta_prior: float = 9.0,
) -> pd.DataFrame:
    if window <= 0:
        raise ValueError("window deve ser maior que zero")

    recent = df.tail(window)
    recent_20 = df.tail(20)
    recent_50 = df.tail(50)
    recent_100 = df.tail(100)
    freq_20 = _count_frequency(recent_20)
    freq_50 = _count_frequency(recent_50)
    freq_100 = _count_frequency(recent_100)
    atraso_draws, atraso_score = _build_atraso(df)

    features = pd.DataFrame(
        {
            "dezena": np.arange(1, 61, dtype=int),
            "freq_20": freq_20[1:61],
            "freq_50": freq_50[1:61],
            "freq_100": freq_100[1:61],
            "atraso_draws": atraso_draws[1:61],
            "atraso_score": atraso_score[1:61],
        }
    )
    bayes = build_beta_binomial_posterior(
        recent,
        alpha_prior=alpha_prior,
        beta_prior=beta_prior,
    )
    features = features.merge(bayes, on="dezena", how="left")
    # Penaliza incerteza alta, deixando uma coluna pronta para calibracao futura.
    features["bayes_score"] = features["bayes_mean"] - features["bayes_var"]
    return features



def generate_features(
    results_path: Path = RESULTS_PATH,
    out_path: Path = OUT_PATH,
    window: int = WINDOW,
    *,
    alpha_prior: float = 1.0,
    beta_prior: float = 9.0,
) -> pd.DataFrame:
    df = pd.read_csv(results_path)
    features = build_features(df, window=window, alpha_prior=alpha_prior, beta_prior=beta_prior)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    features.to_csv(out_path, index=False)
    return features


if __name__ == "__main__":
    config = load_config()
    bayesian = get_bayesian(config)
    generate_features(
        window=int(get_parameters(config).get("window", WINDOW)),
        alpha_prior=float(bayesian["alpha_prior"]),
        beta_prior=float(bayesian["beta_prior"]),
    )
