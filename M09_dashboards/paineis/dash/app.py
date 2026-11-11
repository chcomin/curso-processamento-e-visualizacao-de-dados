"""
Painel de Segurança Pública no Brasil (Dash / Plotly)
Implementação didática baseada na especificação SnowUI.
"""

import json
import os
from pathlib import Path

import dash
from dash import ALL, Input, Output, State, dcc, html
import pandas as pd
import plotly.graph_objects as go

# ------------------------------------------------------------------------------
# 1. Carregamento de Dados e Caminhos
# ------------------------------------------------------------------------------
# Lê a pasta de dados relativa à estrutura do curso (M09_dashboards/dados)
DADOS_DIR = Path(__file__).resolve().parents[2] / "dados"

# Base mensal do SINESP com ocorrências e população IBGE
df_raw = pd.read_csv(DADOS_DIR / "sinesp_uf_mensal.csv")

# Malha geográfica dos 27 estados para o mapa coroplético
with open(DADOS_DIR / "br_uf.geojson", encoding="utf-8") as f:
    geojson_uf = json.load(f)


def _area(anel):
    """Área com sinal (fórmula do cadarço) de um anel de [lon, lat]."""
    return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(anel, anel[1:] + anel[:1])) / 2


def _reorientar(geom):
    """O Plotly (d3-geo) pede anéis externos horários; sem isso o mapa 'vira do avesso'."""
    poligonos = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    for poligono in poligonos:
        for i, anel in enumerate(poligono):
            horario = _area(anel) < 0
            if horario != (i == 0):  # externo deve ser horário, buracos anti-horários
                anel.reverse()


for _feat in geojson_uf["features"]:
    _reorientar(_feat["geometry"])

# Padroniza a coluna comparavel como booleano puro (jan-set)
df_raw["comparavel"] = df_raw["comparavel"].astype(str).str.lower().isin(["true", "1"])

# ------------------------------------------------------------------------------
# 2. Definição do Menu e Indicadores
# ------------------------------------------------------------------------------
# Grupos de indicadores na ordem exata da especificação
GRUPOS_INDICADORES = {
    "Crimes contra a vida": [
        "Homicídio doloso",
        "Latrocínio",
        "Lesão corporal seguida de morte",
        "Morte por intervenção de agente do Estado",
        "Tentativa de homicídio",
    ],
    "Violência contra a mulher e sexual": [
        "Feminicídio",
        "Tentativa de feminicídio",
        "Estupro",
        "Estupro de vulnerável",
    ],
    "Patrimônio": [
        "Roubo de veículo",
        "Furto de veículo",
        "Roubo de carga",
    ],
    "Drogas e armas": [
        "Tráfico de drogas",
        "Armas de fogo apreendidas",
    ],
    "Trânsito": [
        "Mortes no trânsito",
    ],
}

# Indicadores com polaridade neutra (apreensão pode indicar atuação policial)
INDICADORES_NEUTROS = {"Tráfico de drogas", "Armas de fogo apreendidas"}

# Mapeamento numérico dos meses para abreviações pt-BR
MESES_ABREV = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
MES_MAPA = {i: m for i, m in enumerate(MESES_ABREV, start=1)}

# Paleta violeta do painel Dash (os mesmos valores estão em assets/style.css)
DATA_1 = "#2B1F6B"  # 2026 (período atual)
DATA_2 = "#B9B0F0"  # 2025 (comparação)
SEQ = ["#ECE9FF", "#C8C0FA", "#9A8CEF", "#6A56D4", "#37278A"]  # escala do mapa
MESES_OPCOES = [{"label": m, "value": i} for i, m in enumerate(MESES_ABREV[:9], start=1)]


def rotulo_intervalo(m1, m2):
    """'jan–jun'; se for um mês só, apenas 'mar'."""
    return MESES_ABREV[m1 - 1] if m1 == m2 else f"{MESES_ABREV[m1 - 1]}–{MESES_ABREV[m2 - 1]}"


def ordenar_meses(m1, m2):
    """Se o mês inicial passar do final, troca os dois."""
    m1, m2 = int(m1 or 1), int(m2 or 9)
    return (m1, m2) if m1 <= m2 else (m2, m1)


