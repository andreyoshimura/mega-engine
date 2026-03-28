# AGENTS.md

Guia operacional para agentes de codigo trabalhando no `mega-engine`.

## Missao do Projeto

O objetivo principal deste projeto e construir uma engine cada vez mais inteligente para geracao e avaliacao de jogos da Mega-Sena.

O estado atual do projeto e um pipeline estatistico auditavel. A direcao desejada e evoluir essa base para uma estrategia que:

- use backtest walk-forward reproduzivel
- use simulacao de Monte Carlo para testar robustez
- incorpore inferencia bayesiana e atualizacao de crencas
- monitore os proprios erros e acertos
- recalibre parametros automaticamente com seguranca
- sirva como base para automacoes futuras

Regra central: inteligencia sem auditoria nao serve. Toda evolucao deve preservar rastreabilidade, reproducibilidade e capacidade de rollback.

## Fluxo Canonico

Ordem correta de producao:

1. `python -m core.ingest_megasena`
2. `python -m core.features_megasena`
3. `python -m core.generator`
4. `python -m core.compare_results`
5. `python -m core.monitor_performance`

Ordem correta de recalibracao profunda:

1. `python -m core.backtest`
2. `python -m core.optimize`
3. `python -m core.monitor_performance`
4. `python -m core.learning`

Nao inverter a ordem sem justificativa tecnica clara.

## Contratos Criticos

Arquivos canonicos:

- `data/results/megasena.csv`: historico oficial de resultados
- `data/last_result.json`: ultimo resultado conhecido
- `data/performance_log.jsonl`: historico de desempenho por concurso
- `data/model_history.jsonl`: historico de configuracoes e estrategia
- `out/jogos_gerados.json`: jogos correntes do concurso alvo
- `out/history/jogos_concurso_<n>.json`: snapshot imutavel por concurso
- `out/backtest_report.json`: avaliacao walk-forward
- `out/optimization_report.json`: ranking da busca de parametros
- `out/recommended_strategy_config.json`: proposta de configuracao promovivel
- `out/config_promotion_decision.json`: decisao da trava de promocao
- `out/performance_monitor.json`: leitura operacional da performance recente
- `out/recalibration_signal.json`: sinal de recalibracao
- `out/learning_decision.json`: decisao do pipeline de aprendizado
- `out/next_strategy_config.json`: proxima configuracao sugerida
- `data/config_promotion_log.jsonl`: historico de decisoes de promocao
- `data/learning_log.jsonl`: historico de decisoes de aprendizado

Se um agente alterar formato, nomes de campos ou semantica desses artefatos, deve tratar isso como mudanca de contrato.

## Prioridades de Engenharia

Ao propor ou implementar mudancas, priorizar nesta ordem:

1. integridade dos dados
2. reproducibilidade dos resultados
3. compatibilidade com workflows e automacoes
4. qualidade estatistica da estrategia
5. performance computacional

## O Que Agentes Devem Otimizar

Agentes devem favorecer mudancas que aproximem o projeto desta arquitetura:

- geracao guiada por features com peso explicavel
- features multi-janela (`freq_20`, `freq_50`, `freq_100`)
- sinal de atraso (`atraso_score`)
- avaliacao robusta via backtest fora da amostra
- Monte Carlo para stress test de parametros e sensibilidade
- atualizacao bayesiana para ajustar pesos e confianca
- monitoramento de drift e degradacao
- recalibracao controlada, nunca opaca
- regras estruturais de selecao de jogos (`bottom_pairs`, `max_seq`, `min_diff`, `penalty_weak_pair`)

Nao introduzir "IA magica" ou heuristicas sem capacidade de explicacao minima e medicao objetiva.

## Parametros Estrategicos Atuais

O estado atual da estrategia usa, no minimo, estas familias de parametros:

