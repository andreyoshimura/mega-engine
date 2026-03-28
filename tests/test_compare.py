import unittest

from core.compare_results import compute_hits


class CompareTests(unittest.TestCase):
    def test_compute_hits_builds_summary_and_histogram(self):
        draw_set = {1, 2, 3, 4, 5, 6}
        games = [
            ("J01", [1, 2, 3, 10, 11, 12, 13, 14, 15]),
            ("J02", [20, 21, 22, 23, 24, 25, 26, 27, 28]),
        ]
        result = compute_hits(draw_set, games)
        self.assertEqual(result["summary"]["max_hits"], 3)
        self.assertEqual(result["summary"]["hist_hits_count"]["3"], 1)
        self.assertEqual(result["summary"]["hist_hits_count"]["0"], 1)
        self.assertEqual(result["summary"]["coverage_count"], 3)
        self.assertEqual(result["summary"]["coverage_rate"], 0.5)
        self.assertEqual(result["summary"]["covered_draw_numbers"], [1, 2, 3])
        self.assertEqual(result["summary"]["neglected_draw_numbers"], [4, 5, 6])


class CompareSnapshotTests(unittest.TestCase):
    def test_load_generated_games_rejects_wrong_current_target(self):
        from unittest.mock import patch
        from core.compare_results import load_generated_games

        payload = {
            "game": "megasena",
            "ticket_size": 9,
            "draw_size": 6,
            "games": [{"id": "J01", "numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9]}],
            "metadata": {"target_concurso": 9999},
        }

        with patch("core.compare_results.OUT_HISTORY") as out_history, patch("core.compare_results._load_json", return_value=payload):
            out_history.__truediv__.return_value.exists.return_value = False
            with self.assertRaises(ValueError):
                load_generated_games(1234)
if __name__ == "__main__":
    unittest.main()
