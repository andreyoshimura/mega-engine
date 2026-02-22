# 🎯 Mega Engine

Motor estatístico automatizado para geração, avaliação e publicação
estratégica de jogos da Mega-Sena.

O objetivo do projeto não é prever resultados, mas construir um sistema
auditável, mensurável e evolutivo para geração de combinações com base
estatística, mantendo histórico completo de performance e identidade
visual automatizada.

------------------------------------------------------------------------

# 📌 Objetivo

Criar uma engine modular que:

-   Gere jogos automaticamente (9 dezenas por jogo)
-   Registre resultados oficiais automaticamente
-   Calcule acertos por concurso
-   Preserve histórico cumulativo
-   Gere imagens institucionais automaticamente
-   Permita evolução futura com otimização e ML
-   Integre facilmente com automações (n8n, Telegram, redes sociais)

Foco principal:

> Maximizar qualidade estatística, mensurar desempenho real e manter
> consistência operacional.

------------------------------------------------------------------------
# ⚙️ Arquitetura

mega-engine/
├── core/
│   ├── generator.py              # Geração dos jogos
│   ├── compare_results.py        # Comparação com resultado oficial
│   ├── image_generator.py        # Geração automática de imagens (IA)
│   ├── ingest_megasena.py        # Ingestão de resultados
│   ├── features_megasena.py      # Engenharia de features
│   ├── optimize.py               # Otimização (futuro)
│   └── backtest.py               # Backtests (futuro)
│
├── data/
│   ├── performance_log.jsonl     # Histórico cumulativo (append-only)
│   └── last_result.json          # Último resultado oficial
│
├── out/
│   ├── jogos_gerados.json        # Jogos do dia (sobrescrito)
│   └── images/
│       ├── mega_atual.png        # Imagem usada na automação
│       └── mega_semana_X.png     # Histórico semanal versionado
│
└── .github/workflows/
    ├── daily_generate.yml        # Geração diária de jogos
    ├── compare_results.yml       # Comparação automática
    └── generate_images.yml       # Geração semanal de imagem

------------------------------------------------------------------------

# 🔄 Fluxo de Produção

## 1️⃣ Generate Workflow

-   Executa `generator.py`
-   Gera jogos do dia
-   Atualiza `out/jogos_gerados.json`

## 2️⃣ Compare Workflow

-   Consulta API oficial da Mega-Sena
-   Executa `compare_results.py`
-   Calcula acertos
-   Atualiza:
    -   `data/last_result.json`
    -   `data/performance_log.jsonl`

## 3️⃣ Image Workflow (IA)

-   Executa `image_generator.py`
-   Gera imagem 1024x1024 pronta para Instagram
-   Atualiza sempre:
    -   `out/images/mega_atual.png`
-   Mantém histórico semanal:
    -   `out/images/mega_semana_{semana_iso}.png`
-   Commit automático apenas se houver alteração real

## 4️⃣ Automação Externa (n8n)

Consome via `raw.githubusercontent.com`: - Jogos do dia - Resultado
oficial - Performance do concurso - Imagem atual institucional

------------------------------------------------------------------------

# 🖼️ Automação de Imagens

O sistema gera automaticamente uma arte institucional semanal para a
Mega-Sena.

### Estratégia Visual

-   Formato 1024x1024 (ideal para Instagram)
-   Tema visual rotativo por semana
-   Headline variada automaticamente
-   Estética analítica e institucional
-   Identidade visual consistente

### Arquivos Gerados

out/images/mega_atual.png\
out/images/mega_semana_X.png

------------------------------------------------------------------------

# 📊 Métricas Registradas

Para cada concurso: - max_hits - count_ge4 - count_ge5 - count_eq6 -
score ponderado - Histograma de distribuição de acertos - Lista completa
de jogos com hits individuais

------------------------------------------------------------------------

# 🔐 Preservação de Histórico

-   performance_log.jsonl é append-only
-   Não há sobrescrita de concursos anteriores
-   Histórico versionado pelo Git
-   Auditoria completa e rastreável

------------------------------------------------------------------------

# 🚀 Roadmap

## Fase 2

-   Backtest Walk-Forward Automatizado
-   Módulo de Pesos Ajustáveis
-   Penalização de Pares Fracos
-   Diversidade Entre Jogos
-   Ajuste Automático de Pesos
-   Versionamento de Estratégia
-   Dashboard Simplificado

## Fase 3

-   Otimização Paramétrica Automática
-   Estratégias Múltiplas Comparáveis
-   Modelo Adaptativo baseado em Performance

------------------------------------------------------------------------

# 📌 Status Atual

✔ Geração automática funcional\
✔ Comparação automática funcional\
✔ Histórico preservado\
✔ Automação de imagens via IA\
✔ Integração pronta para n8n\
✔ Arquitetura modular

------------------------------------------------------------------------

# ⚠️ Aviso

Este projeto não promete previsão de resultados nem vantagem matemática
garantida.

Mega Engine --- Estatística aplicada, mensuração real e evolução
contínua.