# ------------------------------------------------------------------------------
# 3. Funções Auxiliares de Formatação (Padrão pt-BR)
# ------------------------------------------------------------------------------
def fmt_inteiro(val):
    """Formata número inteiro no padrão pt-BR: 20728 -> '20.728'."""
    if pd.isna(val):
        return "—"
    return f"{int(round(val)):,}".replace(",", ".")


def fmt_decimal(val, casas=2):
    """Formata decimal no padrão pt-BR com sinal de menos tipográfico: 9.68 -> '9,68'."""
    if pd.isna(val):
        return "—"
    s = f"{val:,.{casas}f}"
    s = s.replace(".", "X").replace(",", ".").replace("X", ",")
    if s.startswith("-"):
        s = "−" + s[1:]
    return s


def fmt_delta(val):
    """Formata variação percentual com seta e sinal: -12.94 -> '−12,9% ↘'."""
    if pd.isna(val):
        return "—"
    val_round = round(val, 1)
    if val_round > 0:
        return f"+{val_round:.1f}% ↗".replace(".", ",")
    elif val_round < 0:
        return f"−{abs(val_round):.1f}% ↘".replace(".", ",")
    else:
        return "0,0% →"


# ------------------------------------------------------------------------------
# 4. Cálculo dos 4 KPIs Fixos (P1)
# ------------------------------------------------------------------------------
def renderizar_kpis_fixos(df, m1=1, m2=9):
    """Calcula os 4 cartões fixos no intervalo de meses escolhido (2025 vs 2026)."""
    rot = rotulo_intervalo(m1, m2)
    kpis_config = [
        ("Homicídio doloso", "kpi-blue"),
        ("Latrocínio", "kpi-lav"),
        ("Feminicídio", "kpi-blue"),
        ("Estupro", "kpi-lav"),
    ]
    cards = []
    for ind, tema_cor in kpis_config:
        no_intervalo = df[(df["comparavel"]) & (df["mes"].between(m1, m2)) & (df["indicador"] == ind)]
        df_25 = no_intervalo[no_intervalo["ano"] == 2025]
        df_26 = no_intervalo[no_intervalo["ano"] == 2026]
        tot_25 = int(df_25["valor"].sum())
        tot_26 = int(df_26["valor"].sum())
        delta = ((tot_26 / tot_25) - 1.0) * 100.0 if tot_25 > 0 else 0.0

        # Polaridade: para crimes, queda é desejável (--good) e alta é ruim (--bad)
        delta_class = "kpi-good" if delta < 0 else ("kpi-bad" if delta > 0 else "kpi-neutral")

        cards.append(
            html.Div(
                className=f"kpi-card {tema_cor}",
                children=[
                    html.Div(ind, className="kpi-label"),
                    html.Div(
                        className="kpi-value-row",
                        children=[
                            html.Span(fmt_inteiro(tot_26), className="kpi-number"),
                            html.Span(fmt_delta(delta), className=f"kpi-delta {delta_class}"),
                        ],
                    ),
                    html.Div(
                        f"vs {fmt_inteiro(tot_25)} em {rot} 2025",
                        className="kpi-comparison",
                    ),
                ],
            )
        )
    return cards


# ------------------------------------------------------------------------------
# 5. Inicialização da Aplicação Dash
# ------------------------------------------------------------------------------
app = dash.Dash(
    __name__,
    title="Segurança pública no Brasil · Dash",
    suppress_callback_exceptions=True,
)
server = app.server  # Exposição para o Gunicorn

