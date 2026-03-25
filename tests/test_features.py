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
        self.assertEqual(freq_1, 1.0)
        self.assertEqual(freq_3, 0.0)


if __name__ == "__main__":
    unittest.main()
