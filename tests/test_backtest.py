import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from core.backtest import build_probability_cache, build_weak_pair_cache, run_backtest, slice_results_for_backtest


def _sample_results_df() -> pd.DataFrame:
    rows = []
    for concurso in range(1, 7):
        row = {"concurso": concurso, "data": f"2026-01-{concurso:02d}"}
        for i in range(1, 7):
            row[f"d{i}"] = ((concurso + i - 2) % 60) + 1
        rows.append(row)
    return pd.DataFrame(rows)


class BacktestTests(unittest.TestCase):
    def test_slice_results_for_backtest_limits_recent_rows(self):
        results_df = _sample_results_df()

        limited = slice_results_for_backtest(results_df, min_history=2, max_draws=3)

        self.assertEqual(len(limited), 3)
        self.assertEqual(list(limited["concurso"]), [4, 5, 6])

    def test_slice_results_for_backtest_respects_minimum_history(self):
        results_df = _sample_results_df()

        limited = slice_results_for_backtest(results_df, min_history=4, max_draws=2)

        self.assertEqual(len(limited), 5)
        self.assertEqual(list(limited["concurso"]), [2, 3, 4, 5, 6])

    def test_build_probability_cache_builds_entries_per_window(self):
        results_df = _sample_results_df()

        with patch("core.backtest.build_probabilities_from_history", return_value=np.ones(60) / 60) as mocked:
            caches = build_probability_cache(results_df, windows=[2, 3], min_history=2, config={})

        self.assertEqual(sorted(caches.keys()), [2, 3])
        self.assertEqual(sorted(caches[2].keys()), [2, 3, 4, 5])
        self.assertEqual(sorted(caches[3].keys()), [3, 4, 5])
        self.assertEqual(mocked.call_count, 7)

    def test_run_backtest_uses_probability_cache_when_available(self):
        results_df = _sample_results_df()
        probability_cache = {idx: np.ones(60) / 60 for idx in range(2, len(results_df))}

        with patch("core.backtest.build_probabilities_from_history") as mocked:
            report = run_backtest(
                results_df,
                window=2,
                min_history=2,
                n_games=2,
                ticket_size=6,
                n_sim=5,
                max_intersection=3,
                probability_cache=probability_cache,
                config={},
            )

        self.assertEqual(report["summary"]["draws_evaluated"], 4)
        self.assertEqual(mocked.call_count, 0)

    def test_run_backtest_can_skip_per_draw_payload(self):
        results_df = _sample_results_df()
        probability_cache = {idx: np.ones(60) / 60 for idx in range(2, len(results_df))}

        report = run_backtest(
            results_df,
            window=2,
            min_history=2,
            n_games=2,
            ticket_size=6,
            n_sim=5,
            max_intersection=3,
            probability_cache=probability_cache,
            config={},
            include_per_draw=False,
        )

        self.assertEqual(report["summary"]["draws_evaluated"], 4)
        self.assertEqual(report["per_draw"], [])

    def test_build_weak_pair_cache_builds_incremental_entries(self):
        results_df = _sample_results_df()

        caches = build_weak_pair_cache(results_df, min_history=2, bottom_pairs=2)

        self.assertEqual(sorted(caches.keys()), [2, 3, 4, 5])
        self.assertTrue(all(isinstance(caches[idx], set) for idx in caches))

    def test_run_backtest_uses_weak_pair_cache_when_available(self):
        results_df = _sample_results_df()
        probability_cache = {idx: np.ones(60) / 60 for idx in range(2, len(results_df))}
        weak_pair_cache = {idx: set() for idx in range(2, len(results_df))}

        report = run_backtest(
            results_df,
            window=2,
            min_history=2,
            n_games=2,
            ticket_size=6,
            n_sim=5,
            max_intersection=3,
            probability_cache=probability_cache,
            weak_pair_cache=weak_pair_cache,
            config={},
            include_per_draw=False,
        )

        self.assertEqual(report["summary"]["draws_evaluated"], 4)


if __name__ == "__main__":
    unittest.main()
