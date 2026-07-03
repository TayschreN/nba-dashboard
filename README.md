# EDA — NBA Regular Season (2010–2024)

Análise exploratória de 14 temporadas e 33.316 linhas time-por-jogo da NBA (~16.658 jogos), orientada a 10 perguntas de negócio. Projeto de portfólio focado em storytelling analítico: cada seção parte de uma pergunta, testa uma hipótese nos dados e termina em um insight acionável — inclusive quando o dado contraria a narrativa esperada.

![Dashboard](tela1.png)
![Dashboard](tela2.png)
![Dashboard](tela3.png)


## Perguntas respondidas

1. A vantagem de jogar em casa ainda existe na NBA?
2. A "revolução das bolas de 3" é real nos números, ou é só narrativa de mídia?
3. O jogo ficou mais rápido e mais pontuado ao longo da década?
4. Jogar em back-to-back (sem descanso) prejudica o desempenho?
5. Turnovers matam: qual a força da relação entre erros de bola e resultado?
6. Quais times foram mais dominantes na década?
7. Os jogos estão mais equilibrados ou mais teve "sova" ao longo do tempo?
8. Dentre todas as estatísticas de box score, qual mais separa vitória de derrota?
9. Eficiência de arremesso importa mais que volume?
10. A defesa ativa (roubos + tocos) aumentou ou diminuiu na era do 3 pontos?

## Principais insights

- A vantagem do mandante cai de forma gradual ao longo da década (de ~60% para ~54% de vitórias), tendência estrutural mais ampla que um efeito pontual de pandemia.
- A revolução das bolas de 3 é real: tentativas por jogo quase dobraram, sem perda de eficiência — não é exagero de narrativa esportiva.
- O aumento de pontos por jogo é efeito colateral direto da revolução do 3, não de mudança de regulamento.
- Back-to-backs reduzem a taxa de vitória em ~7 pontos percentuais — fator de ajuste real para apostas/fantasy, não anedota.
- Eficiência de arremesso (FG%) correlaciona muito mais com vitória do que volume de tentativas — otimizar qualidade importa mais que "chover" bola.
- Contraintuitivo: roubos e tocos por jogo se mantiveram estáveis na década, apesar da transformação radical do ataque — a defesa provavelmente se reposicionou, não mudou de volume.

## Dados

Fonte: [NocturneBear/NBA-Data-2010-2024](https://github.com/NocturneBear/NBA-Data-2010-2024) (GitHub, domínio público, extraído via stats.nba.com). Cobre temporada regular, 2010-11 a 2023-24.

**Limitações declaradas:** dataset não inclui playoffs nem eras anteriores a 2010; correlação não implica causalidade (especialmente nos insights de turnovers e correlação com vitória); o efeito de back-to-back não controla força do adversário.

## Estrutura do projeto

```
nba-eda/
├── data/
│   └── regular_season_totals_2010_2024.csv
├── images/
│   └── *.png              (10 gráficos exportados)
├── nba_eda.ipynb           (notebook completo, já executado)
├── requirements.txt
└── README.md
```

## Como rodar

```bash
pip install -r requirements.txt
jupyter notebook nba_eda.ipynb
```

## Stack

Python · pandas · matplotlib · seaborn · Jupyter

---
*Projeto de portfólio — parte da preparação para vaga de estágio em Dados.*
