import unittest

import pandas as pd

from core.features_megasena import build_features


class FeaturesTests(unittest.TestCase):
    def test_build_features_counts_recent_window(self):
        df = pd.DataFrame(
            [
                {"concurso": 1, "data": "01/01/2026", "d1": 1, "d2": 2, "d3": 3, "d4": 4, "d5": 5, "d6": 6},
                {"concurso": 2, "data": "02/01/2026", "d1": 1, "d2": 2, "d3": 7, "d4": 8, "d5": 9, "d6": 10},
            ]
        )
        features = build_features(df, window=1)
        freq_1 = float(features.loc[features["dezena"] == 1, "freq_100"].iloc[0])
        freq_3 = float(features.loc[features["dezena"] == 3, "freq_100"].iloc[0])
        freq_20_1 = float(features.loc[features["dezena"] == 1, "freq_20"].iloc[0])
        atraso_3 = float(features.loc[features["dezena"] == 3, "atraso_draws"].iloc[0])
        bayes_1 = float(features.loc[features["dezena"] == 1, "bayes_mean"].iloc[0])
        bayes_3 = float(features.loc[features["dezena"] == 3, "bayes_mean"].iloc[0])
        self.assertEqual(freq_1, 2.0)
        self.assertEqual(freq_3, 1.0)
        self.assertEqual(freq_20_1, 2.0)
        self.assertEqual(atraso_3, 1.0)
        self.assertGreater(bayes_1, bayes_3)
        self.assertIn("bayes_mean", features.columns)
        self.assertIn("bayes_var", features.columns)
        self.assertIn("bayes_score", features.columns)
        self.assertIn("atraso_score", features.columns)

    def test_build_features_bayesian_signal_respects_recent_draws(self):
        df = pd.DataFrame(
            [
                {"concurso": 1, "data": "01/01/2026", "d1": 1, "d2": 2, "d3": 3, "d4": 4, "d5": 5, "d6": 6},
                {"concurso": 2, "data": "02/01/2026", "d1": 1, "d2": 7, "d3": 8, "d4": 9, "d5": 10, "d6": 11},
            ]
        )
        features = build_features(df, window=2, alpha_prior=1.0, beta_prior=9.0)
        bayes_1 = float(features.loc[features["dezena"] == 1, "bayes_mean"].iloc[0])
        bayes_12 = float(features.loc[features["dezena"] == 12, "bayes_mean"].iloc[0])
        self.assertGreater(bayes_1, bayes_12)

    def test_build_features_atraso_score_favors_more_delayed_numbers(self):
        df = pd.DataFrame(
            [
                {"concurso": 1, "data": "01/01/2026", "d1": 1, "d2": 2, "d3": 3, "d4": 4, "d5": 5, "d6": 6},
                {"concurso": 2, "data": "02/01/2026", "d1": 1, "d2": 7, "d3": 8, "d4": 9, "d5": 10, "d6": 11},
                {"concurso": 3, "data": "03/01/2026", "d1": 1, "d2": 12, "d3": 13, "d4": 14, "d5": 15, "d6": 16},
            ]
        )
        features = build_features(df, window=3)
        atraso_1 = float(features.loc[features["dezena"] == 1, "atraso_score"].iloc[0])
        atraso_6 = float(features.loc[features["dezena"] == 6, "atraso_score"].iloc[0])
        self.assertGreater(atraso_6, atraso_1)


if __name__ == "__main__":
    unittest.main()
