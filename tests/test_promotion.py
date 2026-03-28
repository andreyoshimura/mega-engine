import unittest

from core.config import DEFAULT_PROMOTION_GUARD
from core.promotion import evaluate_promotion_guard


class PromotionGuardTests(unittest.TestCase):
    def test_promotion_guard_accepts_improving_candidate(self):
        current = {"avg_score": 1.5, "rate_ge4": 0.2, "avg_max_hits": 2.1}
        candidate = {"avg_score": 1.8, "rate_ge4": 0.25, "avg_max_hits": 2.2}

        decision = evaluate_promotion_guard(current, candidate, DEFAULT_PROMOTION_GUARD)

        self.assertTrue(decision["should_promote"])
        self.assertEqual(decision["reasons"], ["promotion_guard_passed"])

    def test_promotion_guard_blocks_regression(self):
        current = {"avg_score": 2.0, "rate_ge4": 0.3, "avg_max_hits": 2.4}
        candidate = {"avg_score": 1.6, "rate_ge4": 0.2, "avg_max_hits": 2.1}

        decision = evaluate_promotion_guard(current, candidate, DEFAULT_PROMOTION_GUARD)

        self.assertFalse(decision["should_promote"])
        self.assertIn("score_regression_guard", decision["reasons"])
        self.assertIn("ge4_regression_guard", decision["reasons"])


if __name__ == "__main__":
    unittest.main()
