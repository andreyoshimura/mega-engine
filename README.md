# 🎯 Mega Engine

Motor estatístico automatizado para geração, avaliação, versionamento e
recalibração controlada de estratégias da Mega-Sena.

O projeto não busca "prever" resultados. O foco é construir um sistema
auditável, mensurável e evolutivo para gerar combinações, comparar
desempenho e promover ajustes de estratégia com base em histórico real.

------------------------------------------------------------------------

# 📌 Objetivo

Criar uma engine modular que:

-   Gere jogos automaticamente (9 dezenas por jogo)
-   Registre resultados oficiais automaticamente
-   Calcule acertos por concurso
-   Preserve histórico cumulativo
-   Versione automaticamente cada estratégia utilizada
-   Gere imagens institucionais automaticamente
-   Execute backtests walk-forward reproduzíveis
-   Otimize parâmetros da estratégia com base em histórico
-   Monitore queda de desempenho e sinalize recalibração
-   Integre facilmente com automações (GitHub Actions, n8n, Telegram,
    redes sociais)

Foco principal:

> Maximizar consistência estatística, mensurar desempenho real e manter
> evolução controlada da estratégia.

------------------------------------------------------------------------

# ⚙️ Arquitetura Atual

    mega-engine/
    ├── core/
    │   ├── ingest_megasena.py
    │   ├── features_megasena.py
    │   ├── generator.py
    │   ├── compare_results.py
    │   ├── versioning.py
    │   ├── backtest.py
    │   ├── optimize.py
    │   ├── monitor_performance.py
    │   └── image_generator.py
    │
    ├── configs/
    │   └── strategy_config.json
    │
    ├── data/
    │   ├── results/megasena.csv
    │   ├── features/dezenas.csv
    │   ├── performance_log.jsonl
    │   ├── model_history.jsonl
    │   └── last_result.json
    │
    ├── out/
    │   ├── jogos_gerados.json
    │   ├── backtest_report.json
    │   ├── optimization_report.json
    │   ├── recommended_strategy_config.json
    │   ├── performance_monitor.json
    │   ├── recalibration_signal.json
    │   └── images/
    │       ├── mega_atual.png
    │       └── mega_semana_X.png
    │
    └── .github/workflows/
        ├── daily_generate.yml
        ├── compare_results.yml
        ├── backtest.yml
        ├── optimize.yml
        └── generate_images.yml

------------------------------------------------------------------------

# 🔄 Fluxo Operacional

## 1. Daily Generate

Executa:

-   `core.ingest_megasena`
-   `core.features_megasena`
-   `core.generator`

Atualiza:

-   `data/results/megasena.csv`
-   `data/features/dezenas.csv`
-   `out/jogos_gerados.json`
-   `data/model_history.jsonl`

## 2. Compare Results

Executa:

-   `core.compare_results`
-   `core.monitor_performance`

Atualiza:

-   `data/performance_log.jsonl`
-   `out/performance_monitor.json`
-   `out/recalibration_signal.json`

## 3. Backtest

Executa:

-   `core.backtest`

Atualiza:

-   `out/backtest_report.json`

## 4. Optimize

Executa:

-   `core.optimize`

Atualiza:

-   `out/optimization_report.json`
-   `out/recommended_strategy_config.json`

## 5. Image Generation

Executa:

-   `core.image_generator`

Atualiza:

-   `out/images/mega_atual.png`
-   `out/images/mega_semana_X.png`

------------------------------------------------------------------------

# 📊 Estratégia Atual

Configuração atualmente promovida:

-   `ticket_size = 9`
-   `num_games = 6`
-   `window = 100`
-   `min_history = 100`
-   `max_intersection = 3`
-   `backtest_n_sim = 20`

Monitoramento atual:

-   `recent_window = 5`
-   `baseline_window = 20`
-   `min_draws_required = 12`
-   `score_drop_ratio = 0.5`
-   `max_hits_drop_ratio = 0.85`
-   `ge4_drop_ratio = 0.5`

Grid atual de otimização:

-   `window = [50, 100, 150]`
-   `num_games = [4, 5, 6]`
-   `max_intersection = [3, 4, 5]`

