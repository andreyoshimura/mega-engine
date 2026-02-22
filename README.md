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


## 🎯 Objetivo
Evoluir a mega-engine de um gerador heurístico operacional para um sistema estatístico auditável, autoajustável e preparado para estratégias adaptativas.

---

## 🔵 Fase 2 — Estrutura Estatística e Evolução Controlada

### 🔹 Backtest Walk-Forward Automatizado
- Avaliação temporal fiel (treina no passado, testa no próximo concurso).
- Métricas:
  - média de acertos
  - taxa ≥4
  - taxa ≥5
  - max_hits médio
  - score estratégico
- Garantia de ausência de vazamento de dados futuros.

### 🔹 Módulo de Pesos Ajustáveis
- Estrutura configurável:
  - w20
  - w50
  - w100
  - w_delay
  - w_bayes
  - alpha_score
- Carregamento via JSON / ENV / CLI.
- Separação clara entre estatística e geração.

### 🔹 Penalização de Pares Fracos (1–60)
- Cálculo de coocorrência histórica.
- Identificação de bottom_k pares.
- Penalização no score do jogo.
- Regularização estrutural.

### 🔹 Diversidade Entre Jogos
- Restrição de diferença mínima (symmetric difference).
- Controle de concentração entre jogos.
- Melhor distribuição do portfólio.

### 🔹 Ajuste Automático de Pesos
- Random search / hill-climbing inicial.
- Seleção baseada em backtest walk-forward.
- Aplicação automática da melhor configuração.

### 🔹 Métrica Evolutiva de Estratégia
- Score composto e padronizado.
- Comparação histórica de performance.
- Monitoramento de estabilidade.

### 🔹 Guard Contra Regressão
- Nova estratégia só é aplicada se superar baseline.
- Prevenção de overfitting recente.
- Validação mínima de janela histórica.

### 🔹 Versionamento de Estratégia
- Registro automático em `data/model_history.jsonl`:
  - timestamp
  - janela usada
  - candidatos testados
  - score obtido
  - pesos aplicados
- Auditoria e rollback possíveis.

### 🔹 Modularização para Suportar Lotofácil
- Estrutura adaptável para múltiplas loterias.
- Separação de regras específicas por jogo.
- Núcleo estatístico reutilizável.

### 🔹 Dashboard Simplificado de Performance
- Resumo:
  - média móvel de acertos
  - taxa ≥4 / ≥5
  - max_hits
- Visualização simplificada para acompanhamento.

---

## 🟣 Fase 3 — Sistema Adaptativo e Estratégias Avançadas

### 🔹 Otimização Paramétrica Automática
- Exploração inteligente de hiperparâmetros.
- Evolução futura:
  - Bayesian Optimization
  - Simulated Annealing
  - CMA-ES

### 🔹 Estratégias Múltiplas Comparáveis
- Execução paralela de modelos distintos.
- Ranking por performance real.
- Portfólio de estratégias concorrentes.

### 🔹 Modelo Adaptativo com Aprendizado Baseado em Performance
- Ajuste dinâmico baseado em resultados recentes.
- Controle de estabilidade para evitar drift.
- Possível integração futura com ML supervisionado.

---

## 🧠 Meta Final

Transformar a mega-engine em:

- ✔ Estatisticamente estruturada  
- ✔ Autoajustável  
- ✔ Auditável  
- ✔ Versionada  
- ✔ Preparada para múltiplas loterias  
- ✔ Adaptativa e comparável entre estratégias  

---

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
## 📊 Nível Atual de Maturidade

**Estágio:** Operacional Estruturado (MVP Avançado)

A mega-engine encontra-se em um nível de maturidade onde:

✔ Pipeline automatizado estável (ingestão → geração → comparação → publicação)  
✔ Processamento determinístico e reprodutível  
✔ Logs persistentes e auditáveis (JSONL)  
✔ Integração completa com n8n (Telegram, Gmail, Instagram)  
✔ Estrutura modular preparada para expansão estatística  

### 🔎 Características Técnicas Atuais
- Modelo heurístico baseado em frequência histórica
- Geração automática de múltiplos jogos
- Comparação automática com resultados oficiais
- Registro histórico de performance
- Publicação multi-plataforma automatizada

### 🚧 Ainda Não Implementado (Planejado na Fase 2)
- Backtest walk-forward automatizado
- Otimização automática de pesos
- Penalização estrutural de pares fracos
- Diversidade controlada entre jogos
- Sistema adaptativo com aprendizado baseado em performance

---

### 🧠 Classificação de Maturidade

| Dimensão                  | Status |
|---------------------------|--------|
| Automação Operacional     | ✔ Alto |
| Observabilidade           | ✔ Alto |
| Modelagem Estatística     | ◑ Intermediário |
| Otimização Paramétrica    | ⬜ Não Implementado |
| Aprendizado Adaptativo    | ⬜ Não Implementado |

---

**Resumo:**  
O sistema é operacionalmente robusto e pronto para evolução estatística avançada.
Mega Engine — Estatística aplicada, mensuração real e evolução contínua.
