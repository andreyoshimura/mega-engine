import unittest

import pandas as pd

from core.ingest_megasena import merge_results


class IngestTests(unittest.TestCase):
    def test_merge_results_sorts_and_deduplicates_by_concurso(self):
        existing = pd.DataFrame(
            [{"concurso": 10, "data": "01/01/2026", "d1": 1, "d2": 2, "d3": 3, "d4": 4, "d5": 5, "d6": 6}]
        )
        merged = merge_results(
            existing,
            [
                {"concurso": 12, "data": "03/01/2026", "dezenas": [1, 2, 3, 4, 5, 6]},
                {"concurso": 11, "data": "02/01/2026", "dezenas": [7, 8, 9, 10, 11, 12]},
                {"concurso": 10, "data": "01/01/2026", "dezenas": [1, 2, 3, 4, 5, 6]},
            ],
        )
        self.assertEqual(list(merged["concurso"]), [10, 11, 12])


if __name__ == "__main__":
    unittest.main()
