# NBA Dashboard — Dash + Plotly

Dashboard interativo da temporada regular da NBA (2010–2024), construído com [Dash](https://dash.plotly.com/) e Plotly. Complementa o [EDA em notebook](../nba_eda.ipynb) do mesmo projeto.

## Funcionalidades

- **Filtros:** intervalo de temporadas (slider) e seleção de times (multi-select, opcional)
- **KPIs dinâmicos:** jogos no período, média de pontos/time, % de vitórias em casa, melhor aproveitamento, maior pontuação em um jogo
- **Insights automáticos:** até 8 insights gerados dinamicamente, comparando o período/seleção atual com a média histórica da base completa — incluindo efeito de back-to-back, correlação de cada estatística com vitória, e evolução do arremesso de 3
- **8 gráficos interativos:**
  - Vantagem de jogar em casa, por temporada
  - Evolução do arremesso de 3 pontos (tentativas + % de acerto)
  - Pontos por jogo ao longo do tempo
  - Efeito do back-to-back na taxa de vitória
  - Ranking de times por % de vitórias (adapta ao filtro de times)
  - O que mais correlaciona com vitória (ranking de estatísticas)
  - Turnovers: vitórias vs. derrotas
  - Defesa ativa (roubos + tocos) ao longo do tempo

Todos os componentes reagem em tempo real aos filtros.

## Como rodar localmente

```bash
pip install -r requirements.txt
python app.py
```

Depois abra **http://127.0.0.1:8050** no navegador.

## Como fazer deploy (Render)

```
Build command: pip install -r requirements.txt
Start command: gunicorn app:server   (já configurado no Procfile)
```

## Estrutura

```
dashboard/
├── app.py
├── assets/
│   └── custom.css
├── data/
│   └── regular_season_totals_2010_2024.csv
├── requirements.txt
├── Procfile
└── README.md
```

## Stack

Python · Dash · Plotly · dash-bootstrap-components · pandas · gunicorn

---
*Projeto de portfólio — parte da preparação para vaga de estágio em Dados.*
