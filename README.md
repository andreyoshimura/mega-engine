# 🎯 Mega Engine

Motor estatístico automatizado para geração e avaliação de jogos da Mega-Sena.

O objetivo do projeto não é prever resultados, mas construir um sistema auditável, mensurável e evolutivo para geração de combinações com base estatística, mantendo histórico completo de performance.

---

# 📌 Objetivo

Criar uma engine modular que:

- Gere jogos automaticamente (9 dezenas por jogo)
- Registre resultados oficiais automaticamente
- Calcule acertos por concurso
- Preserve histórico cumulativo
- Permita evolução futura com otimização e ML
- Integre facilmente com automações (n8n, Telegram, redes sociais)

Foco principal:

> Maximizar qualidade estatística e medir desempenho real ao longo do tempo.

---

# ⚙️ Arquitetura

```
mega-engine/
│
├── core/
│   ├── generator.py            # Geração dos jogos
│   ├── compare_results.py      # Comparação com resultado oficial
│   └── backtest.py             # (evolução futura)
│
├── out/
│   └── jogos_gerados.json      # Jogos do dia (sobrescrito)
│
├── data/
│   ├── performance_log.jsonl   # Histórico cumulativo (append-only)
│   └── last_result.json        # Último resultado oficial
│
└── .github/workflows/
    ├── generate.yml
    └── compare_results.yml
```

---

# 🔄 Fluxo de Produção

## 1️⃣ Generate Workflow

- Executa `generator.py`
- Gera jogos do dia
- Atualiza `out/jogos_gerados.json`

## 2️⃣ Compare Workflow

- Consulta API oficial da Mega-Sena
- Executa `compare_results.py`
- Calcula acertos
- Atualiza:
  - `data/last_result.json`
  - `data/performance_log.jsonl`

## 3️⃣ Automação Externa (n8n)

Consome via `raw.githubusercontent.com`:

- Jogos do dia
- Resultado oficial
- Performance do concurso

---

# 📊 Métricas Registradas

Para cada concurso:

- `max_hits`
- `count_ge4`
- `count_ge5`
- `count_eq6`
- `score` ponderado
- Histograma de distribuição de acertos
- Lista completa de jogos com hits individuais

---

# 🔐 Preservação de Histórico

O sistema foi projetado para nunca perder dados históricos.

## Garantias

- `performance_log.jsonl` é append-only
- Não há sobrescrita de concursos anteriores
- Cada concurso é registrado apenas uma vez
- Histórico versionado pelo Git
- Auditoria completa e rastreável

Isso permite:

- Backtests futuros
- Métrica evolutiva real
- Comparação entre versões do modelo
- Transparência total

---

# 🧠 Modelo Atual

O modelo atual utiliza:

- Amostragem estatística
- Critérios estruturais
- Controle de interseção
- Validação rígida de integridade dos jogos

Cada jogo:

- Contém exatamente 9 dezenas
- Intervalo válido: 1–60
- Sem repetição
- Validado antes da publicação

---

# 🔎 Validação Automática

O sistema valida:

- Integridade do JSON
- Tamanho do jogo
- Tamanho do sorteio
- Intervalo permitido
- Duplicidade
- Repetição de concursos

Falhas interrompem o workflow.

---

# 📡 API Oficial Utilizada

Resultados consultados via:

```
https://loteriascaixa-api.herokuapp.com/api/megasena/latest
```

---

# 🚀 Próximos Passos (Roadmap)

Fase 2:

- Backtest walk-forward automatizado
- Ajuste automático de pesos
- Métrica evolutiva de estratégia
- Guard contra regressão
- Versionamento de estratégia
- Modularização para suportar Lotofácil
- Dashboard simplificado de performance

Fase 3:

- Otimização paramétrica automática
- Estratégias múltiplas comparáveis
- Modelo adaptativo com aprendizado baseado em performance

---

# 🎛 Princípios do Projeto

- Estatística > Achismo
- Métrica > Intuição
- Histórico > Memória manual
- Automação > Operação manual
- Reprodutibilidade > Aleatoriedade não controlada

---

# ⚠️ Aviso Importante

Este projeto não promete previsão de resultados nem vantagem matemática garantida.

A Mega-Sena é um sistema de probabilidade combinatória com sorteios independentes.

O objetivo é construir um sistema mensurável, automatizado e evolutivo para análise estatística.

---

# 📌 Status Atual

✔ Geração automática funcional  
✔ Comparação automática funcional  
✔ Histórico preservado  
✔ Integração pronta para n8n  
✔ Arquitetura modular  
✔ Pronto para evolução  

---

Mega Engine — Estatística aplicada, mensuração real e evolução contínua.
