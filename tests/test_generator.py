import unittest

import numpy as np

from core.generator import build_output_payload, generate_games_from_probs


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


if __name__ == "__main__":
    unittest.main()
