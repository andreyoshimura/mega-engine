"""
Mega-Engine — Generator (Mega-Sena)

Responsável por:
✔ Gerar jogos estatísticos
✔ Aplicar diversidade estrutural
✔ Validar integridade
✔ Exportar JSON final
✔ Registrar versionamento de estratégia (produção)

Arquitetura preparada para:
- Backtest Walk-Forward
- Múltiplas estratégias
- Ajuste automático de pesos
- Otimização futura
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from core.features_megasena import build_features
from core.versioning import register_strategy


# ============================================================
# PATHS (ancorados no repositório)
# ============================================================

REPO_ROOT = Path(__file__).resolve().parents[1]

FEATURES_PATH = REPO_ROOT / "data" / "features" / "dezenas.csv"
OUT_PATH = REPO_ROOT / "out" / "jogos_gerados.json"
CONFIG_PATH = REPO_ROOT / "configs" / "strategy_config.json"


# ============================================================
# CONFIGURAÇÃO PADRÃO (Mega-Sena)
# ============================================================

N_GAMES = 5
TICKET_SIZE = 9
DRAW_SIZE = 6
N_SIM = 5000

MIN_N = 1
MAX_N = 60

# Controle de diversidade estrutural
MAX_INTERSECTION = 4


# ============================================================
# AMOSTRAGEM PONDERADA
# ============================================================

def weighted_sample(probs: np.ndarray, k: int, rng: np.random.Generator) -> list[int]:
    """
    Amostragem ponderada sem reposição (Efraimidis–Spirakis).

    probs: vetor tamanho 60 (soma 1)
    retorna: lista ordenada de dezenas (1..60)
    """
    u = rng.random(len(probs))
    keys = -np.log(u) / probs
    idx = np.argsort(keys)[:k] + 1
    return sorted(int(x) for x in idx)


# ============================================================
# VALIDAÇÃO RÍGIDA
# ============================================================

def validate_game(game: list[int]) -> None:
    if len(game) != TICKET_SIZE:
        raise ValueError(f"Jogo inválido: esperado {TICKET_SIZE}, obtido {len(game)}")

    if any((n < MIN_N or n > MAX_N) for n in game):
        raise ValueError(f"Jogo inválido: dezenas fora de [{MIN_N}..{MAX_N}]")

    if len(set(game)) != TICKET_SIZE:
        raise ValueError("Jogo inválido: dezenas repetidas")


def _normalize_scores(scores: np.ndarray) -> np.ndarray:
    scores = np.where(np.isfinite(scores), scores, 0.0)
    scores = np.maximum(scores, 0.0) + 1e-9

    total = float(scores.sum())
    if total <= 0:
        return np.ones(60) / 60.0

    return scores / total


# ============================================================
# CARREGAMENTO DE PROBABILIDADES
# ============================================================

def load_probs() -> np.ndarray:
    """
    Carrega probabilidades a partir de data/features/dezenas.csv

    Esperado:
    - dezena (1..60) [opcional]
    - freq_100

    Fallback: uniforme
    """

    if not FEATURES_PATH.exists():
        return np.ones(60) / 60.0

    df = pd.read_csv(FEATURES_PATH)

    if "freq_100" not in df.columns:
        return np.ones(60) / 60.0

    scores = df["freq_100"].astype(float).values

    if "dezena" in df.columns:
        probs = np.zeros(60)
        for d, s in zip(df["dezena"].astype(int), scores):
            if 1 <= d <= 60:
                probs[d - 1] = float(s)
        scores = probs

    return _normalize_scores(scores)


def scores_from_features(features_df: pd.DataFrame) -> np.ndarray:
    if "freq_100" not in features_df.columns:
        return np.ones(60) / 60.0

    scores = features_df["freq_100"].astype(float).values

    if "dezena" in features_df.columns:
        ordered_scores = np.zeros(60)
        for d, s in zip(features_df["dezena"].astype(int), scores):
            if 1 <= d <= 60:
                ordered_scores[d - 1] = float(s)
        scores = ordered_scores

    return _normalize_scores(scores)


def build_probabilities_from_history(
    results_df: pd.DataFrame,
    window: int = 100,
) -> np.ndarray:
    features_df = build_features(results_df, window=window)
    return scores_from_features(features_df)


# ============================================================
# GERAÇÃO PRINCIPAL
# ============================================================

def generate_games_from_probs(
    probs: np.ndarray,
    *,
    seed: int | None = None,
    n_games: int = N_GAMES,
    ticket_size: int = TICKET_SIZE,
    n_sim: int = N_SIM,
    max_intersection: int = MAX_INTERSECTION,
) -> list[list[int]]:
    rng = np.random.default_rng(seed)
    candidates = [weighted_sample(probs, ticket_size, rng) for _ in range(n_sim)]

    selected: list[list[int]] = []

    for g in candidates:
        if len(selected) >= n_games:
            break

        # Controle de diversidade (interseção máxima)
        if all(len(set(g).intersection(s)) <= max_intersection for s in selected):
            selected.append(g)

    # Fallback se diversidade bloquear demais
    if len(selected) < n_games:
        seen = {tuple(x) for x in selected}
        for g in candidates:
            tg = tuple(g)
            if tg not in seen:
                selected.append(g)
                seen.add(tg)
                if len(selected) >= n_games:
                    break

    # Último fallback determinístico
    while len(selected) < n_games:
        g = sorted(rng.choice(np.arange(1, 61), size=ticket_size, replace=False))
        selected.append([int(x) for x in g])

    for g in selected:
        if len(g) != ticket_size:
            raise ValueError(
                f"Jogo inválido: esperado {ticket_size}, obtido {len(g)}"
            )
        if any((n < MIN_N or n > MAX_N) for n in g):
            raise ValueError(f"Jogo inválido: dezenas fora de [{MIN_N}..{MAX_N}]")
        if len(set(g)) != ticket_size:
            raise ValueError("Jogo inválido: dezenas repetidas")

    return selected[:n_games]


def generate_games(seed: int | None = None) -> list[list[int]]:
    probs = load_probs()
    return generate_games_from_probs(probs, seed=seed)


# ============================================================
# EXPORTAÇÃO
# ============================================================

def export_json(games: list[list[int]]) -> None:
    output = {
        "game": "megasena",
        "ticket_size": TICKET_SIZE,
        "draw_size": DRAW_SIZE,
        "n_games": len(games),
        "objective": "maximize_hit_rate_ge4",
        "games": [
            {"id": f"J{str(i+1).zfill(2)}", "numbers": [int(n) for n in g]}
            for i, g in enumerate(games)
        ],
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


# ============================================================
# EXECUÇÃO PRINCIPAL (PRODUÇÃO)
# ============================================================

if __name__ == "__main__":

    # 1️⃣ Carrega configuração oficial da estratégia
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        config = json.load(f)

    # 2️⃣ Gera jogos
    games = generate_games()

    # 3️⃣ Exporta JSON final
    export_json(games)

    # 4️⃣ Registra versionamento (somente produção)
    register_strategy(config, execution_type="production")
