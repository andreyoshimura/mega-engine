import pandas as pd
import numpy as np
import json
from pathlib import Path

# -----------------------------------------------------------------------------
# core/generator.py
#
# Função:
# - Gera N_GAMES jogos (apostas) de Mega-Sena com TICKET_SIZE dezenas cada.
# - Usa um CSV de features (data/features/dezenas.csv) como base de pesos
#   (coluna "freq_100") para amostragem ponderada das dezenas.
# - Exporta o resultado para um JSON (out/jogos_gerados.json) para consumo
#   por outras etapas do pipeline (ex.: versionamento no repo, ingest, etc.).
#
# Dependências / Entradas:
# - Arquivo obrigatório: data/features/dezenas.csv
#   - Deve conter a coluna "freq_100" (numérica).
#   - A ordem das linhas define o índice das dezenas: linha 0 -> dezena 1,
#     linha 1 -> dezena 2, etc. (porque usamos +1 no índice do array).
#
# Saídas:
# - out/jogos_gerados.json
#   - Estrutura: metadados do "experimento" + lista de jogos gerados.
#
# Observação importante:
# - Numpy/Pandas usam tipos como numpy.int64, que NÃO são serializáveis por
#   json.dump() diretamente. Por isso:
#   1) Convertemos as dezenas para int nativo.
#   2) Usamos json.dump(..., default=...) para blindar qualquer numpy que escape.
# -----------------------------------------------------------------------------

FEATURES_PATH = Path("data/features/dezenas.csv")
OUT_PATH = Path("out/jogos_gerados.json")

N_GAMES = 15       # Quantidade de jogos a selecionar
TICKET_SIZE = 9    # Quantidade de dezenas por jogo
N_SIM = 5000       # Quantidade de candidatos simulados antes da seleção


def weighted_sample(probs, k):
    """
    Amostra k dezenas (sem reposição) usando pesos proporcionais a 'probs'.

    Implementação:
    - Amostragem ponderada via "exponential race":
      weights = -log(U) / p, onde U~Uniform(0,1) e p são probabilidades.
      Seleciona os menores weights.

    Retorno:
    - Lista ordenada de inteiros (1..N), usando int nativo (JSON friendly).
    """
    weights = -np.log(np.random.rand(len(probs))) / probs
    idx = np.argsort(weights)[:k] + 1  # +1 para mapear índice 0 -> dezena 1
    return sorted(map(int, idx))       # converte numpy.int64 -> int


def generate_games():
    """
    Gera jogos candidatos com amostragem ponderada e depois seleciona um
    subconjunto com baixa sobreposição entre jogos.

    Regras:
    - Gera N_SIM candidatos (cada um com TICKET_SIZE dezenas).
    - Seleciona até N_GAMES jogos garantindo que a interseção com qualquer
      jogo já selecionado seja <= 4 dezenas (diversificação).
    """
    df = pd.read_csv(FEATURES_PATH)

    # Probabilidades derivadas da coluna freq_100 (quanto maior, mais provável).
    # 1e-6 evita probabilidade zero, que quebraria a divisão / amostragem.
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
        # Critério de diversidade: no máximo 4 dezenas iguais entre jogos
        if all(len(set(g).intersection(set(s))) <= 4 for s in selected):
            selected.append(g)

    return selected[:N_GAMES]


def _json_default(o):
    """
    Conversor padrão para json.dump, para tratar tipos numpy (int64, float64, ndarray).
    Evita: TypeError: Object of type int64 is not JSON serializable
    """
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")


def export_json(games):
    """
    Exporta os jogos gerados para JSON.

    - Converte explicitamente as dezenas para int nativo.
    - Usa json.dump com default=_json_default para blindar qualquer numpy que escape.
    - Cria a pasta 'out/' se necessário.
    """
    output = {
        "game": "megasena",
        "ticket_size": TICKET_SIZE,
        "draw_size": 6,
        "n_games": N_GAMES,
        "objective": "maximize_hit_rate_ge4",
        "games": [],
    }

    for i, g in enumerate(games):
        output["games"].append(
            {
                "id": f"J{str(i+1).zfill(2)}",
                "numbers": [int(x) for x in g],
            }
        )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=_json_default)


if __name__ == "__main__":
    games = generate_games()
    export_json(games)
