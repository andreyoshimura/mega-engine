# Mega Engine

Motor estatistico para geracao, comparacao, versionamento, backtest e monitoramento de estrategias da Mega-Sena.

O projeto nao tenta prever sorteios. O objetivo e operar um pipeline auditavel que gera jogos para os concursos, registra exatamente quais jogos foram enviados, compara os acertos apos a divulgacao oficial e preserva historico suficiente para automacoes externas, analise e recalibracao controlada.

------------------------------------------------------------------------

## Objetivo

A engine foi desenhada para:

- gerar jogos automaticamente nos dias de sorteio
- registrar resultados oficiais e comparar acertos por concurso
- preservar historico cumulativo e snapshots por concurso
- versionar a estrategia ativa e seus parametros
- executar backtests walk-forward reproduziveis
- otimizar parametros por grid search
- monitorar queda de desempenho e sinalizar recalibracao
- alimentar automacoes externas, incluindo n8n, Instagram e Telegram

------------------------------------------------------------------------

## Contrato com o n8n

O n8n depende de dois fluxos principais:

1. Antes do sorteio, ler [out/jogos_gerados.json](/media/msx/SD200/VSCODE/github/mega-engine/out/jogos_gerados.json) para enviar os jogos do concurso alvo.
2. Depois da divulgacao oficial, ler [data/performance_log.jsonl](/media/msx/SD200/VSCODE/github/mega-engine/data/performance_log.jsonl) para publicar resultado x acertos.

Para evitar comparacao com jogo errado, o projeto agora tambem grava snapshots imutaveis por concurso em [out/history](/media/msx/SD200/VSCODE/github/mega-engine/out/history), por exemplo [jogos_concurso_2987.json](/media/msx/SD200/VSCODE/github/mega-engine/out/history/jogos_concurso_2987.json).

Regra operacional importante:

- `out/jogos_gerados.json` representa o concurso alvo corrente
- `out/history/jogos_concurso_<n>.json` representa a fonte canonica para comparar o concurso `n`
- `core.compare_results` usa primeiro o snapshot do concurso; se ele nao existir e o arquivo corrente apontar para outro concurso, a execucao falha em vez de registrar um log incorreto

------------------------------------------------------------------------

## Estrutura

```text
mega-engine/
├── core/
│   ├── config.py
│   ├── ingest_megasena.py
│   ├── features_megasena.py
│   ├── generator.py
│   ├── compare_results.py
│   ├── versioning.py
│   ├── backtest.py
│   ├── optimize.py
│   ├── monitor_performance.py
│   ├── image_generator.py
│   └── audit_performance_log.py
├── configs/
│   └── strategy_config.json
├── data/
│   ├── results/megasena.csv
│   ├── features/dezenas.csv
│   ├── performance_log.jsonl
│   ├── model_history.jsonl
│   └── last_result.json
├── out/
│   ├── jogos_gerados.json
│   ├── history/
│   ├── backtest_report.json
│   ├── optimization_report.json
│   ├── recommended_strategy_config.json
│   ├── performance_monitor.json
│   ├── recalibration_signal.json
│   ├── performance_audit.json
│   └── images/
├── tests/
├── pyproject.toml
└── .github/workflows/
```

------------------------------------------------------------------------

## Fluxo Operacional

### 1. Daily Generate

Executa:

- `python -m core.ingest_megasena`
- `python -m core.features_megasena`
- `python -m core.generator`

Atualiza:

- [data/results/megasena.csv](/media/msx/SD200/VSCODE/github/mega-engine/data/results/megasena.csv)
- [data/features/dezenas.csv](/media/msx/SD200/VSCODE/github/mega-engine/data/features/dezenas.csv)
- [data/last_result.json](/media/msx/SD200/VSCODE/github/mega-engine/data/last_result.json)
- [out/jogos_gerados.json](/media/msx/SD200/VSCODE/github/mega-engine/out/jogos_gerados.json)
- [out/history](/media/msx/SD200/VSCODE/github/mega-engine/out/history)
- [data/model_history.jsonl](/media/msx/SD200/VSCODE/github/mega-engine/data/model_history.jsonl)

### 2. Compare Results

Executa:

- `python -m core.compare_results`
- `python -m core.monitor_performance`

Atualiza:

- [data/performance_log.jsonl](/media/msx/SD200/VSCODE/github/mega-engine/data/performance_log.jsonl)
- [out/performance_monitor.json](/media/msx/SD200/VSCODE/github/mega-engine/out/performance_monitor.json)
- [out/recalibration_signal.json](/media/msx/SD200/VSCODE/github/mega-engine/out/recalibration_signal.json)

### 3. Backtest

Executa:

- `python -m core.backtest`

Atualiza:

- [out/backtest_report.json](/media/msx/SD200/VSCODE/github/mega-engine/out/backtest_report.json)

### 4. Optimize

Executa:

- `python -m core.optimize`

Atualiza:

- [out/optimization_report.json](/media/msx/SD200/VSCODE/github/mega-engine/out/optimization_report.json)
- [out/recommended_strategy_config.json](/media/msx/SD200/VSCODE/github/mega-engine/out/recommended_strategy_config.json)

### 5. Image Generation

Executa:

- `python -m core.image_generator`

Atualiza:

- [out/images/mega_atual.png](/media/msx/SD200/VSCODE/github/mega-engine/out/images/mega_atual.png)
- [out/images/mega_semana_*.png](/media/msx/SD200/VSCODE/github/mega-engine/out/images)

------------------------------------------------------------------------

## Horarios e Datas dos Sorteios

