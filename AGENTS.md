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
6. `python -m core.backtest`
7. `python -m core.optimize`

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
- `out/performance_monitor.json`: leitura operacional da performance recente
- `out/recalibration_signal.json`: sinal de recalibracao

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
- avaliacao robusta via backtest fora da amostra
- Monte Carlo para stress test de parametros e sensibilidade
- atualizacao bayesiana para ajustar pesos e confianca
- monitoramento de drift e degradacao
- recalibracao controlada, nunca opaca

Nao introduzir "IA magica" ou heuristicas sem capacidade de explicacao minima e medicao objetiva.

## Regras Para Alteracoes

- Nao quebrar o contrato de `out/jogos_gerados.json` sem atualizar consumidores externos.
- Nao registrar resultado de concurso com snapshot errado.
- Nao promover configuracao nova sem evidencia em backtest ou monitoramento.
- Nao usar dado futuro em features, calibracao ou backtest.
- Nao trocar robustez por score aparente.
- Nao esconder falhas de prerequisito; preferir `skip` controlado quando a execucao nao for valida.

## Quando Mexer em Estrategia

Mudancas em `generator.py`, `features_megasena.py`, `backtest.py`, `optimize.py`, `monitor_performance.py` ou configuracoes relacionadas devem responder explicitamente:

- qual hipotese esta sendo testada
- como evitar vazamento temporal
- qual metrica define melhora real
- como reverter se piorar
- quais artefatos provam a decisao

## Validacao Minima

Antes de concluir mudancas relevantes, um agente deve tentar validar com o maximo possivel entre:

- `python3 -m core.compare_results`
- `python3 -m core.monitor_performance`
- `python3 -m core.backtest`
- `python3 -m core.optimize`
- `python3 -m py_compile core/*.py`

Quando houver acesso externo disponivel, tambem validar:

- `python3 -m core.ingest_megasena`

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
- `generate_images.yml`

## Futuro Desejado

O projeto deve caminhar para uma engine que aprende com os proprios resultados sem perder controle.

Isso significa:

- aprender com erro e acerto
- recalibrar pesos e parametros com disciplina estatistica
- manter historico suficiente para explicar qualquer decisao
- separar claramente experimentacao, recomendacao e promocao para producao

Se houver duvida entre uma solucao "mais inteligente" e uma solucao "mais auditavel", escolher a mais auditavel e medir antes de sofisticar.
