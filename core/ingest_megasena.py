import requests
import pandas as pd
from pathlib import Path

API_URL = "https://loteriascaixa-api.herokuapp.com/api/megasena"
OUT_PATH = Path("data/results/megasena.csv")


def fetch_results():
    response = requests.get(API_URL)
    response.raise_for_status()
    data = response.json()

    rows = []
    for item in data:
        dezenas = sorted([int(d) for d in item["dezenas"]])
        rows.append(
            {
                "concurso": int(item["concurso"]),
                "data": item["data"],
                **{f"d{i+1}": dezenas[i] for i in range(6)},
            }
        )

    df = pd.DataFrame(rows).sort_values("concurso")
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)


if __name__ == "__main__":
    fetch_results()
