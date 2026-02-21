import json
from pathlib import Path

import numpy as np
import pandas as pd

# ===== Paths ancorados no repo =====
REPO_ROOT = Path(__file__).resolve().parents[1]  # mega-engine/
FEATURES_PATH = REPO_ROOT / "data" / "features" / "dezenas.csv"
OUT_PATH = REPO_ROOT / "out" / "jogos_gerados.json"

# ===== Config Mega-Sena =====
N_GAMES = 5
TICKET_SIZE = 9
DRAW_SIZE = 6
N_SIM = 5000

MIN_N = 1
MAX_N = 60

# Diversidade básica: máximo de interseção entre jogos
MAX_INTERSECTION = 4


def weighted_sample(probs: np.ndarray, k: int, rng: np.random.Generator) -> list[int]:
    """
    Amostragem ponderada sem reposição (Efraimidis–Spirakis).
    probs: vetor (len 60), soma 1, todos >0
    retorna dezenas 1..60 ordenadas, tamanho k
    """
    u = rng.random(len(probs))
    keys = -np.log(u) / probs
    idx = np.argsort(keys)[:k] + 1  # dezenas 1..60
    return sorted(int(x) for x in idx)


def validate_game(game: list[int]) -> None:
    if len(game) != TICKET_SIZE:
        raise ValueError(f"Jogo inválido: esperado {TICKET_SIZE} dezenas, obtido {len(game)}")
    if any((n < MIN_N or n > MAX_N) for n in game):
        raise ValueError(f"Jogo inválido: dezenas fora de [{MIN_N}..{MAX_N}]: {game}")
    if len(set(game)) != TICKET_SIZE:
        raise ValueError(f"Jogo inválido: dezenas repetidas: {game}")


def load_probs() -> np.ndarray:
    """
    Carrega probabilidades a partir de data/features/dezenas.csv.
    Espera colunas:
      - dezena (1..60)  [opcional, mas recomendado]
      - freq_100 (float/int)
    Se não houver, faz fallback para uniforme.
    """
    if not FEATURES_PATH.exists():
        # fallback: uniforme
        return np.ones(60, dtype=float) / 60.0

    df = pd.read_csv(FEATURES_PATH)

    if "freq_100" not in df.columns:
        return np.ones(60, dtype=float) / 60.0

    scores = df["freq_100"].astype(float).values

    # Se existir coluna "dezena", alinha por 1..60; senão assume ordem correta
    if "dezena" in df.columns:
        probs = np.zeros(60, dtype=float)
        for d, s in zip(df["dezena"].astype(int).values, scores):
            if 1 <= d <= 60:
                probs[d - 1] = float(s)
        scores = probs

    # evita zeros / negativos
    scores = np.where(np.isfinite(scores), scores, 0.0)
    scores = np.maximum(scores, 0.0) + 1e-9

    total = float(scores.sum())
    if total <= 0:
        return np.ones(60, dtype=float) / 60.0

    return scores / total


def generate_games(seed: int | None = None) -> list[list[int]]:
    rng = np.random.default_rng(seed)
    probs = load_probs()

    # gera candidatos
    candidates = [weighted_sample(probs, TICKET_SIZE, rng) for _ in range(N_SIM)]

    selected: list[list[int]] = []
    for g in candidates:
        if len(selected) >= N_GAMES:
            break

        # diversidade por interseção
        if all(len(set(g).intersection(s)) <= MAX_INTERSECTION for s in selected):
            selected.append(g)

    # Se não conseguiu N_GAMES, faz fallback controlado:
    # completa com melhores candidatos únicos (sem repetição interna garantida)
    if len(selected) < N_GAMES:
        seen = {tuple(x) for x in selected}
        for g in candidates:
            tg = tuple(g)
            if tg in seen:
                continue
            selected.append(g)
            seen.add(tg)
            if len(selected) >= N_GAMES:
                break

    # última garantia: se ainda assim falhar, completa com uniforme determinístico
    while len(selected) < N_GAMES:
        g = sorted(rng.choice(np.arange(1, 61), size=TICKET_SIZE, replace=False).tolist())
        selected.append([int(x) for x in g])

    # valida tudo
    for g in selected:
        validate_game(g)

    return selected[:N_GAMES]


def export_json(games: list[list[int]]) -> None:
    output = {
        "game": "megasena",
        "ticket_size": TICKET_SIZE,
        "draw_size": DRAW_SIZE,
        "n_games": len(games),
        "objective": "maximize_hit_rate_ge4",
        "games": [{"id": f"J{str(i+1).zfill(2)}", "numbers": [int(n) for n in g]} for i, g in enumerate(games)],
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    games = generate_games()
    export_json(games)