- pesos de features: `freq_20`, `freq_50`, `freq_100`, `atraso_score`, `bayes_mean`, `bayes_score`, `score_alpha`
- configuracao bayesiana: `alpha_prior`, `beta_prior`
- estrutura dos jogos: `ticket_size`, `num_games`, `max_intersection`
- regras estruturais: `bottom_pairs`, `max_seq`, `min_diff`, `penalty_weak_pair`
- limites de recalibracao: `backtest_history_limit`, `optimization_history_limit`, `backtest_n_sim`
- guardrails: `promotion_guard`, `learning`, `monitoring`

Se um agente mexer nesses grupos, deve considerar impacto em geracao, backtest, optimize, learning e workflows.

## Regras Para Alteracoes

- Nao quebrar o contrato de `out/jogos_gerados.json` sem atualizar consumidores externos.
- Nao registrar resultado de concurso com snapshot errado.
- Nao promover configuracao nova sem evidencia em backtest ou monitoramento.
- Nao usar dado futuro em features, calibracao ou backtest.
- Nao trocar robustez por score aparente.
- Nao esconder falhas de prerequisito; preferir `skip` controlado quando a execucao nao for valida.
- Nao aumentar custo computacional de workflows sem explicitar a contrapartida estatistica.
- Nao reavaliar historico completo por padrao em recalibracao pesada se houver limite recente configurado.

## Quando Mexer em Estrategia

Mudancas em `generator.py`, `features_megasena.py`, `backtest.py`, `optimize.py`, `monitor_performance.py` ou configuracoes relacionadas devem responder explicitamente:

- qual hipotese esta sendo testada
- como evitar vazamento temporal
- qual metrica define melhora real
- como reverter se piorar
- quais artefatos provam a decisao
- qual impacto computacional a mudanca cria em `backtest`, `optimize` e workflows

## Validacao Minima

Antes de concluir mudancas relevantes, um agente deve tentar validar com o maximo possivel entre:

- `python3 -m core.compare_results`
- `python3 -m core.monitor_performance`
- `python3 -m core.backtest`
- `python3 -m core.optimize`
- `python3 -m core.learning`
- `python3 -m py_compile core/*.py`

Quando houver acesso externo disponivel, tambem validar:

- `python3 -m core.ingest_megasena`

Quando mexer em score, geracao, backtest ou regras estruturais, tambem preferir:

- `python3 -m unittest tests.test_generator tests.test_features tests.test_backtest tests.test_learning tests.test_promotion tests.test_compare tests.test_monitor tests.test_ingest`

## Workflows

Os workflows em `.github/workflows/` fazem parte da operacao, nao sao acessorios.

Qualquer agente que mexa em:

- empacotamento
- paths de artefatos
- segredos
- ordem do pipeline
- contratos JSON

deve considerar impacto direto em:

- `daily_generate.yml`
- `compare_results.yml`
- `backtest.yml`
- `optimize.yml`
- `recalibration.yml`
- `recalibration_full.yml`
- `generate_images.yml`

Estado operacional esperado dos workflows:

- `Mega Daily Generate`: pipeline de producao
- `Compare Mega-Sena Results`: comparacao do resultado e monitoramento
- `Mega Recalibration Lite`: automatico, leve, roda `monitor_performance` + `learning`
- `Mega Recalibration Full`: manual, pesado, roda `backtest` + `optimize` + `monitor_performance` + `learning`
- `Mega Backtest`: manual, isolado
- `Mega Optimize`: manual, isolado

Regra pratica:

- nao colocar `optimize` pesado em cron automatico sem reduzir escopo ou justificar custo
- preferir `Lite` para vigilancia recorrente e `Full` para recalibracao sob demanda

## Futuro Desejado

O projeto deve caminhar para uma engine que aprende com os proprios resultados sem perder controle.

Isso significa:

- aprender com erro e acerto
- recalibrar pesos e parametros com disciplina estatistica
- manter historico suficiente para explicar qualquer decisao
- separar claramente experimentacao, recomendacao e promocao para producao

Se houver duvida entre uma solucao "mais inteligente" e uma solucao "mais auditavel", escolher a mais auditavel e medir antes de sofisticar.
