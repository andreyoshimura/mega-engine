# 🎯 Mega Engine

Motor estatístico automatizado para geração, avaliação, versionamento
estratégico e publicação de jogos da Mega-Sena.

O objetivo do projeto não é prever resultados, mas construir um sistema
auditável, mensurável e operacionalmente estável para geração de
combinações com base estatística, mantendo histórico completo de
performance e de estratégia utilizada.

------------------------------------------------------------------------

# 📌 Objetivo

Criar uma engine modular que:

-   Gere jogos automaticamente (9 dezenas por jogo)
-   Registre resultados oficiais automaticamente
-   Calcule acertos por concurso
-   Preserve histórico cumulativo
-   Versione automaticamente cada estratégia utilizada
-   Gere imagens institucionais automaticamente
-   Integre facilmente com automações (n8n, Telegram, redes sociais)

Foco principal:

> Maximizar qualidade estatística, mensurar desempenho real e manter
> consistência operacional.

------------------------------------------------------------------------

# ⚙️ Arquitetura

mega-engine/ ├── core/ │ ├── generator.py │ ├── compare_results.py │ ├──
image_generator.py │ ├── ingest_megasena.py │ ├── features_megasena.py │
├── versioning.py │ ├── optimize.py │ └── backtest.py │ ├── configs/ │
└── strategy_config.json │ ├── data/ │ ├── performance_log.jsonl │ ├──
model_history.jsonl │ └── last_result.json │ ├── out/ │ ├──
jogos_gerados.json │ └── images/ │ ├── mega_atual.png │ └──
mega_semana_X.png │ └── .github/workflows/ ├── daily_generate.yml ├──
compare_results.yml └── generate_images.yml

------------------------------------------------------------------------

# 🔄 Fluxo de Produção

## Daily Generate Workflow

Executa:

-   ingest_megasena.py
-   features_megasena.py
-   generator.py
-   register_strategy()

Atualiza:

-   out/jogos_gerados.json
-   data/model_history.jsonl

------------------------------------------------------------------------

## Compare Workflow

Atualiza:

-   data/last_result.json
-   data/performance_log.jsonl

------------------------------------------------------------------------

## Image Workflow

Gera:

-   out/images/mega_atual.png
-   out/images/mega_semana_X.png

------------------------------------------------------------------------

# 🧠 Versionamento de Estratégia

Cada execução registra:

-   timestamp
-   execution_type
-   strategy_name
-   model_version
-   parameters
-   config_hash
-   commit_sha

Arquivo:

data/model_history.jsonl

Garantias:

-   Append-only
-   Sem duplicação de hash
-   Registro automático via GitHub Actions
-   Auditoria rastreável

------------------------------------------------------------------------

# 📊 Métricas Registradas

-   max_hits
-   count_ge4
-   count_ge5
-   count_eq6
-   score ponderado
-   histograma de distribuição

Arquivo:

data/performance_log.jsonl

------------------------------------------------------------------------

# 📌 Status Atual

✔ Geração automática funcional\
✔ Comparação automática funcional\
✔ Histórico cumulativo preservado\
✔ Versionamento de estratégia implementado e validado\
✔ Automação de imagens via IA\
✔ Pipeline estável

------------------------------------------------------------------------

# ⚠️ Aviso

Este projeto não promete previsão de resultados nem vantagem matemática
garantida.