# ------------------------------------------------------------------------------
# 6. Layout Principal
# ------------------------------------------------------------------------------
app.layout = html.Div(
    className="dashboard-root",
    children=[
        # Armazena em memória do navegador o indicador selecionado
        dcc.Store(id="indicador-ativo", data="Homicídio doloso"),
        # Div oculta para permitir callbacks puramente client-side
        html.Div(id="client-dummy", style={"display": "none"}),

        # --- BARRA LATERAL (Menu de Indicadores agrupado) ---
        html.Aside(
            className="sidebar",
            children=[
                # Marca: ícone do Plotly/Dash + nome do painel e da ferramenta
                html.Div(
                    className="brand-header",
                    children=[
                        html.Span(className="brand-logo"),
                        html.Div(
                            className="brand-text",
                            children=[
                                html.Div("Segurança pública no Brasil", className="brand-title"),
                                html.Div(["Painel em ", html.Strong("Dash")], className="brand-sub"),
                            ],
                        ),
                    ],
                ),
                html.Nav(
                    children=[
                        html.Div(
                            className="nav-group",
                            children=[
                                html.Div(grupo, className="nav-group-title"),
                                *[
                                    html.Button(
                                        ind,
                                        id={"type": "item", "indicador": ind},
                                        className=(
                                            "nav-item active"
                                            if ind == "Homicídio doloso"
                                            else "nav-item"
                                        ),
                                        n_clicks=0,
                                    )
                                    for ind in lista
                                ],
                            ],
                        )
                        for grupo, lista in GRUPOS_INDICADORES.items()
                    ]
                ),
            ],
        ),

        # --- ÁREA CENTRAL ---
        html.Div(
            className="main-wrapper",
            children=[
                # Topo (Breadcrumb + Período + Tema)
                html.Header(
                    className="app-header",
                    children=[
                        html.Div(
                            className="breadcrumb",
                            children=[
                                html.Span("Painéis", className="breadcrumb-root"),
                                html.Span("/", className="breadcrumb-sep"),
                                html.Span("Segurança pública", className="breadcrumb-current"),
                            ],
                        ),
                        html.Div(
                            className="header-right",
                            children=[
                                # Filtro temporal: mesmos meses nos dois anos
                                html.Div(
                                    className="period-filter",
                                    children=[
                                        html.Span("De", className="filter-label"),
                                        dcc.Dropdown(id="mes-de", options=MESES_OPCOES, value=1,
                                                     clearable=False, searchable=False, className="mes-dd"),
                                        html.Span("até", className="filter-label"),
                                        dcc.Dropdown(id="mes-ate", options=MESES_OPCOES, value=9,
                                                     clearable=False, searchable=False, className="mes-dd"),
                                    ],
                                ),
                                html.Div("jan–set · 2026 × 2025", id="period-chip", className="period-chip"),
                                html.Button(
                                    "◐",
                                    id="theme-toggle-btn",
                                    className="theme-toggle-btn",
                                    title="Alternar tema claro/escuro",
                                    n_clicks=0,
                                ),
                            ],
                        ),
                    ],
                ),

                # Conteúdo Principal
                html.Main(
                    className="main-content",
                    children=[
                        html.H1("Segurança pública no Brasil", className="page-title"),

                        # P1: KPIs Fixos
                        html.Section(
                            className="kpis-grid",
                            id="kpis-grid",
                            children=renderizar_kpis_fixos(df_raw),
                        ),

                        # P2, P3 e P4: Cartões Dinâmicos em CSS Grid
                        html.Section(
                            className="charts-grid",
                            children=[
                                # Bloco P2: Mapa + Ranking Top 5
                                html.Div(
                                    className="card card-p2",
                                    children=[
                                        html.Div(
                                            className="card-header",
                                            children=[
                                                html.H2("Onde o risco é maior?", className="card-title"),
                                                html.Div(id="p2-subtitle", className="card-subtitle"),
                                            ],
                                        ),
                                        html.Div(
                                            className="p2-container",
                                            children=[
                                                html.Div(
                                                    className="p2-map-col",
                                                    children=[
                                                        dcc.Graph(
                                                            id="p2-mapa-graph",
                                                            config={"displayModeBar": False},
                                                        ),
                                                        html.Div(id="p2-mapa-legend", className="p2-legend"),
                                                    ],
                                                ),
                                                html.Div(
                                                    className="p2-ranking-col",
                                                    children=[
                                                        html.Div("Maiores taxas", className="ranking-title"),
                                                        html.Div(id="p2-ranking-list", className="ranking-list"),
                                                    ],
                                                ),
                                            ],
                                        ),
                                    ],
                                ),

                                # Bloco P3: Gráfico Dumbbell (Pareado)
                                html.Div(
                                    className="card card-p3",
                                    children=[
                                        html.Div(
                                            className="card-header",
                                            children=[
                                                html.H2("Quais estados melhoraram ou pioraram?", className="card-title"),
                                                html.Div(id="p3-subtitle", className="card-subtitle"),
                                            ],
                                        ),
                                        dcc.Graph(
                                            id="p3-dumbbell-graph",
                                            config={"displayModeBar": False},
                                        ),
                                    ],
                                ),

                                # Bloco P4: Tendência Mensal
                                html.Div(
                                    className="card card-p4",
                                    children=[
                                        html.Div(
                                            className="card-header",
                                            children=[
                                                html.Div(
                                                    className="card-header-row",
                                                    children=[
                                                        html.H2("A mudança é de um mês ou do ano todo?", className="card-title"),
                                                        html.Div(id="p4-legend", className="header-legend-p4"),
                                                    ],
                                                ),
                                                html.Div(id="p4-subtitle", className="card-subtitle"),
                                            ],
                                        ),
                                        dcc.Graph(
                                            id="p4-tendencia-graph",
                                            config={"displayModeBar": False},
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),

        # --- PAINEL DIREITO (Sobre os dados) ---
        html.Aside(
            className="sidebar-right",
            children=[
                html.H3("Sobre os dados", className="about-header"),
                html.Div(
                    className="about-list",
                    children=[
                        html.Div(
                            className="about-item",
                            children=[
                                html.Div("1", className="about-icon"),
                                html.Div(
                                    className="about-content",
                                    children=[
                                        html.Div("Fonte", className="about-title"),
                                        html.Div(
                                            "SINESP VDE / Ministério da Justiça e Segurança Pública (extração em 11/11/2026). População: estimativas do IBGE para 2025 e 2026.",
                                            className="about-text",
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            className="about-item",
                            children=[
                                html.Div("2", className="about-icon"),
                                html.Div(
                                    className="about-content",
                                    children=[
                                        html.Div("Período comparável", className="about-title"),
                                        html.Div(
                                            "jan–set. A base de 2026 disponibilizada vai até setembro.",
                                            className="about-text",
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            className="about-item",
                            children=[
                                html.Div("3", className="about-icon"),
                                html.Div(
                                    className="about-content",
                                    children=[
                                        html.Div("Dados preliminares", className="about-title"),
                                        html.Div(
                                            "Os estados ainda podem revisar os dados históricos enviados.",
                                            className="about-text",
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            className="about-item",
                            children=[
                                html.Div("4", className="about-icon"),
                                html.Div(
                                    className="about-content",
                                    children=[
                                        html.Div("Atenção a MS", className="about-title"),
                                        html.Div(
                                            "A série de homicídios muda de patamar entre 2025 e 2026. Compare com cautela.",
                                            className="about-text",
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            className="about-item",
                            children=[
                                html.Div("5", className="about-icon"),
                                html.Div(
                                    className="about-content",
                                    children=[
                                        html.Div("Como ler a taxa", className="about-title"),
                                        html.Div(
                                            "Ocorrências (ou vítimas) no período ÷ população × 100 mil. Não é anualizada.",
                                            className="about-text",
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)

# ------------------------------------------------------------------------------
# 7. Callbacks de Navegação e Tema
# ------------------------------------------------------------------------------
@app.callback(
    Output("indicador-ativo", "data"),
    Input({"type": "item", "indicador": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def atualizar_indicador(n_clicks_list):
    """Atualiza o indicador selecionado a partir do clique no menu lateral."""
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    prop_id = ctx.triggered[0]["prop_id"].split(".")[0]
    data = json.loads(prop_id)
    return data["indicador"]


@app.callback(
    Output({"type": "item", "indicador": ALL}, "className"),
    Input("indicador-ativo", "data"),
    State({"type": "item", "indicador": ALL}, "id"),
)
def atualizar_classe_menu(indicador_ativo, ids):
    """Aplica a classe 'active' ao botão do indicador atualmente selecionado."""
    return [
        "nav-item active" if item_id["indicador"] == indicador_ativo else "nav-item"
        for item_id in ids
    ]


app.clientside_callback(
    """
    function(n_clicks) {
        if (!n_clicks) return "";
        var current = document.documentElement.getAttribute("data-theme");
        var next = current === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", next);
        return "";
    }
    """,
    Output("client-dummy", "children"),
    Input("theme-toggle-btn", "n_clicks"),
    prevent_initial_call=True,
)

# ------------------------------------------------------------------------------
# 8. Callback dos Gráficos (P2, P3 e P4)
# ------------------------------------------------------------------------------
@app.callback(
    Output("p2-subtitle", "children"),
    Output("p2-mapa-graph", "figure"),
    Output("p2-mapa-legend", "children"),
    Output("p2-ranking-list", "children"),
    Output("p3-subtitle", "children"),
    Output("p3-dumbbell-graph", "figure"),
    Output("p4-subtitle", "children"),
    Output("p4-legend", "children"),
    Output("p4-tendencia-graph", "figure"),
    Output("kpis-grid", "children"),
    Output("period-chip", "children"),
    Input("indicador-ativo", "data"),
    Input("mes-de", "value"),
    Input("mes-ate", "value"),
)
def atualizar_paineis(indicador_ativo, mes_de, mes_ate):
    """Recalcula KPIs, chip e os gráficos P2, P3 e P4 para o indicador e o intervalo de meses."""
    m1, m2 = ordenar_meses(mes_de, mes_ate)
    rot = rotulo_intervalo(m1, m2)
    # --------------------------------------------------------------------------
    # A. Agregação por UF no período comparável (jan-set)
    # --------------------------------------------------------------------------
    df_comp = df_raw[
        (df_raw["comparavel"]) & (df_raw["mes"].between(m1, m2)) & (df_raw["indicador"] == indicador_ativo)
    ]

    # Soma de valores por UF e ano
    df_val = df_comp.groupby(["uf", "ano"])["valor"].sum().reset_index()
    # População anual por UF
    df_pop = df_comp.groupby(["uf", "ano", "uf_nome"])["populacao"].first().reset_index()
    df_uf_ano = pd.merge(df_val, df_pop, on=["uf", "ano"])
    df_uf_ano["taxa"] = (df_uf_ano["valor"] / df_uf_ano["populacao"]) * 100000.0

    m25 = df_uf_ano[df_uf_ano["ano"] == 2025].set_index("uf")
    m26 = df_uf_ano[df_uf_ano["ano"] == 2026].set_index("uf")

    linhas_ufs = []
    for uf in sorted(df_raw["uf"].unique()):
        nome = (
            m26.loc[uf, "uf_nome"]
            if uf in m26.index
            else (m25.loc[uf, "uf_nome"] if uf in m25.index else uf)
        )
        t26 = float(m26.loc[uf, "taxa"]) if uf in m26.index else 0.0
        t25 = float(m25.loc[uf, "taxa"]) if uf in m25.index else 0.0
        v26 = int(m26.loc[uf, "valor"]) if uf in m26.index else 0
        v25 = int(m25.loc[uf, "valor"]) if uf in m25.index else 0
        delta = ((v26 / v25) - 1.0) * 100.0 if v25 > 0 else 0.0

        linhas_ufs.append({
            "uf": uf,
            "uf_nome": nome,
            "taxa_2026": t26,
            "taxa_2025": t25,
            "valor_2026": v26,
            "valor_2025": v25,
            "delta": delta,
        })
    df_ufs = pd.DataFrame(linhas_ufs)

    # --------------------------------------------------------------------------
    # B. Bloco P2: Mapa Coroplético e Ranking Top 5
    # --------------------------------------------------------------------------
    p2_sub = f"{indicador_ativo} · taxa por 100 mil hab. · {rot} 2026"

    # Quantis para divisão em 5 classes (0 a 4)
    q = df_ufs["taxa_2026"].quantile([0.0, 0.2, 0.4, 0.6, 0.8, 1.0]).tolist()

    def classificar_quantil(val):
        for i in range(4, -1, -1):
            if val >= q[i]:
                return min(i, 4)
        return 0

    df_ufs["classe"] = df_ufs["taxa_2026"].apply(classificar_quantil)

    # Cores sequenciais do SnowUI (--seq-0 até --seq-4)
    colorscale_seq = []
    for i, cor in enumerate(SEQ):  # 5 degraus planos (classes por quantis)
        colorscale_seq += [[i / 5, cor], [(i + 1) / 5, cor]]

    custom_mapa = df_ufs.apply(
        lambda r: [
            r["uf_nome"],
            fmt_decimal(r["taxa_2026"], 2),
            fmt_decimal(r["taxa_2025"], 2),
            fmt_delta(r["delta"]),
        ],
        axis=1,
    ).tolist()

    fig_mapa = go.Figure(
        go.Choropleth(
            geojson=geojson_uf,
            locations=df_ufs["uf"],
            featureidkey="properties.uf",
            z=df_ufs["classe"],
            zmin=0,
            zmax=4,
            colorscale=colorscale_seq,
            showscale=False,
            marker_line_color="#FFFFFF",
            marker_line_width=0.5,
            customdata=custom_mapa,
            hovertemplate=(
                "<b>%{customdata[0]} (%{location})</b><br>"
                "Taxa 2026: %{customdata[1]} por 100k<br>"
                "Taxa 2025: %{customdata[2]} por 100k<br>"
                "Δ: %{customdata[3]}<extra></extra>"
            ),
        )
    )
    fig_mapa.update_geos(
        fitbounds="locations", visible=False, projection_type="mercator",
        bgcolor="rgba(0,0,0,0)", domain=dict(x=[0, 1], y=[0, 1]),
    )
    fig_mapa.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", size=12, color="#1C1C1C"),
        height=340,
    )

    # Legenda HTML das classes por quantis
    cores_legend = SEQ
    rotulos_legend = [
        f"≤ {fmt_decimal(q[1], 1)}",
        f"{fmt_decimal(q[1], 1)}–{fmt_decimal(q[2], 1)}",
        f"{fmt_decimal(q[2], 1)}–{fmt_decimal(q[3], 1)}",
        f"{fmt_decimal(q[3], 1)}–{fmt_decimal(q[4], 1)}",
        f"> {fmt_decimal(q[4], 1)}",
    ]
    p2_legend = [
        html.Div(
            className="legend-step",
            children=[
                html.Span(className="legend-color-box", style={"backgroundColor": c}),
                html.Span(r, className="legend-label"),
            ],
        )
        for c, r in zip(cores_legend, rotulos_legend)
    ]

    # Ranking Top 5 (SnowUI: nome, valor formatado e barra horizontal)
    top5 = df_ufs.sort_values(by="taxa_2026", ascending=False).head(5)
    max_top5 = top5["taxa_2026"].max() if len(top5) > 0 and top5["taxa_2026"].max() > 0 else 1.0

    p2_ranking = []
    for _, row in top5.iterrows():
        pct_bar = (row["taxa_2026"] / max_top5) * 100.0
        p2_ranking.append(
            html.Div(
                className="ranking-item",
                children=[
                    html.Div(
                        className="ranking-row",
                        children=[
                            html.Span(f"{row['uf']} · {row['uf_nome']}", className="ranking-name"),
                            html.Span(fmt_decimal(row["taxa_2026"], 2), className="ranking-val"),
                        ],
                    ),
                    html.Div(
                        className="ranking-bar-track",
                        children=[
                            html.Div(
                                className="ranking-bar-fill",
                                style={"width": f"{pct_bar:.1f}%"},
                            )
                        ],
                    ),
                ],
            )
        )

    # --------------------------------------------------------------------------
    # C. Bloco P3: Gráfico Dumbbell (Pareado)
    # --------------------------------------------------------------------------
    p3_sub = f"{indicador_ativo} · taxa por 100 mil hab. · {rot} 2025 → 2026"

    # Ordena ascendente para que a maior taxa 2026 apareça no topo do eixo Y
    df_db = df_ufs.sort_values(by="taxa_2026", ascending=True)

    is_neutro = indicador_ativo in INDICADORES_NEUTROS
    cor_good = "#0F7B5F"
    cor_bad = "#C0362C"
    cor_neutra = "rgba(28, 28, 28, 0.40)"

    # Segmentos agrupados por cor separando pares com None
    x_good, y_good = [], []
    x_bad, y_bad = [], []
    x_neutra, y_neutra = [], []

    for _, r in df_db.iterrows():
        uf_sigla = r["uf"]
        t25 = r["taxa_2025"]
        t26 = r["taxa_2026"]
        if is_neutro:
            x_neutra.extend([t25, t26, None])
            y_neutra.extend([uf_sigla, uf_sigla, None])
        else:
            if t26 < t25:
                x_good.extend([t25, t26, None])
                y_good.extend([uf_sigla, uf_sigla, None])
            elif t26 > t25:
                x_bad.extend([t25, t26, None])
                y_bad.extend([uf_sigla, uf_sigla, None])
            else:
                x_neutra.extend([t25, t26, None])
                y_neutra.extend([uf_sigla, uf_sigla, None])

    fig_db = go.Figure()

    if x_good:
        fig_db.add_trace(go.Scatter(
            x=x_good, y=y_good, mode="lines",
            line=dict(color=cor_good, width=2),
            hoverinfo="skip", showlegend=False,
        ))
    if x_bad:
        fig_db.add_trace(go.Scatter(
            x=x_bad, y=y_bad, mode="lines",
            line=dict(color=cor_bad, width=2),
            hoverinfo="skip", showlegend=False,
        ))
    if x_neutra:
        fig_db.add_trace(go.Scatter(
            x=x_neutra, y=y_neutra, mode="lines",
            line=dict(color=cor_neutra, width=2),
            hoverinfo="skip", showlegend=False,
        ))

    # Ponto de 2025: círculo de 6px em --data-2 (#A8C5DA)
    fig_db.add_trace(go.Scatter(
        x=df_db["taxa_2025"],
        y=df_db["uf"],
        mode="markers",
        marker=dict(size=6, color=DATA_2),
        name="2025",
        hoverinfo="skip",
        showlegend=False,
    ))

    # Ponto de 2026: círculo de 8px em --data-1 (#1C1C1C) com tooltip
    custom_db = df_db.apply(
        lambda r: [
            r["uf_nome"],
            fmt_decimal(r["taxa_2026"], 2),
            fmt_decimal(r["taxa_2025"], 2),
            fmt_delta(r["delta"]),
        ],
        axis=1,
    ).tolist()

    fig_db.add_trace(go.Scatter(
        x=df_db["taxa_2026"],
        y=df_db["uf"],
        mode="markers",
        marker=dict(size=8, color=DATA_1),
        name="2026",
        customdata=custom_db,
        hovertemplate=(
            "<b>%{customdata[0]} (%{y})</b><br>"
            "Taxa 2026: %{customdata[1]} por 100k<br>"
            "Taxa 2025: %{customdata[2]} por 100k<br>"
            "Δ: %{customdata[3]}<extra></extra>"
        ),
        showlegend=False,
    ))

    max_db = max(df_db["taxa_2026"].max(), df_db["taxa_2025"].max())
    fig_db.update_layout(
        margin=dict(l=35, r=16, t=8, b=24),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", size=11, color="#1C1C1C"),
        height=580,
        xaxis=dict(
            range=[0, max_db * 1.05 if max_db > 0 else 10],
            showgrid=True,
            gridcolor="rgba(28, 28, 28, 0.10)",
            gridwidth=1,
            showline=False,
            zeroline=False,
            ticks="",
            tickfont=dict(size=11, color="rgba(28, 28, 28, 0.40)"),
        ),
        yaxis=dict(
            showgrid=False,
            showline=False,
            zeroline=False,
            ticks="",
            tickfont=dict(size=11, color="#1C1C1C"),
            categoryorder="array",  # fixa a ordem: maior taxa de 2026 no topo
            categoryarray=df_db["uf"].tolist(),
        ),
    )

    # --------------------------------------------------------------------------
    # D. Bloco P4: Tendência Mensal
    # --------------------------------------------------------------------------
    df_tend = df_raw[df_raw["indicador"] == indicador_ativo]
    unidade = df_tend["unidade"].iloc[0] if len(df_tend) > 0 else "ocorrências"
    p4_sub = f"{indicador_ativo} · total no Brasil por mês ({unidade})"

    # Agrupamento nacional mensal (2025 inteiro vs 2026 jan-set)
    mensal = df_tend.groupby(["ano", "mes"])["valor"].sum().reset_index()
    m25_tend = mensal[mensal["ano"] == 2025].sort_values("mes")
    m26_tend = mensal[mensal["ano"] == 2026].sort_values("mes")

    m25_tend["mes_nome"] = m25_tend["mes"].map(MES_MAPA)
    m26_tend["mes_nome"] = m26_tend["mes"].map(MES_MAPA)

    # Totais da legenda: só o intervalo de meses escolhido
    tot_js_25 = int(m25_tend[m25_tend["mes"].between(m1, m2)]["valor"].sum())
    tot_js_26 = int(m26_tend[m26_tend["mes"].between(m1, m2)]["valor"].sum())

    p4_legenda = html.Span([
        html.Span("● 2026 "),
        html.Strong(fmt_inteiro(tot_js_26)),
        html.Span("  ·  ○ 2025 "),
        html.Strong(fmt_inteiro(tot_js_25)),
    ])

    fig_tend = go.Figure()

    # 2025 tracejado em --data-2 (#A8C5DA)
    fig_tend.add_trace(go.Scatter(
        x=m25_tend["mes_nome"],
        y=m25_tend["valor"],
        mode="lines",
        line=dict(color=DATA_2, width=2, dash="dash"),
        name="2025",
        customdata=[fmt_inteiro(v) for v in m25_tend["valor"]],
        hovertemplate="2025 · %{x}: %{customdata}<extra></extra>",
    ))

    # 2026 sólido em --data-1 (#1C1C1C)
    fig_tend.add_trace(go.Scatter(
        x=m26_tend["mes_nome"],
        y=m26_tend["valor"],
        mode="lines",
        line=dict(color=DATA_1, width=2),
        name="2026",
        customdata=[fmt_inteiro(v) for v in m26_tend["valor"]],
        hovertemplate="2026 · %{x}: %{customdata}<extra></extra>",
    ))

    # Rótulos diretos no final de cada série
    anotacoes_tend = []
    if len(m26_tend) > 0:
        anotacoes_tend.append(dict(
            x=m26_tend.iloc[-1]["mes_nome"],
            y=m26_tend.iloc[-1]["valor"],
            text="2026",
            showarrow=False,
            xanchor="left",
            xshift=8,
            font=dict(family="Inter", size=12, color=DATA_1),
        ))
    if len(m25_tend) > 0:
        anotacoes_tend.append(dict(
            x=m25_tend.iloc[-1]["mes_nome"],
            y=m25_tend.iloc[-1]["valor"],
            text="2025",
            showarrow=False,
            xanchor="left",
            xshift=8,
            font=dict(family="Inter", size=12, color=DATA_2),
        ))

    fig_tend.update_layout(
        margin=dict(l=45, r=45, t=10, b=25),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", size=12, color="#1C1C1C"),
        height=280,
        showlegend=False,
        annotations=anotacoes_tend,
        # Faixa vertical sombreia o intervalo de meses (eixo categórico: posição = índice do mês)
        shapes=[dict(
            type="rect", xref="x", yref="paper", x0=m1 - 1.5, x1=m2 - 0.5, y0=0, y1=1,
            fillcolor="rgba(28, 28, 28, 0.05)", line_width=0, layer="below",
        )],
        xaxis=dict(
            categoryorder="array",
            categoryarray=MESES_ABREV,
            tickangle=0,
            tickvals=MESES_ABREV[::2],  # a cada 2 meses: cabe em 390 px
            showgrid=False,
            showline=False,
            zeroline=False,
            ticks="",
            tickfont=dict(size=12, color="rgba(28, 28, 28, 0.40)"),
        ),
        yaxis=dict(
            rangemode="tozero",
            showgrid=True,
            gridcolor="rgba(28, 28, 28, 0.10)",
            gridwidth=1,
            showline=False,
            zeroline=False,
            ticks="",
            tickfont=dict(size=11, color="rgba(28, 28, 28, 0.40)"),
        ),
    )

    return (
        p2_sub,
        fig_mapa,
        p2_legend,
        p2_ranking,
        p3_sub,
        fig_db,
        p4_sub,
        p4_legenda,
        fig_tend,
        renderizar_kpis_fixos(df_raw, m1, m2),
        f"{rot} · 2026 × 2025",
    )


# ------------------------------------------------------------------------------
# 9. Execução Local
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8050)),
        debug=False,
    )
