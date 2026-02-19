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
    return sorted(np.argsort(weights)[:k] + 1)


def generate_games():
    df = pd.read_csv(FEATURES_PATH)

    scores = df["freq_100"].values + 1e-6
    probs = scores / scores.sum()

    candidates = []

    for _ in range(N_SIM):
        game = weighted_sample(probs, TICKET_SIZE)
        candidates.append(game)

    selected = []
    for g in candidates:
        if len(selected) >= N_GAMES:
            break
        if all(len(set(g).intersection(set(s))) <= 4 for s in selected):
            selected.append(g)

    return selected[:N_GAMES]


def export_json(games):
    output = {
        "game": "megasena",
        "ticket_size": 9,
        "draw_size": 6,
        "n_games": 15,
        "objective": "maximize_hit_rate_ge4",
        "games": [],
    }

    for i, g in enumerate(games):
        output["games"].append(
            {
                "id": f"J{str(i+1).zfill(2)}",
                "numbers": g,
            }
        )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(output, f, indent=2)


if __name__ == "__main__":
    games = generate_games()
    export_json(games)
