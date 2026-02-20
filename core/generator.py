import pandas as pd
import numpy as np
import json
from pathlib import Path

FEATURES_PATH = Path("data/features/dezenas.csv")
OUT_PATH = Path("out/jogos_gerados.json")

N_GAMES = 15
TICKET_SIZE = 9
N_SIM = 5000


def weighted_sample(probs, k):
    weights = -np.log(np.random.rand(len(probs))) / probs
    idx = np.argsort(weights)[:k] + 1
    return sorted(int(x) for x in idx)


def generate_games():
    df = pd.read_csv(FEATURES_PATH)

    scores = df["freq_100"].values.astype(float) + 1e-6
    probs = scores / scores.sum()

    candidates = [
        weighted_sample(probs, TICKET_SIZE)
        for _ in range(N_SIM)
    ]

    selected = []
    for g in candidates:
        if len(selected) >= N_GAMES:
            break
        if all(len(set(g).intersection(s)) <= 4 for s in selected):
            selected.append(g)

    return selected[:N_GAMES]


def export_json(games):
    output = {
        "game": "megasena",
        "ticket_size": TICKET_SIZE,
        "draw_size": 6,
        "n_games": N_GAMES,
        "objective": "maximize_hit_rate_ge4",
        "games": [
            {
                "id": f"J{str(i+1).zfill(2)}",
                "numbers": [int(n) for n in g],
            }
            for i, g in enumerate(games)
        ],
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    def json_default(o):
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        raise TypeError(f"{type(o)} not serializable")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=json_default)


# ⚠️ IMPORTANTE: nada executa automaticamente ao importar
if __name__ == "__main__":
    games = generate_games()
    export_json(games)