A referencia operacional e a data local de `America/Sao_Paulo`.

A Mega-Sena roda nas datas locais de sorteio:

- terca
- quinta
- sabado

Os workflows foram documentados para seguir essa regra local.

Tabela operacional:

- [daily_generate.yml](/media/msx/SD200/VSCODE/github/mega-engine/.github/workflows/daily_generate.yml)
  horario local: `03:00` nas `tercas`, `quintas` e `sabados`
  cron GitHub em UTC: `0 6 * * 2,4,6`
- [compare_results.yml](/media/msx/SD200/VSCODE/github/mega-engine/.github/workflows/compare_results.yml)
  polling local em janela de resultado:
  `19:05`, `19:35`, `20:05`, `20:35`, `21:05`, `21:35`, `22:05`, `22:35`, `23:05`, `23:35`, `00:05`, `00:35`, `01:05`, `01:35`
  cron GitHub em UTC:
  `5,35 22,23 * * 2,4,6`
  `5,35 0-4 * * 3,5,0`
- [recalibration.yml](/media/msx/SD200/VSCODE/github/mega-engine/.github/workflows/recalibration.yml)
  horario local: `01:30` de `segunda-feira`
  cron GitHub em UTC: `30 4 * * 1`
- [generate_images.yml](/media/msx/SD200/VSCODE/github/mega-engine/.github/workflows/generate_images.yml)
  horario local: `06:00` de `domingo`
  cron GitHub em UTC: `0 9 * * 0`
- [backtest.yml](/media/msx/SD200/VSCODE/github/mega-engine/.github/workflows/backtest.yml)
  execucao manual, sem cron
- [optimize.yml](/media/msx/SD200/VSCODE/github/mega-engine/.github/workflows/optimize.yml)
  execucao manual, sem cron
- [recalibration_full.yml](/media/msx/SD200/VSCODE/github/mega-engine/.github/workflows/recalibration_full.yml)
  execucao manual, sem cron

Regra mental para converter:

- o cron do GitHub Actions e sempre em UTC
- para este projeto, pensar em `UTC = America/Sao_Paulo + 3h`
- exemplo:
  `03:00` local = `06:00` UTC
  `19:05` local = `22:05` UTC
  `23:35` local = `02:35` UTC do dia seguinte
  `01:30` local = `04:30` UTC

Regra de manutencao:

- sempre adicionar comentarios nos workflows explicando o horario local em `America/Sao_Paulo`
- sempre documentar no proprio YAML a conversao entre horario local e cron UTC
- sempre preferir guardrails por data local e janela local em vez de depender de um unico horario fixo

------------------------------------------------------------------------

## Estrategia Atual

Configuracao promovida em [strategy_config.json](/media/msx/SD200/VSCODE/github/mega-engine/configs/strategy_config.json):

- `ticket_size = 9`
- `num_games = 6`
- `window = 100`
- `min_history = 100`
- `max_intersection = 3`
- `backtest_n_sim = 20`

Monitoramento:

- `recent_window = 5`
- `baseline_window = 20`
- `min_draws_required = 12`
- `score_drop_ratio = 0.5`
- `max_hits_drop_ratio = 0.85`
- `ge4_drop_ratio = 0.5`

Grid de otimizacao:

- `window = [50, 100, 150]`
- `num_games = [4, 5, 6]`
- `max_intersection = [3, 4, 5]`

------------------------------------------------------------------------

## Auditoria e Versionamento

Cada execucao de producao registra estrategia e parametros em [data/model_history.jsonl](/media/msx/SD200/VSCODE/github/mega-engine/data/model_history.jsonl).

O historico de acertos fica em [data/performance_log.jsonl](/media/msx/SD200/VSCODE/github/mega-engine/data/performance_log.jsonl).

A auditoria do log pode ser refeita com:

```bash
python -m core.audit_performance_log
```

Esse comando:

- reconcilia o log com os snapshots por concurso
- reaplica o snapshot correto quando houver `git_sha` historico
- recalcula `hits`, `hist_hits_count`, `score` e metadados derivados
- gera [out/performance_audit.json](/media/msx/SD200/VSCODE/github/mega-engine/out/performance_audit.json)

------------------------------------------------------------------------

## Instalacao

```bash
python -m pip install --upgrade pip
pip install .
```

Para desenvolvimento local:

```bash
python -m unittest discover -s tests -v
```

------------------------------------------------------------------------

## Validacao Operacional

Validacao local executada com sucesso:

- `python3 -m unittest discover -s tests -v`
- `python3 -m py_compile core/*.py tests/*.py`
- `python3 -m core.features_megasena`
- `python3 -m core.generator`
- `python3 -m core.compare_results`
- `python3 -m core.monitor_performance`
- `python3 -m core.backtest`
- `python3 -m core.optimize`
- `python3 -m core.audit_performance_log`

Limitacoes da validacao local:

- `core.ingest_megasena` depende de API externa
- `core.image_generator` depende de `OPENAI_API_KEY`

------------------------------------------------------------------------

## Estado Atual

Concluido:

- pipeline automatizado funcional
- snapshots por concurso para blindar comparacao
- historico auditavel e reprocessavel
- backtest automatizado
- otimizacao automatizada
- monitoramento ativo
- workflows do GitHub Actions alinhados ao horario local dos sorteios
- integracao preparada para n8n, Instagram e Telegram

Proximos passos naturais:

- recalibracao controlada via workflow dedicado
- champion/challenger formal
- enriquecimento de features e score composto
- documentacao operacional complementar para n8n
