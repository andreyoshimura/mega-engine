import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import numpy as np
import pandas as pd

from core.generator import (
    _is_materially_equal_output,
    build_output_payload,
    build_weak_pair_set,
    check_max_consecutive,
    count_weak_pairs_in_game,
    export_json,
    generate_games_from_probs,
    scores_from_features,
)


class GeneratorTests(unittest.TestCase):
    def test_generate_games_from_probs_respects_size_and_uniqueness(self):
        probs = np.ones(60) / 60
        games = generate_games_from_probs(probs, seed=123, n_games=4, ticket_size=9, n_sim=50, max_intersection=3)
        self.assertEqual(len(games), 4)
        for game in games:
            self.assertEqual(len(game), 9)
            self.assertEqual(game, sorted(game))
            self.assertEqual(len(set(game)), 9)

    def test_generate_games_from_probs_respects_max_seq_and_min_diff(self):
        probs = np.ones(60) / 60
        games = generate_games_from_probs(
            probs,
            seed=123,
            n_games=3,
            ticket_size=6,
            n_sim=300,
            max_intersection=5,
            max_seq=2,
            min_diff=3,
        )
        self.assertEqual(len(games), 3)
        for game in games:
            self.assertTrue(check_max_consecutive(game, 2))
        self.assertGreaterEqual(len(set(games[0]).difference(games[1])), 3)

    def test_build_output_payload_keeps_n8n_contract_and_metadata(self):
        config = {"strategy_name": "megasena_v1", "model_version": "1.1.0", "parameters": {"ticket_size": 9}}
        payload = build_output_payload([[1, 2, 3, 4, 5, 6, 7, 8, 9]], config)
        self.assertEqual(payload["game"], "megasena")
        self.assertEqual(payload["games"][0]["id"], "J01")
        self.assertEqual(payload["metadata"]["strategy_name"], "megasena_v1")
        self.assertIn("generation_seed", payload["metadata"])

    def test_is_materially_equal_output_ignores_generated_timestamp(self):
        current = {
            "game": "megasena",
            "ticket_size": 9,
            "draw_size": 6,
            "n_games": 1,
            "objective": "maximize_hit_rate_ge4",
            "games": [{"id": "J01", "numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9]}],
            "metadata": {"generated_at_utc": "2026-04-02T00:00:00+00:00", "target_concurso": 2992},
        }
        existing = {
            **current,
            "metadata": {"generated_at_utc": "2026-04-02T00:05:00+00:00", "target_concurso": 2992},
        }
        self.assertTrue(_is_materially_equal_output(current, existing))

    def test_export_json_skips_rewrite_when_games_and_target_are_equal(self):
        with TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "jogos_gerados.json"
            history_dir = Path(tmpdir) / "history"
            config = {"strategy_name": "megasena_v1", "model_version": "1.1.0", "parameters": {"ticket_size": 9}}
            games = [[1, 2, 3, 4, 5, 6, 7, 8, 9]]
            existing_payload = {
                "game": "megasena",
                "ticket_size": 9,
                "draw_size": 6,
                "n_games": 1,
                "objective": "maximize_hit_rate_ge4",
                "games": [{"id": "J01", "numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9]}],
                "metadata": {"generated_at_utc": "2026-04-02T00:00:00+00:00", "target_concurso": 2992},
            }
            out_path.write_text(__import__("json").dumps(existing_payload), encoding="utf-8")

            with patch("core.generator.OUT_PATH", out_path), patch("core.generator.OUT_HISTORY_DIR", history_dir), patch(
                "core.generator.build_output_payload",
                return_value={
                    **existing_payload,
                    "metadata": {"generated_at_utc": "2026-04-02T00:10:00+00:00", "target_concurso": 2992},
                },
            ):
                payload, changed = export_json(games, config=config)

            self.assertFalse(changed)
            self.assertEqual(payload["metadata"]["target_concurso"], 2992)
            self.assertFalse(history_dir.exists())

    def test_scores_from_features_combines_freq_and_bayesian_weights(self):
        features = pd.DataFrame(
            [
                {
                    "dezena": 1,
                    "freq_20": 0.0,
                    "freq_50": 0.0,
                    "freq_100": 10.0,
                    "atraso_score": 0.1,
                    "bayes_mean": 0.05,
                    "bayes_score": 0.04,
                },
                {
                    "dezena": 2,
                    "freq_20": 3.0,
                    "freq_50": 2.0,
                    "freq_100": 1.0,
                    "atraso_score": 0.9,
                    "bayes_mean": 0.50,
                    "bayes_score": 0.49,
                },
            ]
        )
        config = {
            "parameters": {
                "feature_weights": {
                    "freq_20": 1.0,
                    "freq_50": 0.5,
                    "freq_100": 0.0,
                    "atraso_score": 1.0,
                    "bayes_mean": 1.0,
                    "bayes_score": 0.0,
                    "score_alpha": 1.0,
                }
            }
        }
        probs = scores_from_features(features, config=config)
        self.assertGreater(probs[1], probs[0])

    def test_scores_from_features_applies_score_alpha(self):
        features = pd.DataFrame(
            [
                {"dezena": 1, "freq_20": 1.0, "freq_50": 0.0, "freq_100": 0.0, "atraso_score": 0.0, "bayes_mean": 0.0, "bayes_score": 0.0},
                {"dezena": 2, "freq_20": 2.0, "freq_50": 0.0, "freq_100": 0.0, "atraso_score": 0.0, "bayes_mean": 0.0, "bayes_score": 0.0},
            ]
        )
        linear = scores_from_features(features, config={"parameters": {"feature_weights": {"freq_20": 1.0, "score_alpha": 1.0}}})
        aggressive = scores_from_features(features, config={"parameters": {"feature_weights": {"freq_20": 1.0, "score_alpha": 2.0}}})
        self.assertGreater(aggressive[1] - aggressive[0], linear[1] - linear[0])

    def test_build_weak_pair_set_and_count_penalty(self):
        results_df = pd.DataFrame(
            [
                {"concurso": 1, "data": "01/01/2026", "d1": 1, "d2": 2, "d3": 3, "d4": 4, "d5": 5, "d6": 6},
                {"concurso": 2, "data": "02/01/2026", "d1": 1, "d2": 2, "d3": 7, "d4": 8, "d5": 9, "d6": 10},
                {"concurso": 3, "data": "03/01/2026", "d1": 1, "d2": 3, "d3": 7, "d4": 11, "d5": 12, "d6": 13},
            ]
        )
        weak_pairs = build_weak_pair_set(results_df, 3)
        self.assertTrue(weak_pairs)
        weak_pair = next(iter(weak_pairs))
        game = sorted({weak_pair[0], weak_pair[1], 20, 21, 22, 23})
        penalty = count_weak_pairs_in_game(game, weak_pairs)
        self.assertGreaterEqual(penalty, 1)


if __name__ == "__main__":
    unittest.main()
