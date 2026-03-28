import unittest

import numpy as np
import pandas as pd

from core.generator import build_output_payload, generate_games_from_probs, scores_from_features


class GeneratorTests(unittest.TestCase):
    def test_generate_games_from_probs_respects_size_and_uniqueness(self):
        probs = np.ones(60) / 60
        games = generate_games_from_probs(probs, seed=123, n_games=4, ticket_size=9, n_sim=50, max_intersection=3)
        self.assertEqual(len(games), 4)
        for game in games:
            self.assertEqual(len(game), 9)
            self.assertEqual(game, sorted(game))
            self.assertEqual(len(set(game)), 9)

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
                {"dezena": 1, "freq_100": 10.0, "bayes_mean": 0.05, "bayes_score": 0.04},
                {"dezena": 2, "freq_100": 1.0, "bayes_mean": 0.50, "bayes_score": 0.49},
            ]
        )
        config = {
            "parameters": {
                "feature_weights": {
                    "freq_100": 0.0,
                    "bayes_mean": 1.0,
                    "bayes_score": 0.0,
                }
            }
        }
        probs = scores_from_features(features, config=config)
        self.assertGreater(probs[1], probs[0])


if __name__ == "__main__":
    unittest.main()
