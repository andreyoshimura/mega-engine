# 🎯 Mega Engine

Motor estatístico automatizado para geração, avaliação, versionamento
estratégico e publicação de jogos da Mega-Sena.

O projeto não busca prever resultados, mas construir um sistema:

-   Auditável
-   Mensurável
-   Determinístico
-   Operacionalmente estável
-   Versionado

------------------------------------------------------------------------

# 📌 Objetivo

Criar uma engine modular que:

-   Gere jogos automaticamente (9 dezenas por jogo)
-   Registre resultados oficiais automaticamente
-   Calcule acertos por concurso
-   Preserve histórico cumulativo
-   Versione automaticamente cada estratégia utilizada
-   Gere imagens institucionais automaticamente
-   Integre com automações (n8n, Telegram, Instagram)

Foco principal:

> Maximizar qualidade estatística e medir desempenho real ao longo do
> tempo.

------------------------------------------------------------------------

# ⚙️ Arquitetura

``` bash
mega-engine/
├── core/
│   ├── generator.py              # Geração dos jogos
│   ├── compare_results.py        # Comparação com resultado oficial
│   ├── image_generator.py        # Geração automática de imagens (IA)
│   ├── ingest_megasena.py        # Ingestão de resultados
│   ├── features_megasena.py      # Engenharia de features
│   ├── versioning.py             # Registro automático de estratégia
│   ├── optimize.py               # (reservado)
│   └── backtest.py               # (reservado)
│
├── configs/
│   └── strategy_config.json      # Configuração ativa da estratégia
│
├── data/
│   ├── performance_log.jsonl     # Histórico cumulativo (append-only)
│   ├── model_history.jsonl       # Histórico de estratégias (append-only)
│   └── last_result.json          # Último resultado oficial
│
├── out/
│   ├── jogos_gerados.json        # Jogos do dia (sobrescrito)
│   └── images/
│       ├── mega_atual.png        # Imagem usada na automação
│       └── mega_semana_X.png     # Histórico semanal versionado
│
└── .github/workflows/
    ├── daily_generate.yml
    ├── compare_results.yml
    └── generate_images.yml
```

------------------------------------------------------------------------

# 🔄 Fluxo de Produção

## 1️⃣ Daily Generate

Executa:

-   ingest_megasena.py\
-   features_megasena.py\
-   generator.py\
-   register_strategy()

Atualiza:

-   out/jogos_gerados.json
-   data/model_history.jsonl

------------------------------------------------------------------------

## 2️⃣ Compare Results

-   Consulta API oficial
-   Calcula acertos
-   Atualiza:
    -   data/last_result.json
    -   data/performance_log.jsonl

------------------------------------------------------------------------

## 3️⃣ Image Workflow (IA)

Executa:

-   image_generator.py

Gera:

-   1024x1024 otimizado para Instagram
-   Tema visual rotativo por semana
-   Headline variável
-   Identidade institucional consistente

Atualiza:

-   out/images/mega_atual.png (sempre sobrescreve)
-   out/images/mega_semana\_{ISO_WEEK}.png (histórico preservado)

Commit automático apenas se houver alteração real.

------------------------------------------------------------------------

# 🖼️ Estratégia de Imagens

Características:

-   Formato 1:1 (Instagram ready)
-   Tema rotativo semanal
-   Headline variável:
    -   Análise de Padrões
    -   Estratégia Numérica
    -   Probabilidade Aplicada
-   Sem apelo a prêmio
-   Sem promessa
-   Sem linguagem de urgência

Objetivo: posicionamento institucional e analítico.

------------------------------------------------------------------------

# 🧠 Versionamento de Estratégia (Implementado)

Toda execução de produção registra automaticamente:

``` json
{
  "timestamp": "...",
  "execution_type": "production",
  "strategy_name": "...",
  "model_version": "...",
  "parameters": {...},
  "config_hash": "...",
  "commit_sha": "..."
}
```

Arquivo:

data/model_history.jsonl

Garantias:

-   Append-only
-   Não duplica hash
-   Resiliente a falhas
-   Auditoria completa
-   Integração automática com GitHub Actions

Validação realizada:

✔ Configuração idêntica não duplica\
✔ Configuração alterada gera novo registro\
✔ Pipeline estável

------------------------------------------------------------------------

# 📊 Métricas Registradas

Por concurso:

-   max_hits
-   count_ge4
-   count_ge5
-   count_eq6
-   score ponderado
-   histograma de distribuição
-   lista completa de jogos

Arquivo:

data/performance_log.jsonl

------------------------------------------------------------------------

# 🚀 Roadmap

## 🔵 Fase 2 --- Estrutura Estatística

-   Backtest Walk-Forward Automatizado
-   Módulo de Pesos Ajustáveis
-   Penalização de Pares Fracos
-   Diversidade Controlada Entre Jogos
-   Ajuste Automático de Pesos
-   Dashboard Simplificado de Performance

## 🟣 Fase 3 --- Sistema Adaptativo

-   Estratégias múltiplas comparáveis
-   Otimização paramétrica automática
-   Modelo adaptativo baseado em performance
-   Guard contra regressão estatística

------------------------------------------------------------------------

# 📌 Status Atual

✔ Geração automática funcional\
✔ Comparação automática funcional\
✔ Histórico cumulativo preservado\
✔ Versionamento de estratégia implementado\
✔ Automação de imagens via IA\
✔ Integração pronta para n8n\
✔ Pipeline estável

------------------------------------------------------------------------

# ⚠️ Aviso

A Mega-Sena é um sistema de probabilidade combinatória com sorteios
independentes.

Este projeto não promete previsão de resultados nem vantagem matemática
garantida.

O objetivo é construir um sistema estatístico auditável e
operacionalmente consistente.
