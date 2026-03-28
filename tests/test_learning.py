import unittest

from core.learning import build_incremental_config, build_learning_decision


class LearningTests(unittest.TestCase):
    def test_build_incremental_config_blends_weights_and_bayes(self):
        current = {
            "strategy_name": "megasena_v1",
            "model_version": "1.0.0",
            "parameters": {
                "window": 100,
                "num_games": 6,
                "max_intersection": 3,
                "feature_weights": {"freq_100": 1.0, "bayes_mean": 1.0, "bayes_score": 0.0},
                "bayesian": {"alpha_prior": 1.0, "beta_prior": 9.0},
            },
        }
        recommended = {
            "strategy_name": "megasena_v1",
            "model_version": "1.0.0",
            "parameters": {
                "window": 150,
                "num_games": 5,
                "max_intersection": 4,
                "feature_weights": {"freq_100": 0.6, "bayes_mean": 1.2, "bayes_score": 0.8},
                "bayesian": {"alpha_prior": 2.0, "beta_prior": 8.0},
            },
        }
        learning = {
            "feature_weight_step_ratio": 0.25,
            "bayesian_step_ratio": 0.2,
            "allow_parameter_promotion": True,
            "require_recalibration_signal": True,
        }

        promoted = build_incremental_config(current, recommended, learning)
        params = promoted["parameters"]

        self.assertEqual(params["window"], 150)
        self.assertEqual(params["num_games"], 5)
        self.assertEqual(params["max_intersection"], 4)
        self.assertAlmostEqual(params["feature_weights"]["freq_100"], 0.9)
        self.assertAlmostEqual(params["feature_weights"]["bayes_mean"], 1.05)
        self.assertAlmostEqual(params["feature_weights"]["bayes_score"], 0.2)
        self.assertAlmostEqual(params["bayesian"]["alpha_prior"], 1.2)
        self.assertAlmostEqual(params["bayesian"]["beta_prior"], 8.8)

    def test_learning_decision_requires_recalibration_signal(self):
        current = {
            "strategy_name": "megasena_v1",
            "model_version": "1.0.0",
            "parameters": {
                "learning": {
                    "feature_weight_step_ratio": 0.25,
                    "bayesian_step_ratio": 0.2,
                    "allow_parameter_promotion": True,
                    "require_recalibration_signal": True,
                }
            },
        }
        recommended = {
            "strategy_name": "megasena_v1",
            "model_version": "1.0.0",
            "parameters": {},
        }
        promotion_decision = {"decision": {"should_promote": True, "reasons": ["promotion_guard_passed"]}}
        monitor_report = {"status": "ok", "decision": {"should_recalibrate": False}}

        decision = build_learning_decision(current, recommended, promotion_decision, monitor_report)

        self.assertEqual(decision["action"], "hold_current")
        self.assertIn("waiting_recalibration_signal", decision["reasons"])

    def test_learning_decision_promotes_incrementally_when_allowed(self):
        current = {
            "strategy_name": "megasena_v1",
            "model_version": "1.0.0",
            "parameters": {
                "feature_weights": {"freq_100": 1.0, "bayes_mean": 1.0, "bayes_score": 0.0},
                "bayesian": {"alpha_prior": 1.0, "beta_prior": 9.0},
                "learning": {
                    "feature_weight_step_ratio": 0.25,
                    "bayesian_step_ratio": 0.2,
                    "allow_parameter_promotion": True,
                    "require_recalibration_signal": True,
                },
            },
        }
        recommended = {
            "strategy_name": "megasena_v1",
            "model_version": "1.0.0",
            "parameters": {
                "window": 150,
                "feature_weights": {"freq_100": 0.0, "bayes_mean": 2.0, "bayes_score": 1.0},
                "bayesian": {"alpha_prior": 2.0, "beta_prior": 8.0},
            },
        }
        promotion_decision = {"decision": {"should_promote": True, "reasons": ["promotion_guard_passed"]}}
        monitor_report = {"status": "ok", "decision": {"should_recalibrate": True}}

        decision = build_learning_decision(current, recommended, promotion_decision, monitor_report)

        self.assertEqual(decision["action"], "promote_incremental")
        self.assertIn("recalibration_signal_active", decision["reasons"])
        self.assertEqual(decision["next_config"]["parameters"]["window"], 150)

    def test_learning_decision_holds_when_recommendation_equals_current(self):
        current = {
            "strategy_name": "megasena_v1",
            "model_version": "1.0.0",
            "parameters": {
                "feature_weights": {"freq_100": 1.0},
                "learning": {
                    "feature_weight_step_ratio": 0.25,
                    "bayesian_step_ratio": 0.2,
                    "allow_parameter_promotion": True,
                    "require_recalibration_signal": True,
                },
            },
        }
        recommended = {
            "strategy_name": "megasena_v1",
            "model_version": "1.0.0",
            "parameters": {
                "feature_weights": {"freq_100": 1.0},
                "learning": {
                    "feature_weight_step_ratio": 0.25,
                    "bayesian_step_ratio": 0.2,
                    "allow_parameter_promotion": True,
                    "require_recalibration_signal": True,
                },
            },
        }
        promotion_decision = {"decision": {"should_promote": True, "reasons": ["promotion_guard_passed"]}}
        monitor_report = {"status": "ok", "decision": {"should_recalibrate": True}}

        decision = build_learning_decision(current, recommended, promotion_decision, monitor_report)

        self.assertEqual(decision["action"], "hold_current")
        self.assertIn("no_effective_change", decision["reasons"])


if __name__ == "__main__":
    unittest.main()
