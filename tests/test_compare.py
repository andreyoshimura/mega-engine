import unittest
from unittest.mock import mock_open, patch

from core.compare_results import _draw_date_to_timestamp_utc, compute_hits, load_pending_draws, LatestDraw


class CompareTests(unittest.TestCase):
    def test_draw_date_to_timestamp_utc_normalizes_to_same_draw_day(self):
        self.assertEqual(_draw_date_to_timestamp_utc("26/03/2026"), "2026-03-26T00:00:00+00:00")

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
    def test_load_pending_draws_uses_results_csv_until_latest_draw(self):
        csv_text = "\n".join(
            [
                "concurso,data,d1,d2,d3,d4,d5,d6",
                "2989,26/03/2026,6,14,28,31,56,59",
                "2990,28/03/2026,6,14,18,29,30,44",
                "2991,31/03/2026,4,14,19,23,36,53",
            ]
        )
        latest = LatestDraw(concurso=2991, data="31/03/2026", dezenas=(4, 14, 19, 23, 36, 53))
        fake_results_csv = mock_open(read_data=csv_text)
        fake_path = type("FakePath", (), {"exists": lambda self: True, "open": fake_results_csv})()

        with patch("core.compare_results.RESULTS_CSV", fake_path):
            draws = load_pending_draws(latest)

        self.assertEqual([draw.concurso for draw in draws], [2989, 2990, 2991])

    def test_load_generated_games_rejects_wrong_current_target(self):
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
