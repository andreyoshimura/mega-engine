import unittest

from core.monitor_performance import build_monitor_report


class MonitorTests(unittest.TestCase):
    def test_build_monitor_report_flags_drop(self):
        config = {
            "strategy_name": "megasena_v1",
            "model_version": "1.1.0",
            "parameters": {
                "monitoring": {
                    "recent_window": 2,
                    "baseline_window": 3,
                    "min_draws_required": 5,
                    "score_drop_ratio": 0.6,
                    "max_hits_drop_ratio": 0.9,
                    "ge4_drop_ratio": 0.6,
                }
            },
        }
        events = [
            {"concurso": 1, "score": 10, "max_hits": 4, "count_ge4": 1, "count_ge5": 0},
            {"concurso": 2, "score": 9, "max_hits": 4, "count_ge4": 1, "count_ge5": 0},
            {"concurso": 3, "score": 8, "max_hits": 4, "count_ge4": 1, "count_ge5": 0},
            {"concurso": 4, "score": 0, "max_hits": 1, "count_ge4": 0, "count_ge5": 0},
            {"concurso": 5, "score": 0, "max_hits": 1, "count_ge4": 0, "count_ge5": 0},
        ]
        report = build_monitor_report(config, events)
        self.assertTrue(report["decision"]["should_recalibrate"])
        self.assertIn("score_drop", report["decision"]["reasons"])


if __name__ == "__main__":
    unittest.main()
