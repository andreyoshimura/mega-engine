import unittest

import numpy as np
import pandas as pd

from core.generator import (
    build_output_payload,
    build_weak_pair_set,
    check_max_consecutive,
    count_weak_pairs_in_game,
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