------------------------------------------------------------------------

# 📊 Versionamento de Estratégia

Cada execução de produção registra:

-   `strategy_name`
-   `model_version`
-   parâmetros utilizados
-   `config_hash`
-   `timestamp`
-   `execution_type`
-   `commit_sha`

Arquivo:

`data/model_history.jsonl`

Garantias:

-   Append-only
-   Hash para evitar duplicidade imediata
-   Auditoria de mudanças de configuração
-   Histórico versionado via Git

------------------------------------------------------------------------

# ✅ Etapas Concluídas

## Fase 1 --- Pipeline Operacional

Concluído:

-   Ingestão automática com fallback entre API oficial e histórico
-   Geração de features básicas por frequência recente
-   Geração de jogos com diversidade estrutural
-   Comparação dos jogos com resultado oficial
-   Registro de performance em histórico append-only
-   Versionamento da estratégia em produção
-   Geração automática de imagens institucionais
-   Automação completa via GitHub Actions

## Fase 2 --- Estrutura Estatística Base

Concluído:

-   Backtest walk-forward automatizado
-   Otimização de parâmetros por grid search
-   Exportação de configuração recomendada
-   Monitoramento de queda de desempenho real
-   Sinal explícito de recalibração
-   Promoção manual controlada de nova configuração

------------------------------------------------------------------------

# 🚧 Etapa Atual

O projeto está atualmente em:

## Fase 2.5 --- Recalibração Controlada

Estado atual:

-   Pipeline operacional validado em produção
-   Backtest remoto validado no GitHub Actions
-   Otimização remota validada no GitHub Actions
-   Estratégia promovida com base em comparação histórica
-   Monitor pronto para indicar quando recalibrar

Ainda em aberto nesta etapa:

-   Disparo automático de recalibração a partir do sinal de monitoramento
-   Processo formal de champion/challenger
-   Regra automática de promoção ou rejeição de estratégia candidata

------------------------------------------------------------------------

# 🚀 Próximas Etapas

## Próxima Etapa Imediata

-   Criar workflow de recalibração controlada
-   Ler `out/recalibration_signal.json`
-   Rodar `optimize` apenas quando houver sinal
-   Comparar config atual vs config recomendada
-   Aprovar ou rejeitar promoção com critérios objetivos

## Roadmap de Curto Prazo

-   Padronizar comparação entre estratégia `champion` e `challenger`
-   Criar relatório consolidado de promoção de estratégia
-   Incluir métricas de janela recente no backtest e na otimização
-   Adicionar guard de não-regressão antes de promover config nova
-   Reduzir custo computacional de backtest/optimize sem perder rastreabilidade

## Roadmap de Médio Prazo

-   Feature engineering adicional:
    - frequência curta vs longa
    - atraso desde última aparição
    - repetição em relação ao último concurso
    - distribuição por faixas
    - pares/ímpares
-   Score composto com pesos ajustáveis
-   Penalização explícita de combinações pouco desejáveis
-   Dashboard simplificado de performance

## Roadmap de Longo Prazo

-   Modelos supervisionados para scoring de dezenas
-   Ensemble entre heurística e modelo estatístico/ML
-   Validação temporal mais robusta
-   Registro versionado de modelos treinados
-   Recalibração assistida por dados com promoção segura

------------------------------------------------------------------------

# 🎛 Princípios do Projeto

-   Estatística \> Achismo
-   Métrica \> Intuição
-   Histórico \> Memória manual
-   Automação \> Operação manual
-   Reprodutibilidade \> Aleatoriedade não controlada
-   Promoção controlada \> ajuste impulsivo

------------------------------------------------------------------------

# 📌 Status Atual

✔ Pipeline automatizado funcional\
✔ Versionamento de estratégia ativo\
✔ Histórico auditável\
✔ Backtest automatizado\
✔ Otimização automatizada\
✔ Monitoramento de performance ativo\
✔ Sinal de recalibração ativo\
✔ Geração automática de imagens\
✔ Promoção manual de estratégia validada

Mega Engine --- Estatística aplicada, mensuração real e evolução
controlada.
