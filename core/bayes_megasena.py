from __future__ import annotations

import numpy as np
import pandas as pd

from core.config import MAX_NUMBER, MIN_NUMBER

DRAW_COLUMNS = [f"d{i}" for i in range(1, 7)]


def build_beta_binomial_posterior(
    results_df: pd.DataFrame,
    *,
    alpha_prior: float = 1.0,
    beta_prior: float = 9.0,
    window: int | None = None,
) -> pd.DataFrame:
    if alpha_prior <= 0 or beta_prior <= 0:
        raise ValueError("alpha_prior e beta_prior devem ser maiores que zero")

    recent_df = results_df.tail(window) if window is not None and window > 0 else results_df
    draws_observed = len(recent_df)

    successes = np.zeros(MAX_NUMBER, dtype=float)
    if draws_observed > 0:
        flattened = recent_df[DRAW_COLUMNS].to_numpy(dtype=int).ravel()
        counts = np.bincount(flattened, minlength=MAX_NUMBER + 1)
        successes = counts[MIN_NUMBER : MAX_NUMBER + 1].astype(float)

    alpha_post = alpha_prior + successes
    beta_post = beta_prior + max(draws_observed, 0) - successes
    mean = alpha_post / (alpha_post + beta_post)
    var = (alpha_post * beta_post) / (
        ((alpha_post + beta_post) ** 2) * (alpha_post + beta_post + 1.0)
    )

    return pd.DataFrame(
        {
            "dezena": np.arange(MIN_NUMBER, MAX_NUMBER + 1, dtype=int),
            "bayes_alpha": alpha_post,
            "bayes_beta": beta_post,
            "bayes_mean": mean,
            "bayes_var": var,
        }
    )
