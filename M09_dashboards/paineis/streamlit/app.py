"""
Painel 'Segurança pública no Brasil' em Streamlit.

Desenvolvido para a disciplina de Processamento e Visualização de Dados (PVD).
Segue estritamente as especificações visuais do kit SnowUI (fundo claro,
sem bordas pesadas, cartões em cinza suave e paleta pastel para KPIs).
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E CARREGAMENTO DE ESTILOS CSS
# ==============================================================================

# O layout 'wide' aproveita a largura total do navegador para a grade 7/5
st.set_page_config(
    layout="wide",
    page_title="Segurança pública no Brasil · Streamlit",
    initial_sidebar_state="auto",
)

# Injeção do arquivo style.css para aplicar o Design System SnowUI
CSS_PATH = Path(__file__).resolve().parent / "style.css"
if CSS_PATH.exists():
    with open(CSS_PATH, "r", encoding="utf-8") as f_css:
        st.markdown(f"<style>{f_css.read()}</style>", unsafe_allow_html=True)



def html(texto: str) -> str:
    """Remove indentação e quebras de linha: o Markdown trata linhas com 4+
    espaços como bloco de código, o que quebraria o HTML dos cartões."""
    return "".join(linha.strip() for linha in texto.splitlines())


def ajuda(chave: str, texto: str) -> None:
    """Botao redondo '?' (st.popover) que abre o balao de ajuda do grafico."""
    with st.popover("?", help="Como ler este gráfico", key=f"ajuda_{chave}"):
        st.markdown(texto)


def titulo_cartao(chave: str, titulo: str, subtitulo: str, texto: str) -> None:
    """Titulo H3 do cartao com o '?' ao lado (linha que nao empilha no celular)."""
    with st.container(key=f"cab_{chave}"):
        c_tit, c_aj = st.columns([30, 1], vertical_alignment="top")
        with c_tit:
            st.markdown(
                html(f"""
                <div class="card-container">
                    <h3 class="card-title">{titulo}</h3>
                    <div class="card-subtitle">{subtitulo}</div>
                </div>
                """),
                unsafe_allow_html=True,
            )
        with c_aj:
            ajuda(chave, texto)


MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set"]


def rotulo_intervalo(m0: int, m1: int) -> str:
    """'jan–jun' para intervalos; só o mês quando m0 == m1 (ex.: 'mar')."""
    return MESES[m0 - 1] if m0 == m1 else f"{MESES[m0 - 1]}–{MESES[m1 - 1]}"


# ==============================================================================
# 2. DEFINIÇÃO DOS INDICADORES E GRUPOS (15 INDICADORES EM 5 GRUPOS)
# ==============================================================================

# Dicionário na ordem exata definida na especificação da disciplina
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

# Lista plana dos 15 indicadores e mapa indicador -> grupo para exibição
TODOS_INDICADORES = []
MAPA_INDICADOR_GRUPO = {}
for grupo, lista_inds in GRUPOS_INDICADORES.items():
    for ind in lista_inds:
        TODOS_INDICADORES.append(ind)
        MAPA_INDICADOR_GRUPO[ind] = grupo

# Indicadores com polaridade neutra: mais apreensões podem significar mais polícia
INDICADORES_NEUTROS = {"Tráfico de drogas", "Armas de fogo apreendidas"}

# ==============================================================================
# 3. FUNÇÕES UTILITÁRIAS DE FORMATAÇÃO (PADRÃO pt-BR)
# ==============================================================================


def format_int_br(valor: float | int) -> str:
    """Formata inteiros com ponto separador de milhar no padrão brasileiro."""
    if pd.isna(valor):
        return "—"
    return f"{int(round(valor)):,}".replace(",", ".")


def format_decimal_br(valor: float, casas: int = 1) -> str:
    """Formata número decimal com vírgula e sinal tipográfico de menos (−)."""
    if pd.isna(valor):
        return "—"
    txt = f"{valor:.{casas}f}".replace(".", ",")
    if txt.startswith("-"):
        txt = "−" + txt[1:]
    return txt


def format_delta_br(pct: float) -> str:
    """Formata variação percentual com sinal explícito (+ ou −) e 1 casa decimal."""
    if pd.isna(pct):
        return "—"
    if abs(pct) < 0.05:
        return "0,0%"
    sinal = "+" if pct > 0 else "−"
    return f"{sinal}{abs(pct):.1f}%".replace(".", ",")


def obter_polaridade(indicador: str, pct: float) -> dict:
    """
    Define a semântica visual da variação percentual.
    Para crimes em geral: queda é boa (--good, verde), aumento é ruim (--bad, vermelho).
    Para drogas e armas: neutro (--ink-80 / --ink-40).
    """
    if indicador in INDICADORES_NEUTROS:
        return {
            "cor": "rgba(28, 28, 28, 0.80)",
            "cor_segmento": "rgba(28, 28, 28, 0.40)",
            "classe": "neutral",
            "seta": "↗" if pct > 0 else ("↘" if pct < 0 else "→"),
        }

    if pct < -0.05:
        return {
            "cor": "#0F7B5F",  # --good (queda em crime é desejável)
            "cor_segmento": "#0F7B5F",
            "classe": "good",
            "seta": "↘",
        }
    elif pct > 0.05:
        return {
            "cor": "#C0362C",  # --bad (aumento em crime é indesejável)
            "cor_segmento": "#C0362C",
            "classe": "bad",
            "seta": "↗",
        }
    else:
        return {
            "cor": "rgba(28, 28, 28, 0.80)",
            "cor_segmento": "rgba(28, 28, 28, 0.40)",
            "classe": "neutral",
            "seta": "→",
        }


# ==============================================================================
# 4. CARREGAMENTO DOS DADOS COM CACHE
# ==============================================================================


@st.cache_data
def carregar_dados():
    """Lê a base mensal do SINESP e a malha geográfica das 27 UFs em GeoJSON."""
    diretorio_dados = Path(__file__).resolve().parents[2] / "dados"
    csv_path = diretorio_dados / "sinesp_uf_mensal.csv"
    geojson_path = diretorio_dados / "br_uf.geojson"

    # Leitura do CSV com tipos garantidos
    df = pd.read_csv(csv_path)
    df["comparavel"] = df["comparavel"].astype(str).str.lower() == "true"
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")

    # Leitura do GeoJSON das 27 UFs
    with open(geojson_path, "r", encoding="utf-8") as f_geo:
        geojson = json.load(f_geo)

    return df, geojson


def _area(anel):
    """Área assinada de um anel (>0 = anti-horário)."""
    return sum(
        x0 * y1 - x1 * y0
        for (x0, y0), (x1, y1) in zip(anel, anel[1:] + anel[:1])
    ) / 2


def reorientar(geojson: dict) -> dict:
    """O Plotly (d3) preenche o mundo todo se o anel externo for anti-horário.
    Aqui deixamos os anéis externos horários e os buracos anti-horários."""
    for feat in geojson["features"]:
        geom = feat["geometry"]
        poligonos = (
            [geom["coordinates"]]
            if geom["type"] == "Polygon"
            else geom["coordinates"]
        )
        for pol in poligonos:
            for i, anel in enumerate(pol):
                horario = _area(anel[:-1]) < 0
                if horario != (i == 0):
                    anel.reverse()
    return geojson


df_sinesp, geojson_brasil = carregar_dados()
geojson_brasil = reorientar(geojson_brasil)

# ==============================================================================
# 5. CÁLCULO DOS 4 KPIS FIXOS (BLOCO P1)
# ==============================================================================


@st.cache_data
def calcular_kpis_fixos(df: pd.DataFrame, m0: int, m1: int):
    """
    Calcula os 4 KPIs de referência para o período comparável (jan-set):
    Homicídio doloso, Latrocínio, Feminicídio e Estupro.
    """
    config_kpis = [
        ("Homicídio doloso", "blue"),
        ("Latrocínio", "lav"),
        ("Feminicídio", "blue"),
        ("Estupro", "lav"),
    ]

    df_comp = df[df["mes"].between(m0, m1)]  # mesmos meses nos dois anos
    resultado = []

    for ind_nome, cor_fundo in config_kpis:
        sub = df_comp[df_comp["indicador"] == ind_nome]
        tot_2025 = sub[sub["ano"] == 2025]["valor"].sum()
        tot_2026 = sub[sub["ano"] == 2026]["valor"].sum()

        pct = ((tot_2026 / tot_2025) - 1.0) * 100.0 if tot_2025 > 0 else 0.0
        pol = obter_polaridade(ind_nome, pct)

        resultado.append(
            {
                "indicador": ind_nome,
                "cor_fundo": cor_fundo,
                "tot_2026": tot_2026,
                "tot_2025": tot_2025,
                "delta_pct": pct,
                "delta_str": f"{format_delta_br(pct)} {pol['seta']}",
                "classe_delta": pol["classe"],
                "vs_str": f"vs {format_int_br(tot_2025)} em {rotulo_intervalo(m0, m1)} 2025",
            }
        )

    return resultado



# ==============================================================================
# 6. SELETOR PRINCIPAL NA BARRA LATERAL (MENU COMPLETO COM 15 OPÇÕES)
# ==============================================================================

# Cabeçalho da barra lateral no padrão SnowUI
# Marca da ferramenta: ícone do Streamlit inline, na cor da marca (#FF4B4B)
LOGO_SVG = (Path(__file__).resolve().parent / "logo_streamlit.svg").read_text(
    encoding="utf-8"
).replace("<svg ", '<svg width="24" height="24" fill="#FF4B4B" ', 1)

st.sidebar.markdown(
    html(f"""
    <div class="brand">
        <span class="brand-logo">{LOGO_SVG}</span>
        <div>
            <div class="brand-title">Segurança pública no Brasil</div>
            <div class="brand-sub">Painel em <strong>Streamlit</strong></div>
        </div>
    </div>
    <div class="sidebar-divider"></div>
    <div class="sidebar-label">Selecione o indicador</div>
    """),
    unsafe_allow_html=True,
)

# Lista os 15 indicadores diretamente no rádio com legendas da categoria
indicador_selecionado = st.sidebar.radio(
    label="Indicador",
    options=TODOS_INDICADORES,
    index=0,  # "Homicídio doloso" como padrão
    captions=[MAPA_INDICADOR_GRUPO[ind] for ind in TODOS_INDICADORES],
    label_visibility="collapsed",
)

# ==============================================================================
# 7. CÁLCULO DAS MÉTRICAS POR UF E SÉRIE MENSAL PARA O INDICADOR ATIVO
# ==============================================================================


@st.cache_data
def calcular_metricas_uf(df: pd.DataFrame, indicador: str, m0: int, m1: int):
    """
    Calcula totais e taxas por 100 mil habitantes para cada uma das 27 UFs.
    Taxa = soma(valor) / populacao_uf_naquele_ano * 100.000.
    """
    df_comp = df[(df["indicador"] == indicador) & df["mes"].between(m0, m1)]

    # Soma de ocorrências/vítimas por UF e ano
    soma = (
        df_comp.groupby(["uf", "uf_nome", "ano"])["valor"]
        .sum()
        .unstack("ano", fill_value=0)
    )

    # População única de cada UF naquele ano
    pop_2025 = (
        df_comp[df_comp["ano"] == 2025].groupby("uf")["populacao"].first()
    )
    pop_2026 = (
        df_comp[df_comp["ano"] == 2026].groupby("uf")["populacao"].first()
    )

    res = pd.DataFrame(index=soma.index)
    res["valor_2025"] = soma[2025]
    res["valor_2026"] = soma[2026]
    res["pop_2025"] = pop_2025
    res["pop_2026"] = pop_2026

    # Taxas por 100 mil habitantes (sem anualização)
    res["taxa_2025"] = (res["valor_2025"] / res["pop_2025"]) * 100000.0
    res["taxa_2026"] = (res["valor_2026"] / res["pop_2026"]) * 100000.0
    res["delta_pct"] = (
        (res["valor_2026"] / res["valor_2025"]) - 1.0
    ) * 100.0

    return res.reset_index()


@st.cache_data
def calcular_serie_mensal(df: pd.DataFrame, indicador: str, m0: int, m1: int):
    """
    Calcula a evolução mensal do indicador no Brasil:
    - 2025: ano completo (meses 1 a 12)
    - 2026: período disponível (meses 1 a 9)
    """
    df_ind = df[df["indicador"] == indicador]
    unidade = (
        df_ind["unidade"].dropna().iloc[0]
        if not df_ind.empty
        else "ocorrências"
    )

    mensal = df_ind.groupby(["ano", "mes"])["valor"].sum().unstack("ano")

    # Totais no período comparável (jan-set) para a legenda do cabeçalho
    df_comp = df_ind[df_ind["mes"].between(m0, m1)]
    tot_2026_comp = df_comp[df_comp["ano"] == 2026]["valor"].sum()
    tot_2025_comp = df_comp[df_comp["ano"] == 2025]["valor"].sum()

    return mensal, unidade, tot_2026_comp, tot_2025_comp


AJUDA_P1 = (
    "Cada cartão soma o crime em todo o Brasil nos meses do filtro de 2026 e compara com os mesmos "
    "meses de 2025: Δ% = (2026 ÷ 2025 − 1) × 100. ▼ verde é queda (melhora) e ▲ vermelho é alta "
    "(piora). Estes quatro cartões não mudam com o menu: são os crimes que a página acompanha sempre."
)
AJUDA_P2 = (
    "A cor de cada estado é a taxa de {ind} por 100 mil habitantes em 2026, nos meses do filtro: "
    "casos ÷ população do estado × 100 mil. Quanto mais escuro, maior o risco para cada morador. "
    "A taxa, e não a contagem, permite comparar estados grandes e pequenos. O ranking lista os 5 "
    "maiores. A taxa não é anualizada: com jan–jun, é a taxa de seis meses."
)
AJUDA_P3 = (
    "Cada linha é um estado: o ponto claro é a taxa de 2025 e o escuro, a de 2026, nos mesmos meses. "
    "Ponto escuro à esquerda do claro: a taxa caiu; à direita: subiu. Quanto maior a distância, "
    "maior a mudança. Estados com poucos casos oscilam mais por acaso."
)
AJUDA_P4 = (
    "Total de {ind} no Brasil, mês a mês: linha cheia = 2026 (até setembro), tracejada = 2025 "
    "(ano inteiro). A faixa sombreada marca os meses do filtro. Se a linha cheia fica abaixo da "
    "tracejada em quase todos os meses, a mudança é do ano todo, e não de um mês isolado."
)

# Topo da página (preenchido mais abaixo) e filtro temporal de meses
topo = st.container()
col_filtro, _ = st.columns([2, 3])
with col_filtro:
    mes_ini_txt, mes_fim_txt = st.select_slider(
        "Período (meses; vale para 2025 e 2026)",
        options=MESES,
        value=("jan", "set"),
    )
# Se o início vier depois do fim, troca os dois
m0, m1 = sorted([MESES.index(mes_ini_txt) + 1, MESES.index(mes_fim_txt) + 1])
rot = rotulo_intervalo(m0, m1)
kpis_dados = calcular_kpis_fixos(df_sinesp, m0, m1)

dados_uf = calcular_metricas_uf(df_sinesp, indicador_selecionado, m0, m1)
serie_mensal, unidade_indicador, total_2026_comp, total_2025_comp = (
    calcular_serie_mensal(df_sinesp, indicador_selecionado, m0, m1)
)

# ==============================================================================
# 8. CONSTRUÇÃO VISUAL DA PÁGINA
# ==============================================================================

LOGO_SVG_TOPO = LOGO_SVG.replace('width="24" height="24"', 'width="22" height="22" aria-hidden="true"', 1)

# Topo: trilha de navegação (breadcrumb) e chip do período de comparação
with topo:
    st.markdown(
        html(f"""
        <div class="top-nav">
            <div class="breadcrumb">
                <span class="breadcrumb-root">Painéis</span>
                <span class="breadcrumb-sep">/</span>
                <span class="breadcrumb-current">Segurança pública</span>
            </div>
            <div class="period-chip">{rot} · 2026 × 2025</div>
        </div>
        <h1 class="page-title">Segurança pública no Brasil</h1>
        <h2 class="page-tool"><span class="page-tool-logo">{LOGO_SVG_TOPO}</span>Painel em <strong>Streamlit</strong></h2>
        """),
        unsafe_allow_html=True,
    )

# BLOCO P1: 4 Cartões de KPI fixos (renderizados via HTML com estilo SnowUI)
kpis_html = ['<div class="kpi-grid">']
for item in kpis_dados:
    kpis_html.append(
        html(f"""
        <div class="kpi-card {item['cor_fundo']}">
            <div class="kpi-label">{item['indicador']}</div>
            <div class="kpi-middle">
                <span class="kpi-number">{format_int_br(item['tot_2026'])}</span>
                <span class="kpi-delta {item['classe_delta']}">{item['delta_str']}</span>
            </div>
            <div class="kpi-footer">{item['vs_str']}</div>
        </div>
        """)
    )
kpis_html.append("</div>")
with st.container(key="cab_p1"):
    c_vg, c_aj = st.columns([30, 1], vertical_alignment="center")
    with c_vg:
        st.markdown('<div class="visao-geral">Visão geral</div>', unsafe_allow_html=True)
    with c_aj:
        ajuda("p1", AJUDA_P1)
st.markdown("".join(kpis_html), unsafe_allow_html=True)

# Grade principal em 7 colunas (esquerda) e 5 colunas (direita)
col_esq, col_dir = st.columns([7, 5])

# ------------------------------------------------------------------------------
# COLUNA ESQUERDA (7 colunas): P2 (Mapa + Ranking Top 5) e P4 (Tendência)
# ------------------------------------------------------------------------------
with col_esq:
    with st.container(key="card_p2"):
        # --------------------------------------------------------------------------
        # P2: MAPA COROPLÉTICO + RANKING TOP 5
        # --------------------------------------------------------------------------
        titulo_cartao(
            "p2",
            "Onde o risco é maior?",
            f"{indicador_selecionado} · taxa por 100 mil hab. · {rot} 2026",
            AJUDA_P2.format(ind=indicador_selecionado),
        )

        # Subdivisão interna de P2: 60% mapa coroplético e 40% ranking Top 5
        col_mapa, col_rank = st.columns([6, 4])

        with col_mapa:
            # Cálculo das 5 classes por quantis para a escala sequencial SnowUI
            valores_taxa = dados_uf["taxa_2026"].values
            q_limites = [
                float(np.quantile(valores_taxa, q))
                for q in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
            ]

            # Atribuição da classe (0 a 4) para cada UF
            classes_uf = []
            for v in valores_taxa:
                if v <= q_limites[1]:
                    c = 0
                elif v <= q_limites[2]:
                    c = 1
                elif v <= q_limites[3]:
                    c = 2
                elif v <= q_limites[4]:
                    c = 3
                else:
                    c = 4
                classes_uf.append(c)

            dados_uf["classe"] = classes_uf

            # Paleta sequencial SnowUI (--seq-0 a --seq-4)
            seq_cores = ["#FFF1E3", "#FFD2A8", "#FFA766", "#E07834", "#9C4415"]  # --seq (âmbar)
            escala_discreta = [
                [0.0, seq_cores[0]],
                [0.2, seq_cores[0]],
                [0.2, seq_cores[1]],
                [0.4, seq_cores[1]],
                [0.4, seq_cores[2]],
                [0.6, seq_cores[2]],
                [0.6, seq_cores[3]],
                [0.8, seq_cores[3]],
                [0.8, seq_cores[4]],
                [1.0, seq_cores[4]],
            ]

            # Montagem dos dados de hover enriquecidos
            customdata_mapa = []
            for _, row in dados_uf.iterrows():
                customdata_mapa.append(
                    [
                        row["uf_nome"],
                        format_decimal_br(row["taxa_2026"], 2),
                        format_decimal_br(row["taxa_2025"], 2),
                        format_delta_br(row["delta_pct"]),
                    ]
                )

            fig_mapa = go.Figure(
                data=go.Choropleth(
                    geojson=geojson_brasil,
                    featureidkey="properties.uf",
                    locations=dados_uf["uf"],
                    z=dados_uf["classe"],
                    zmin=0,
                    zmax=4,
                    colorscale=escala_discreta,
                    showscale=False,
                    marker_line_color="#FFFFFF",
                    marker_line_width=0.6,
                    customdata=customdata_mapa,
                    hovertemplate=(
                        "<b>%{customdata[0]}</b><br>"
                        "Taxa 2026: %{customdata[1]} por 100k<br>"
                        "Taxa 2025: %{customdata[2]} por 100k<br>"
                        "Variação: %{customdata[3]}<extra></extra>"
                    ),
                )
            )

            fig_mapa.update_geos(
                fitbounds="locations",
                visible=False,
                projection_type="mercator",
                domain=dict(x=[0, 1], y=[0, 1]),  # ocupa toda a área da figura
                bgcolor="rgba(0,0,0,0)",
            )
            fig_mapa.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                separators=",.",  # pt-BR: 3.000 e 9,68
        font=dict(family="Inter, sans-serif"),
        paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=340,
            )

            st.plotly_chart(
                fig_mapa,
                width="stretch",
                config={"displayModeBar": False},
            )

            # Legenda das 5 classes quantílicas abaixo do mapa
            legenda_html = ['<div class="map-legend">']
            textos_legenda = [
                f"≤ {format_decimal_br(q_limites[1], 2)}",
                f"{format_decimal_br(q_limites[1], 2)}–{format_decimal_br(q_limites[2], 2)}",
                f"{format_decimal_br(q_limites[2], 2)}–{format_decimal_br(q_limites[3], 2)}",
                f"{format_decimal_br(q_limites[3], 2)}–{format_decimal_br(q_limites[4], 2)}",
                f"≥ {format_decimal_br(q_limites[4], 2)}",
            ]
            for cor, txt in zip(seq_cores, textos_legenda):
                legenda_html.append(
                    f'<div class="legend-item"><span class="legend-swatch" style="background:{cor};"></span><span class="legend-text">{txt}</span></div>'
                )
            legenda_html.append("</div>")
            st.markdown("".join(legenda_html), unsafe_allow_html=True)

        with col_rank:
            # Ranking Top 5 ordenado pela maior taxa em 2026
            top5 = (
                dados_uf.sort_values("taxa_2026", ascending=False)
                .head(5)
                .reset_index(drop=True)
            )
            maior_taxa_top = top5["taxa_2026"].max()

            rank_html = ['<div class="ranking-box">']
            rank_html.append(
                '<div class="ranking-header-title">Maiores taxas por UF</div>'
            )

            for _, row in top5.iterrows():
                largura_pct = (
                    (row["taxa_2026"] / maior_taxa_top) * 100.0
                    if maior_taxa_top > 0
                    else 0
                )
                val_formatado = format_decimal_br(row["taxa_2026"], 2)

                rank_html.append(
                    html(f"""
                    <div class="ranking-row-item">
                        <div class="ranking-labels">
                            <span class="ranking-name">{row['uf_nome']}</span>
                            <span class="ranking-val">{val_formatado}</span>
                        </div>
                        <div class="ranking-track">
                            <div class="ranking-fill" style="width: {largura_pct:.1f}%;"></div>
                        </div>
                    </div>
                    """)
                )
            rank_html.append("</div>")
            st.markdown("".join(rank_html), unsafe_allow_html=True)

    with st.container(key="card_p4"):
        # --------------------------------------------------------------------------
        # P4: TENDÊNCIA TEMPORAL MENSAL
        # --------------------------------------------------------------------------
        titulo_cartao(
            "p4",
            "A mudança é de um mês ou do ano todo?",
            f"{indicador_selecionado} · total no Brasil por mês ({unidade_indicador})",
            AJUDA_P4.format(ind=indicador_selecionado),
        )
        st.markdown(
            html(f"""
            <div class="trend-legend-header">
                <span class="legend-dot-2026">● 2026 <strong>{format_int_br(total_2026_comp)}</strong></span>
                <span class="legend-sep">·</span>
                <span class="legend-dot-2025">○ 2025 <strong>{format_int_br(total_2025_comp)}</strong></span>
            </div>
            """),
            unsafe_allow_html=True,
        )

        meses_abrev = [
            "jan",
            "fev",
            "mar",
            "abr",
            "mai",
            "jun",
            "jul",
            "ago",
            "set",
            "out",
            "nov",
            "dez",
        ]

        # Série 2025 completa (jan a dez)
        y_2025 = (
            [serie_mensal[2025].get(m, np.nan) for m in range(1, 13)]
            if 2025 in serie_mensal.columns
            else []
        )
        # Série 2026 incompleta (jan a set)
        y_2026 = (
            [serie_mensal[2026].get(m, np.nan) for m in range(1, 10)]
            if 2026 in serie_mensal.columns
            else []
        )

        fig_tendencia = go.Figure()

        # Linha 2025: tracejada, cor --data-2 (#F2BE94)
        fig_tendencia.add_trace(
            go.Scatter(
                x=meses_abrev,
                y=y_2025,
                mode="lines",
                name="2025",
                line=dict(color="#F2BE94", width=2, dash="dash"),
                hovertemplate="2025 · %{x}: <b>%{y:,.0f}</b><extra></extra>",
            )
        )

        # Linha 2026: sólida, cor --data-1 (#4A2412)
        fig_tendencia.add_trace(
            go.Scatter(
                x=meses_abrev[: len(y_2026)],
                y=y_2026,
                mode="lines",
                name="2026",
                line=dict(color="#4A2412", width=2),
                hovertemplate="2026 · %{x}: <b>%{y:,.0f}</b><extra></extra>",
            )
        )

        # Rótulos diretos no último ponto de cada série
        if len(y_2025) >= 12 and not pd.isna(y_2025[11]):
            fig_tendencia.add_annotation(
                x="dez",
                y=y_2025[11],
                text=f" {format_int_br(y_2025[11])}",
                showarrow=False,
                xanchor="left",
                font=dict(size=11, color="#C98A5B", family="Inter"),
            )
        if len(y_2026) >= 9 and not pd.isna(y_2026[8]):
            fig_tendencia.add_annotation(
                x="set",
                y=y_2026[8],
                text=f" {format_int_br(y_2026[8])}",
                showarrow=False,
                xanchor="left",
                font=dict(size=11, color="#4A2412", family="Inter"),
            )

        # Sombreia o intervalo escolhido (posições numéricas em eixo categórico)
        fig_tendencia.add_vrect(
            x0=m0 - 1.5,
            x1=m1 - 0.5,
            fillcolor="rgba(28,28,28,0.05)",
            line_width=0,
            layer="below",
        )

        fig_tendencia.update_layout(
            showlegend=False,
            margin=dict(l=35, r=45, t=15, b=25),
            separators=",.",  # pt-BR: 3.000 e 9,68
        font=dict(family="Inter, sans-serif"),
        paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=260,
            xaxis=dict(
                tickangle=0,  # meses sempre na horizontal, mesmo em tela estreita
                showline=False,
                ticks="",
                zeroline=False,
                gridcolor="rgba(0,0,0,0)",
                tickfont=dict(
                    size=10, color="rgba(28, 28, 28, 0.40)", family="Inter"
                ),
            ),
            yaxis=dict(
                rangemode="tozero",
                tickformat=",.0f",  # milhar com ponto (separators=",.")
                showline=False,
                ticks="",
                zeroline=False,
                gridcolor="rgba(28, 28, 28, 0.10)",
                tickfont=dict(
                    size=11, color="rgba(28, 28, 28, 0.40)", family="Inter"
                ),
            ),
        )

        st.plotly_chart(
            fig_tendencia,
            width="stretch",
            config={"displayModeBar": False},
        )

# ------------------------------------------------------------------------------
# COLUNA DIREITA (5 colunas): P3 (Gráfico Pareado / Dumbbell das 27 UFs)
# ------------------------------------------------------------------------------
with col_dir:
    with st.container(key="card_p3"):
        titulo_cartao(
            "p3",
            "Quais estados melhoraram ou pioraram?",
            f"{indicador_selecionado} · taxa por 100 mil hab. · {rot} 2025 → 2026",
            AJUDA_P3,
        )

        # Ordenação decrescente: estado com maior taxa de 2026 fica no topo
        ufs_ordenadas = dados_uf.sort_values(
            "taxa_2026", ascending=False
        ).reset_index(drop=True)
        lista_ufs_ordem = list(ufs_ordenadas["uf"])

        fig_dumbbell = go.Figure()

        # Segmentos de reta conectando taxa 2025 à taxa 2026
        for _, row in ufs_ordenadas.iterrows():
            t25 = row["taxa_2025"]
            t26 = row["taxa_2026"]
            uf = row["uf"]
            pol = obter_polaridade(indicador_selecionado, row["delta_pct"])

            fig_dumbbell.add_shape(
                type="line",
                x0=t25,
                x1=t26,
                y0=uf,
                y1=uf,
                line=dict(color=pol["cor_segmento"], width=2),
            )

        # Ponto de 2025: círculo de 6 px em --data-2 (#F2BE94)
        fig_dumbbell.add_trace(
            go.Scatter(
                x=ufs_ordenadas["taxa_2025"],
                y=ufs_ordenadas["uf"],
                mode="markers",
                name="2025",
                marker=dict(color="#F2BE94", size=6),
                customdata=ufs_ordenadas[
                    ["uf_nome", "taxa_2025", "taxa_2026", "delta_pct"]
                ].values,
                hovertemplate=(
                    "<b>%{customdata[0]} (%{y})</b><br>"
                    "Taxa 2025: %{customdata[1]:.2f}<br>"
                    "Taxa 2026: %{customdata[2]:.2f}<br>"
                    "Variação: %{customdata[3]:+.1f}%<extra></extra>"
                ),
            )
        )

        # Ponto de 2026: círculo de 8 px em --data-1 (#4A2412)
        fig_dumbbell.add_trace(
            go.Scatter(
                x=ufs_ordenadas["taxa_2026"],
                y=ufs_ordenadas["uf"],
                mode="markers",
                name="2026",
                marker=dict(color="#4A2412", size=8),
                customdata=ufs_ordenadas[
                    ["uf_nome", "taxa_2025", "taxa_2026", "delta_pct"]
                ].values,
                hovertemplate=(
                    "<b>%{customdata[0]} (%{y})</b><br>"
                    "Taxa 2025: %{customdata[1]:.2f}<br>"
                    "Taxa 2026: %{customdata[2]:.2f}<br>"
                    "Variação: %{customdata[3]:+.1f}%<extra></extra>"
                ),
            )
        )

        fig_dumbbell.update_layout(
            showlegend=False,
            margin=dict(l=40, r=20, t=10, b=25),
            separators=",.",  # pt-BR: 3.000 e 9,68
        font=dict(family="Inter, sans-serif"),
        paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=660,
            xaxis=dict(
                rangemode="tozero",
                tickformat=",.0f",  # milhar com ponto (separators=",.")
                showline=False,
                ticks="",
                zeroline=False,
                gridcolor="rgba(28, 28, 28, 0.10)",
                tickfont=dict(
                    size=11, color="rgba(28, 28, 28, 0.40)", family="Inter"
                ),
            ),
            yaxis=dict(
                showline=False,
                ticks="",
                zeroline=False,
                categoryorder="array",
                categoryarray=lista_ufs_ordem,
                autorange="reversed",  # Garante que a 1ª UF da lista (maior) fique no topo
                gridcolor="rgba(0,0,0,0)",
                tickfont=dict(
                    size=11, color="rgba(28, 28, 28, 0.80)", family="Inter"
                ),
            ),
        )

        st.plotly_chart(
            fig_dumbbell,
            width="stretch",
            config={"displayModeBar": False},
        )

# ==============================================================================
# 9. SEÇÃO RODAPÉ: "SOBRE OS DADOS" (ESTILO NOTIFICAÇÕES SNOWUI)
# ==============================================================================

st.markdown(
    html("""
    <div class="about-card">
        <div class="about-card-title">Sobre os dados e metodologia</div>
        <div class="about-grid">
            <div class="about-item">
                <div class="about-icon">1</div>
                <div class="about-content">
                    <div class="about-heading">Fonte</div>
                    <div class="about-desc">SINESP VDE / Ministério da Justiça e Segurança Pública, bases de 2025 e 2026 (extraídas em 11/11/2026). População: estimativas do IBGE para 2025 e 2026.</div>
                </div>
            </div>
            <div class="about-item">
                <div class="about-icon">2</div>
                <div class="about-content">
                    <div class="about-heading">Período comparável</div>
                    <div class="about-desc">jan–set. A base de 2026 vai até setembro.</div>
                </div>
            </div>
            <div class="about-item">
                <div class="about-icon">3</div>
                <div class="about-content">
                    <div class="about-heading">Dados preliminares</div>
                    <div class="about-desc">Os estados ainda podem revisar os números.</div>
                </div>
            </div>
            <div class="about-item">
                <div class="about-icon">4</div>
                <div class="about-content">
                    <div class="about-heading">Atenção a MS</div>
                    <div class="about-desc">A série de homicídios muda de patamar entre 2025 e 2026. Compare com cautela.</div>
                </div>
            </div>
            <div class="about-item">
                <div class="about-icon">5</div>
                <div class="about-content">
                    <div class="about-heading">Como ler a taxa</div>
                    <div class="about-desc">ocorrências (ou vítimas) no período ÷ população × 100 mil. Não é anualizada.</div>
                </div>
            </div>
        </div>
    </div>
    """),
    unsafe_allow_html=True,
)
