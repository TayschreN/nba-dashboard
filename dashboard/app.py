"""
Dashboard interativo — NBA Regular Season (2010-2024)
Autor: Gabriel

Rodar localmente:
    pip install -r requirements.txt
    python app.py
Depois abrir http://127.0.0.1:8050
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc

# ------------------------------------------------------------------
# 1. Carregamento e preparação dos dados
# ------------------------------------------------------------------

df = pd.read_csv('data/regular_season_totals_2010_2024.csv')
df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])
df['season_start'] = df['SEASON_YEAR'].str[:4].astype(int)
df['is_home'] = df['MATCHUP'].str.contains('vs.')
df['win'] = (df['WL'] == 'W').astype(int)
df['adversario'] = df['MATCHUP'].str.split(' ').str[-1]

# Descanso / back-to-back: calculado sobre a base inteira (não filtrada),
# pois depende do jogo anterior de cada time, que pode ficar fora do recorte filtrado.
df = df.sort_values(['TEAM_ABBREVIATION', 'GAME_DATE']).copy()
df['dias_descanso'] = df.groupby('TEAM_ABBREVIATION')['GAME_DATE'].diff().dt.days - 1
df['back_to_back'] = df['dias_descanso'] == 0

SEASON_MIN, SEASON_MAX = int(df['season_start'].min()), int(df['season_start'].max())

# Mapas de nome <-> sigla do time
TEAM_NOME_MAP = df.drop_duplicates('TEAM_ABBREVIATION').set_index('TEAM_ABBREVIATION')['TEAM_NAME'].to_dict()
LISTA_TIMES = sorted(TEAM_NOME_MAP.items(), key=lambda kv: kv[1])  # [(sigla, nome), ...] ordenado por nome

# Baselines históricos (base completa, sem filtro) — usados para comparação nos insights
HIST_PTS_MEDIA = df['PTS'].mean()
HIST_HOME_WIN_PCT = df[df['is_home']]['win'].mean() * 100
HIST_FG3A_MEDIA = df['FG3A'].mean()
HIST_FG3_PCT_MEDIA = df['FG3_PCT'].mean() * 100
HIST_TOV_MEDIA = df['TOV'].mean()

CORES = {
    'azul': '#1d428a',
    'vermelho': '#c9082a',
    'cinza': '#8a8f8d',
    'dourado': '#d4a017',
}

TEMPLATE_PLOTLY = 'plotly_white'

# Configuração da barra de ferramentas: habilita o botão de câmera (download)
# em todos os gráficos. Sem height/width fixos, o PNG exportado sai no
# tamanho original em que o gráfico está renderizado na tela (sem distorcer).
CONFIG_DOWNLOAD = {
    'displayModeBar': True,
    'displaylogo': False,
    'modeBarButtonsToRemove': ['zoom2d', 'pan2d', 'select2d', 'lasso2d',
                                'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d'],
    'toImageButtonOptions': {
        'format': 'png',
        'filename': 'grafico_nba',
        'scale': 2,
    },
}

STATS_CORRELACAO = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'FG3M', 'FG_PCT', 'FG3_PCT', 'FT_PCT']
NOMES_STATS = {
    'PTS': 'Pontos', 'REB': 'Rebotes', 'AST': 'Assistências', 'STL': 'Roubos',
    'BLK': 'Tocos', 'TOV': 'Turnovers', 'FG3M': 'Cestas de 3 convertidas',
    'FG_PCT': 'Aproveitamento geral (FG%)', 'FG3_PCT': 'Aproveitamento de 3 (FG3%)',
    'FT_PCT': 'Aproveitamento de lance livre (FT%)',
}


# ------------------------------------------------------------------
# 2. Funções de cálculo (separadas do callback para permitir testes diretos)
# ------------------------------------------------------------------

def filtrar_dados(season_range, times_selecionados):
    ini, fim = season_range
    df_f = df[(df['season_start'] >= ini) & (df['season_start'] <= fim)].copy()
    if times_selecionados:
        df_f = df_f[df_f['TEAM_ABBREVIATION'].isin(times_selecionados)]
    return df_f


def calcular_kpis(df_f):
    total_linhas = len(df_f)
    jogos_unicos = df_f['GAME_ID'].nunique()
    if total_linhas == 0:
        return {
            'jogos': 0, 'media_pts': 0, 'pct_mandante': 0,
            'melhor_time': '—', 'melhor_time_pct': 0, 'maior_pontuacao': '—'
        }

    media_pts = df_f['PTS'].mean()
    linhas_casa = df_f[df_f['is_home']]
    pct_mandante = linhas_casa['win'].mean() * 100 if len(linhas_casa) else 0

    ranking = df_f.groupby('TEAM_ABBREVIATION').agg(jogos=('win', 'count'), vitorias=('win', 'sum'))
    min_jogos = max(5, int(ranking['jogos'].max() * 0.15)) if len(ranking) else 5
    elegiveis = ranking[ranking['jogos'] >= min_jogos].copy()
    if len(elegiveis):
        elegiveis['pct'] = elegiveis['vitorias'] / elegiveis['jogos'] * 100
        sigla_melhor = elegiveis['pct'].idxmax()
        melhor_time = TEAM_NOME_MAP.get(sigla_melhor, sigla_melhor)
        melhor_time_pct = elegiveis['pct'].max()
    else:
        melhor_time, melhor_time_pct = '—', 0

    idx_max_pts = df_f['PTS'].idxmax()
    linha_max = df_f.loc[idx_max_pts]
    maior_pontuacao = f"{linha_max['TEAM_ABBREVIATION']} {int(linha_max['PTS'])} pts (vs {linha_max['adversario']})"

    return {
        'jogos': jogos_unicos,
        'media_pts': round(media_pts, 1),
        'pct_mandante': round(pct_mandante, 1),
        'melhor_time': melhor_time,
        'melhor_time_pct': round(melhor_time_pct, 1),
        'maior_pontuacao': maior_pontuacao,
    }


def fig_mando_casa(df_f):
    if len(df_f) == 0:
        return go.Figure()
    linhas_casa = df_f[df_f['is_home']]
    if len(linhas_casa) == 0:
        return go.Figure()
    tab = linhas_casa.groupby('season_start')['win'].mean() * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=tab.index, y=tab.values, mode='lines+markers',
                              line=dict(color=CORES['vermelho'], width=3), marker=dict(size=7),
                              name='% vitória em casa'))
    fig.add_hline(y=50, line_dash='dash', line_color='#b0b0b0',
                  annotation_text='Equilíbrio (50%)', annotation_font_size=10)
    fig.update_layout(template=TEMPLATE_PLOTLY, margin=dict(l=10, r=10, t=10, b=10),
                       height=300, yaxis_title='% de vitórias em casa', xaxis_title=None)
    return fig


def fig_evolucao_tres(df_f):
    if len(df_f) == 0:
        return go.Figure()
    tab = df_f.groupby('season_start').agg(fg3a=('FG3A', 'mean'), fg3_pct=('FG3_PCT', 'mean'))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=tab.index, y=tab['fg3a'], mode='lines+markers', name='Tentativas de 3/jogo',
                              line=dict(color=CORES['azul'], width=3), marker=dict(size=6), yaxis='y1'))
    fig.add_trace(go.Scatter(x=tab.index, y=tab['fg3_pct'] * 100, mode='lines+markers', name='% de acerto',
                              line=dict(color=CORES['vermelho'], width=3, dash='dash'), marker=dict(size=6), yaxis='y2'))
    fig.update_layout(template=TEMPLATE_PLOTLY, margin=dict(l=10, r=10, t=10, b=10),
                       height=300, xaxis_title=None,
                       yaxis=dict(title='Tentativas de 3 por jogo'),
                       yaxis2=dict(title='% de acerto', overlaying='y', side='right', showgrid=False),
                       legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0))
    return fig


def fig_pontos_por_ano(df_f):
    if len(df_f) == 0:
        return go.Figure()
    media = df_f.groupby('season_start')['PTS'].mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=media.index, y=media.values, mode='lines+markers',
                              line=dict(color=CORES['azul'], width=3), marker=dict(size=7)))
    fig.add_hline(y=HIST_PTS_MEDIA, line_dash='dash', line_color='#b0b0b0',
                  annotation_text=f'Média histórica: {HIST_PTS_MEDIA:.1f}', annotation_font_size=10)
    fig.update_layout(template=TEMPLATE_PLOTLY, margin=dict(l=10, r=10, t=10, b=10),
                       height=300, yaxis_title='Pontos por jogo (por time)', xaxis_title=None)
    return fig


def fig_back_to_back(df_f):
    if len(df_f) == 0:
        return go.Figure()
    validos = df_f.dropna(subset=['dias_descanso'])
    validos = validos[validos['dias_descanso'] >= 0]
    if len(validos) == 0:
        return go.Figure()

    win_b2b = validos[validos['back_to_back']]['win'].mean() * 100 if validos['back_to_back'].any() else 0
    win_descansado = validos[~validos['back_to_back']]['win'].mean() * 100

    fig = go.Figure(go.Bar(
        x=['Back-to-back<br>(0 dias descanso)', 'Com descanso<br>(1+ dias)'],
        y=[win_b2b, win_descansado],
        marker_color=[CORES['vermelho'], CORES['azul']],
        text=[f"{win_b2b:.1f}%", f"{win_descansado:.1f}%"], textposition='outside',
    ))
    fig.update_layout(template=TEMPLATE_PLOTLY, margin=dict(l=10, r=10, t=10, b=10),
                       height=300, yaxis_title='Taxa de vitória (%)', yaxis_range=[0, 65])
    return fig


def fig_ranking_times(df_f, times_selecionados):
    if len(df_f) == 0:
        return go.Figure()
    ranking = df_f.groupby('TEAM_ABBREVIATION').agg(jogos=('win', 'count'), vitorias=('win', 'sum'))

    if times_selecionados:
        elegiveis = ranking.copy()
    else:
        min_jogos = max(5, int(ranking['jogos'].max() * 0.15)) if len(ranking) else 5
        elegiveis = ranking[ranking['jogos'] >= min_jogos].copy()

    if len(elegiveis) == 0:
        return go.Figure()

    elegiveis['pct'] = (elegiveis['vitorias'] / elegiveis['jogos'] * 100).round(1)
    elegiveis['nome'] = [TEAM_NOME_MAP.get(t, t) for t in elegiveis.index]
    elegiveis = elegiveis.sort_values('pct', ascending=False).head(15).sort_values('pct')

    cores_barras = [CORES['vermelho'] if t in (times_selecionados or []) else '#9fb3d9' for t in elegiveis.index]
    if not times_selecionados:
        cores_barras = [CORES['azul']] * len(elegiveis)

    textos_barra = []
    for v in elegiveis['pct']:
        textos_barra.append(str(v) + '%')

    fig = go.Figure(go.Bar(
        x=elegiveis['pct'], y=elegiveis['nome'], orientation='h',
        marker_color=cores_barras,
        text=textos_barra, textposition='outside',
        customdata=elegiveis['jogos'],
        hovertemplate='%{y}<br>Vitórias: %{x}%<br>Jogos: %{customdata}<extra></extra>'
    ))
    fig.update_layout(template=TEMPLATE_PLOTLY, margin=dict(l=10, r=30, t=10, b=10),
                       height=420, xaxis_title='% de vitórias',
                       xaxis_range=[0, max(elegiveis['pct'].max() * 1.15, 10)])
    return fig


def fig_correlacao_vitoria(df_f):
    if len(df_f) < 5:
        return go.Figure()
    sub = df_f[STATS_CORRELACAO + ['win']].copy()
    if sub['win'].std() == 0:
        return go.Figure()
    corr = sub.corr()['win'].drop('win')
    corr = corr.reindex(corr.abs().sort_values(ascending=True).index)

    cores_barras = [CORES['azul'] if v > 0 else CORES['vermelho'] for v in corr.values]
    nomes_eixo = [NOMES_STATS.get(s, s) for s in corr.index]

    textos_barra = []
    for v in corr.values:
        textos_barra.append(str(round(v, 2)))

    fig = go.Figure(go.Bar(
        x=corr.values, y=nomes_eixo, orientation='h',
        marker_color=cores_barras,
        text=textos_barra, textposition='outside',
    ))
    fig.add_vline(x=0, line_color='gray', line_width=0.8)
    fig.update_layout(template=TEMPLATE_PLOTLY, margin=dict(l=10, r=30, t=10, b=10),
                       height=350, xaxis_title='Correlação com vitória')
    return fig


def fig_turnovers(df_f):
    if len(df_f) == 0:
        return go.Figure()
    tov_vitoria = df_f[df_f['win'] == 1]['TOV'].mean()
    tov_derrota = df_f[df_f['win'] == 0]['TOV'].mean()
    if pd.isna(tov_vitoria) or pd.isna(tov_derrota):
        return go.Figure()

    fig = go.Figure(go.Bar(
        x=['Vitórias', 'Derrotas'], y=[tov_vitoria, tov_derrota],
        marker_color=[CORES['azul'], CORES['vermelho']],
        text=[f"{tov_vitoria:.2f}", f"{tov_derrota:.2f}"], textposition='outside',
    ))
    fig.update_layout(template=TEMPLATE_PLOTLY, margin=dict(l=10, r=10, t=10, b=10),
                       height=300, yaxis_title='Turnovers médios por jogo')
    return fig


def fig_defesa_ativa(df_f):
    if len(df_f) == 0:
        return go.Figure()
    tab = df_f.groupby('season_start').agg(roubos=('STL', 'mean'), tocos=('BLK', 'mean'))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=tab.index, y=tab['roubos'], mode='lines+markers', name='Roubos (STL)',
                              line=dict(color=CORES['azul'], width=3), marker=dict(size=6)))
    fig.add_trace(go.Scatter(x=tab.index, y=tab['tocos'], mode='lines+markers', name='Tocos (BLK)',
                              line=dict(color=CORES['vermelho'], width=3), marker=dict(size=6)))
    fig.update_layout(template=TEMPLATE_PLOTLY, margin=dict(l=10, r=10, t=10, b=10),
                       height=300, yaxis_title='Média por jogo', xaxis_title=None,
                       legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0))
    return fig


def gerar_insights(df_f, season_range, times_selecionados):
    if len(df_f) == 0:
        return [html.Div("Nenhum jogo encontrado para os filtros selecionados. Tente ampliar o período ou os times.",
                          className='insight-item')]

    insights = []

    linhas_casa = df_f[df_f['is_home']]
    if len(linhas_casa):
        pct_mandante = linhas_casa['win'].mean() * 100
        diff = pct_mandante - HIST_HOME_WIN_PCT
        if abs(diff) < 0.3:
            insights.append(
                f"O time da casa venceu {pct_mandante:.1f}% dos jogos no período selecionado, "
                f"praticamente em linha com a média histórica geral."
            )
        else:
            direcao = "acima" if diff > 0 else "abaixo"
            insights.append(
                f"O time da casa venceu {pct_mandante:.1f}% dos jogos no período selecionado, "
                f"{abs(diff):.1f} p.p. {direcao} da média histórica geral ({HIST_HOME_WIN_PCT:.1f}%)."
            )

    media_pts = df_f['PTS'].mean()
    diff_pts = media_pts - HIST_PTS_MEDIA
    if abs(diff_pts) < 0.05:
        insights.append(
            f"A média foi de {media_pts:.1f} pontos por time por jogo, em linha com a média histórica geral."
        )
    else:
        direcao_pts = "mais" if diff_pts > 0 else "menos"
        insights.append(
            f"A média foi de {media_pts:.1f} pontos por time por jogo — {abs(diff_pts):.1f} pontos {direcao_pts} "
            f"que a média histórica geral ({HIST_PTS_MEDIA:.1f})."
        )

    media_fg3a = df_f['FG3A'].mean()
    diff_fg3a = media_fg3a - HIST_FG3A_MEDIA
    if abs(diff_fg3a) > 0.5:
        direcao_3 = "mais" if diff_fg3a > 0 else "menos"
        insights.append(
            f"Foram {media_fg3a:.1f} tentativas de 3 pontos por jogo em média — {abs(diff_fg3a):.1f} "
            f"{direcao_3} que a média histórica geral ({HIST_FG3A_MEDIA:.1f}), refletindo a evolução do estilo de jogo entre as temporadas selecionadas."
        )

    ranking = df_f.groupby('TEAM_ABBREVIATION').agg(jogos=('win', 'count'), vitorias=('win', 'sum'))
    min_jogos = max(5, int(ranking['jogos'].max() * 0.15)) if len(ranking) else 5
    elegiveis = ranking[ranking['jogos'] >= min_jogos].copy()
    if len(elegiveis):
        elegiveis['pct'] = elegiveis['vitorias'] / elegiveis['jogos'] * 100
        sigla_melhor = elegiveis['pct'].idxmax()
        nome_melhor = TEAM_NOME_MAP.get(sigla_melhor, sigla_melhor)
        insights.append(
            f"{nome_melhor} teve o melhor aproveitamento do período ({elegiveis['pct'].max():.1f}% de vitórias) "
            f"entre os times com pelo menos {min_jogos} jogos disputados."
        )

    validos = df_f.dropna(subset=['dias_descanso'])
    validos = validos[validos['dias_descanso'] >= 0]
    if len(validos) and validos['back_to_back'].any():
        win_b2b = validos[validos['back_to_back']]['win'].mean() * 100
        win_desc = validos[~validos['back_to_back']]['win'].mean() * 100
        gap = win_desc - win_b2b
        insights.append(
            f"Jogando em back-to-back (sem descanso), a taxa de vitória cai para {win_b2b:.1f}%, contra "
            f"{win_desc:.1f}% com pelo menos 1 dia de descanso — uma diferença de {gap:.1f} p.p."
        )

    if len(df_f) >= 5 and df_f['win'].std() > 0:
        sub = df_f[STATS_CORRELACAO + ['win']]
        corr = sub.corr()['win'].drop('win')
        stat_mais_forte = corr.abs().idxmax()
        insights.append(
            f"A estatística mais associada à vitória no período é {NOMES_STATS.get(stat_mais_forte, stat_mais_forte)} "
            f"(correlação de {corr[stat_mais_forte]:.2f}) — mais até do que volume bruto de pontos em muitos casos."
        )

    tov_vitoria = df_f[df_f['win'] == 1]['TOV'].mean()
    tov_derrota = df_f[df_f['win'] == 0]['TOV'].mean()
    if pd.notna(tov_vitoria) and pd.notna(tov_derrota):
        insights.append(
            f"Times venceram cometendo em média {tov_vitoria:.2f} turnovers por jogo, contra {tov_derrota:.2f} "
            f"nas derrotas — cuidar da bola segue sendo um dos fundamentos mais ligados à vitória."
        )

    if times_selecionados and len(times_selecionados) >= 1:
        sub = df_f[df_f['TEAM_ABBREVIATION'].isin(times_selecionados)]
        casa = sub[sub['is_home']]
        fora = sub[~sub['is_home']]
        if len(casa) > 0 and len(fora) > 0:
            pct_casa = casa['win'].mean() * 100
            pct_fora = fora['win'].mean() * 100
            gap2 = pct_casa - pct_fora
            times_txt = ', '.join(TEAM_NOME_MAP.get(t, t) for t in times_selecionados) if len(times_selecionados) <= 2 \
                else f"{len(times_selecionados)} times selecionados"
            insights.append(
                f"Para {times_txt}, o aproveitamento em casa ({pct_casa:.1f}%) é "
                f"{abs(gap2):.1f} p.p. {'maior' if gap2 > 0 else 'menor'} que fora ({pct_fora:.1f}%)."
            )

    return [html.Div(f"• {texto}", className='insight-item') for texto in insights]


# ------------------------------------------------------------------
# 3. Layout
# ------------------------------------------------------------------

app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], title="NBA Dashboard")
server = app.server  # necessário para deploy (gunicorn)

app.layout = dbc.Container([

    html.Div([
        html.H1("🏀 NBA Dashboard"),
        html.P(f"Retrospectiva interativa da temporada regular — {SEASON_MIN}-{str(SEASON_MIN+1)[-2:]} a "
               f"{SEASON_MAX}-{str(SEASON_MAX+1)[-2:]} · {df['GAME_ID'].nunique():,} jogos".replace(',', '.')),
    ], className='header-banner'),

    # Filtros
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Div("Período (temporadas)", className='filter-label'),
                dcc.RangeSlider(
                    id='filtro-temporada', min=SEASON_MIN, max=SEASON_MAX, value=[SEASON_MIN, SEASON_MAX],
                    marks={a: str(a) for a in range(SEASON_MIN, SEASON_MAX + 1, 2)},
                    tooltip={'placement': 'bottom', 'always_visible': False},
                    step=1,
                ),
            ], className='filter-card')
        ], md=7),
        dbc.Col([
            html.Div([
                html.Div("Times (vazio = todos)", className='filter-label'),
                dcc.Dropdown(
                    id='filtro-times',
                    options=[{'label': nome, 'value': sigla} for sigla, nome in LISTA_TIMES],
                    value=[], multi=True, placeholder="Selecione um ou mais times...",
                ),
            ], className='filter-card')
        ], md=5),
    ]),

    # KPIs
    dbc.Row(id='kpi-row', className='mb-2'),

    # Insights dinâmicos
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H5("💡 Insights do período selecionado"),
                html.Div(id='insights-container'),
            ], className='insight-box')
        ], md=12)
    ], className='mb-3'),

    # Gráficos - linha 1
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H5("Vantagem de jogar em casa"),
                html.Div("% de vitórias do time da casa, por temporada", className='chart-sub'),
                dcc.Graph(id='grafico-mando', config=CONFIG_DOWNLOAD),
            ], className='chart-card')
        ], md=6),
        dbc.Col([
            html.Div([
                html.H5("Evolução do arremesso de 3 pontos"),
                html.Div("Tentativas por jogo e % de acerto, por temporada", className='chart-sub'),
                dcc.Graph(id='grafico-tres', config=CONFIG_DOWNLOAD),
            ], className='chart-card')
        ], md=6),
    ]),

    # Gráficos - linha 2
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H5("Pontos por jogo ao longo do tempo"),
                html.Div("Média de pontos por time, por temporada", className='chart-sub'),
                dcc.Graph(id='grafico-pontos', config=CONFIG_DOWNLOAD),
            ], className='chart-card')
        ], md=6),
        dbc.Col([
            html.Div([
                html.H5("Efeito do back-to-back"),
                html.Div("Taxa de vitória com e sem descanso entre jogos", className='chart-sub'),
                dcc.Graph(id='grafico-b2b', config=CONFIG_DOWNLOAD),
            ], className='chart-card')
        ], md=6),
    ]),

    # Gráficos - linha 3
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H5("Ranking por % de vitórias"),
                html.Div("Times ordenados por aproveitamento no período/seleção", className='chart-sub'),
                dcc.Graph(id='grafico-ranking', config=CONFIG_DOWNLOAD),
            ], className='chart-card')
        ], md=6),
        dbc.Col([
            html.Div([
                html.H5("O que mais correlaciona com vitória"),
                html.Div("Correlação de cada estatística de box score com o resultado", className='chart-sub'),
                dcc.Graph(id='grafico-correlacao', config=CONFIG_DOWNLOAD),
            ], className='chart-card')
        ], md=6),
    ]),

    # Gráficos - linha 4
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H5("Turnovers: vitórias vs. derrotas"),
                html.Div("Média de turnovers por jogo, separado por resultado", className='chart-sub'),
                dcc.Graph(id='grafico-turnovers', config=CONFIG_DOWNLOAD),
            ], className='chart-card')
        ], md=6),
        dbc.Col([
            html.Div([
                html.H5("Defesa ativa ao longo do tempo"),
                html.Div("Roubos de bola e tocos por jogo, por temporada", className='chart-sub'),
                dcc.Graph(id='grafico-defesa', config=CONFIG_DOWNLOAD),
            ], className='chart-card')
        ], md=6),
    ]),

    html.Div([
        "Dashboard construído com Dash + Plotly · Dados: NBA temporada regular 2010-2024 (GitHub, domínio público) · Projeto de portfólio"
    ], className='footer-note'),

], fluid=True, style={'maxWidth': '1300px', 'paddingBottom': '20px'})


# ------------------------------------------------------------------
# 4. Componente de KPI card (helper de layout)
# ------------------------------------------------------------------

def kpi_card(label, value, sub=None):
    children = [
        html.Div(label, className='kpi-label'),
        html.Div(value, className='kpi-value'),
    ]
    if sub:
        children.append(html.Div(sub, className='kpi-sub'))
    return dbc.Col(html.Div(children, className='kpi-card'), md=True, className='mb-3')


# ------------------------------------------------------------------
# 5. Callback principal
# ------------------------------------------------------------------

@app.callback(
    Output('kpi-row', 'children'),
    Output('insights-container', 'children'),
    Output('grafico-mando', 'figure'),
    Output('grafico-tres', 'figure'),
    Output('grafico-pontos', 'figure'),
    Output('grafico-b2b', 'figure'),
    Output('grafico-ranking', 'figure'),
    Output('grafico-correlacao', 'figure'),
    Output('grafico-turnovers', 'figure'),
    Output('grafico-defesa', 'figure'),
    Input('filtro-temporada', 'value'),
    Input('filtro-times', 'value'),
)
def atualizar_dashboard(season_range, times_selecionados):
    df_f = filtrar_dados(season_range, times_selecionados)
    kpis = calcular_kpis(df_f)

    kpi_cards = [
        kpi_card("Jogos no período", f"{kpis['jogos']:,}".replace(',', '.')),
        kpi_card("Média de pontos/time", f"{kpis['media_pts']:.1f}"),
        kpi_card("Vitórias em casa", f"{kpis['pct_mandante']:.1f}%"),
        kpi_card("Melhor aproveitamento", kpis['melhor_time'], f"{kpis['melhor_time_pct']:.1f}% de vitórias"),
        kpi_card("Maior pontuação", kpis['maior_pontuacao']),
    ]

    insights = gerar_insights(df_f, season_range, times_selecionados)

    fig1 = fig_mando_casa(df_f)
    fig2 = fig_evolucao_tres(df_f)
    fig3 = fig_pontos_por_ano(df_f)
    fig4 = fig_back_to_back(df_f)
    fig5 = fig_ranking_times(df_f, times_selecionados)
    fig6 = fig_correlacao_vitoria(df_f)
    fig7 = fig_turnovers(df_f)
    fig8 = fig_defesa_ativa(df_f)

    return kpi_cards, insights, fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8050)