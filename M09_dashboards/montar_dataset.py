"""Monta o dataset dos painéis de segurança pública (M09 — Dashboards).

Fontes
------
- SINESP VDE (Ministério da Justiça e Segurança Pública): bases 2025 e 2026,
  uma linha por município x mês x evento.
  https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/dados-nacionais-1/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-sinesp-vde-2022-e-2023
- IBGE: população residente estimada por UF (SIDRA, tabela 6579), nomes e
  regiões das UFs (API de localidades) e malha das UFs (API de malhas).

Saídas (em dados/)
------------------
- sinesp_uf_mensal.csv / .parquet: UF x mês x indicador, com a população da UF
  no ano. É a base de todos os painéis (Quarto, Dash, Streamlit, Apps Script,
  Looker Studio).
- br_uf.geojson: contorno das 27 UFs, com as propriedades `uf` e `nome`.
- conferencia.csv / .json: totais de jan-set de 2025 e 2026 (a "tabela
  dinâmica" que todo painel precisa reproduzir).

Decisões
--------
- O SINESP mede cada evento numa coluna: vítimas (`total_vitima`),
  ocorrências (`total`) ou quilos (`total_peso`). MEDIDAS diz qual usar.
- Linhas repetidas no mesmo mês (ex.: tentativa de homicídio, "NÃO
  INFORMADO") são somadas, como pedem as notas do SINESP.
- Quando um evento tem registro estadual e federal (PF, PRF), o valor da UF
  soma as fontes. "Mortes no trânsito" vem só da PRF (rodovias federais) e
  fica separado das mortes no trânsito registradas pelos estados.
- Os eventos do Corpo de Bombeiros ficam de fora: não são indicadores de
  segurança pública.
- Mês sem registro fica vazio (NaN), não zero.
- Os valores são inteiros (kg arredondados), para a planilha não confundir
  ponto decimal com separador de milhar.
- A taxa por 100 mil habitantes NÃO vem pronta: ela é soma(valor) /
  população x 100 mil, calculada depois de agregar. Média de taxas mensais
  dá resultado errado.

Uso
---
    python montar_dataset.py               # baixa o que faltar e monta
    python montar_dataset.py --sem-download  # usa só o que já está em dados/brutos/
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
PASTA_DADOS = AQUI / "dados"
PASTA_BRUTOS = PASTA_DADOS / "brutos"

URL_VDE = (
    "https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/"
    "estatistica/download/dnsp-base-de-dados/bancovde-{ano}.xlsx/@@download/file"
)
URL_POPULACAO = "https://apisidra.ibge.gov.br/values/t/6579/n3/all/v/9324/p/{anos}"
URL_UFS = "https://servicodados.ibge.gov.br/api/v1/localidades/estados"
URL_MALHA = (
    "https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"
    "?formato=application/vnd.geo%2Bjson&qualidade=minima&intrarregiao=UF"
)

# evento no SINESP -> (indicador no painel, categoria, coluna da medida, unidade)
MEDIDAS = {
    "Homicídio doloso": ("Homicídio doloso", "Crimes contra a vida", "total_vitima", "vítimas"),
    "Roubo seguido de morte (latrocínio)": ("Latrocínio", "Crimes contra a vida", "total_vitima", "vítimas"),
    "Lesão corporal seguida de morte": ("Lesão corporal seguida de morte", "Crimes contra a vida", "total_vitima", "vítimas"),
    "Morte por intervenção de Agente do Estado": ("Morte por intervenção de agente do Estado", "Crimes contra a vida", "total_vitima", "vítimas"),
    "Tentativa de homicídio": ("Tentativa de homicídio", "Crimes contra a vida", "total_vitima", "vítimas"),
    "Feminicídio": ("Feminicídio", "Violência contra a mulher e sexual", "total_vitima", "vítimas"),
    "Tentativa de feminicídio": ("Tentativa de feminicídio", "Violência contra a mulher e sexual", "total_vitima", "vítimas"),
    "Estupro": ("Estupro", "Violência contra a mulher e sexual", "total_vitima", "vítimas"),
    "Estupro de vulnerável": ("Estupro de vulnerável", "Violência contra a mulher e sexual", "total_vitima", "vítimas"),
    "Roubo de veículo": ("Roubo de veículo", "Patrimônio", "total", "ocorrências"),
    "Furto de veículo": ("Furto de veículo", "Patrimônio", "total", "ocorrências"),
    "Roubo de carga": ("Roubo de carga", "Patrimônio", "total", "ocorrências"),
    "Roubo a instituição financeira": ("Roubo a instituição financeira", "Patrimônio", "total", "ocorrências"),
    "Tráfico de drogas": ("Tráfico de drogas", "Drogas e armas", "total", "ocorrências"),
    "Apreensão de Cocaína": ("Apreensão de cocaína", "Drogas e armas", "total_peso", "kg"),
    "Apreensão de Maconha": ("Apreensão de maconha", "Drogas e armas", "total_peso", "kg"),
    "Arma de Fogo Apreendida": ("Armas de fogo apreendidas", "Drogas e armas", "total", "armas"),
    "Morte no trânsito ou em decorrência dele (exceto homicídio doloso)": ("Mortes no trânsito", "Trânsito", "total_vitima", "vítimas"),
    "Mortes no trânsito": ("Mortes no trânsito (rodovias federais)", "Trânsito", "total_vitima", "vítimas"),
    "Suicídio": ("Suicídio", "Outras mortes", "total_vitima", "vítimas"),
    "Mortes a esclarecer (sem indício de crime)": ("Mortes a esclarecer", "Outras mortes", "total_vitima", "vítimas"),
    "Morte de Agente do Estado": ("Morte de agente do Estado", "Agentes do Estado", "total_vitima", "vítimas"),
    "Suicídio de Agente do Estado": ("Suicídio de agente do Estado", "Agentes do Estado", "total_vitima", "vítimas"),
    "Pessoa Desaparecida": ("Pessoas desaparecidas", "Pessoas", "total_vitima", "pessoas"),
    "Pessoa Localizada": ("Pessoas localizadas", "Pessoas", "total_vitima", "pessoas"),
    "Mandado de prisão cumprido": ("Mandados de prisão cumpridos", "Prisões", "total", "mandados"),
}
BOMBEIROS = {
    "Atendimento pré-hospitalar", "Busca e salvamento", "Combate a incêndios",
    "Emissão de Alvarás de licença", "Realização de vistorias",
}

# indicadores dos cartões de KPI dos painéis (P1) e indicador padrão (P2-P4)
KPIS = ["Homicídio doloso", "Latrocínio", "Feminicídio", "Estupro"]
INDICADOR_PADRAO = "Homicídio doloso"


# ---------------------------------------------------------------- download --

def baixar(url: str, destino: Path, tentativas: int = 5) -> Path:
    """Baixa `url` para `destino`, a menos que ele já exista.

    O gov.br derruba a conexão depois de alguns downloads seguidos, então
    tentamos de novo com espera crescente (20 s, 40 s, ...). O User-Agent de
    curl evita que o servidor devolva uma página HTML no lugar do arquivo.
    """
    if destino.exists() and destino.stat().st_size > 0:
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_suffix(destino.suffix + ".parcial")
    for i in range(1, tentativas + 1):
        try:
            if shutil.which("curl"):
                subprocess.run(
                    ["curl", "-sSL", "--fail", "-A", "curl/8", "-o", str(temporario), url],
                    check=True,
                )
            else:
                pedido = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
                with urllib.request.urlopen(pedido, timeout=120) as r:
                    temporario.write_bytes(r.read())
            temporario.rename(destino)
            print(f"  baixado: {destino.name} ({destino.stat().st_size / 1e6:.1f} MB)")
            return destino
        except Exception as erro:  # noqa: BLE001 - qualquer falha de rede vale nova tentativa
            espera = 20 * i
            print(f"  tentativa {i} falhou ({erro}); nova tentativa em {espera} s")
            time.sleep(espera)
    raise RuntimeError(
        f"Não consegui baixar {url}. Baixe pelo navegador e salve em {destino}."
    )


def ler_vde(ano: int, baixar_se_faltar: bool) -> pd.DataFrame:
    """Lê a base VDE de um ano. Guarda uma cópia em parquet para a próxima vez."""
    xlsx = PASTA_BRUTOS / f"bancovde-{ano}.xlsx"
    cache = xlsx.with_suffix(".parquet")
    if cache.exists():
        return pd.read_parquet(cache)
    if not xlsx.exists():
        if not baixar_se_faltar:
            raise FileNotFoundError(xlsx)
        baixar(URL_VDE.format(ano=ano), xlsx)
    print(f"  lendo {xlsx.name} (leva cerca de 1 minuto)...")
    bruto = pd.read_excel(xlsx)
    bruto.to_parquet(cache)
    return bruto


def ler_json(url: str, nome: str, baixar_se_faltar: bool):
    arquivo = PASTA_BRUTOS / nome
    if not arquivo.exists():
        if not baixar_se_faltar:
            raise FileNotFoundError(arquivo)
        baixar(url, arquivo)
    return json.loads(arquivo.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- montagem --

def agregar_por_uf(bruto: pd.DataFrame) -> pd.DataFrame:
    """De município x mês x evento para UF x mês x indicador."""
    eventos = set(bruto["evento"].unique())
    sem_regra = eventos - set(MEDIDAS) - BOMBEIROS
    assert not sem_regra, f"eventos sem regra de medida: {sem_regra}"

    partes = []
    for evento, (indicador, categoria, coluna, unidade) in MEDIDAS.items():
        linhas = bruto[bruto["evento"] == evento]
        # a coluna escolhida precisa ter dados para esse evento
        assert linhas[coluna].notna().any(), f"{evento}: coluna {coluna} vazia"
        soma = (
            linhas.groupby(["uf", "data_referencia"])[coluna]
            .sum(min_count=1)  # tudo vazio continua vazio, não vira zero
            .rename("valor")
            .reset_index()
        )
        soma["indicador"], soma["categoria"], soma["unidade"] = indicador, categoria, unidade
        partes.append(soma)
    return pd.concat(partes, ignore_index=True)


def completar_grade(df: pd.DataFrame) -> pd.DataFrame:
    """Garante uma linha por UF x mês x indicador; mês sem registro fica NaN."""
    meses = pd.Index(sorted(df["data_referencia"].unique()), name="data_referencia")
    ufs = pd.Index(sorted(df["uf"].unique()), name="uf")
    rotulos = df[["indicador", "categoria", "unidade"]].drop_duplicates()
    grade = (
        pd.MultiIndex.from_product([ufs, meses, rotulos["indicador"]], names=["uf", "data_referencia", "indicador"])
        .to_frame(index=False)
        .merge(rotulos, on="indicador")
    )
    return grade.merge(df, on=["uf", "data_referencia", "indicador", "categoria", "unidade"], how="left")


def tabela_ufs(baixar_se_faltar: bool) -> pd.DataFrame:
    ufs = ler_json(URL_UFS, "ibge_ufs.json", baixar_se_faltar)
    return pd.DataFrame(
        {
            "cod_uf": [u["id"] for u in ufs],
            "uf": [u["sigla"] for u in ufs],
            "uf_nome": [u["nome"] for u in ufs],
            "regiao": [u["regiao"]["nome"] for u in ufs],
        }
    )


def tabela_populacao(anos: list[int], baixar_se_faltar: bool) -> pd.DataFrame:
    """População estimada pelo IBGE por UF e ano. Ano sem estimativa usa a última."""
    pedidos = ",".join(str(a) for a in anos)
    linhas = ler_json(URL_POPULACAO.format(anos=pedidos), f"ibge_populacao_{pedidos.replace(',', '_')}.json", baixar_se_faltar)[1:]
    pop = pd.DataFrame(
        {"cod_uf": [int(r["D1C"]) for r in linhas], "ano": [int(r["D3N"]) for r in linhas], "populacao": [int(r["V"]) for r in linhas]}
    )
    for ano in anos:
        if ano not in set(pop["ano"]):
            ultimo = pop["ano"].max()
            print(f"  aviso: IBGE sem estimativa para {ano}; usando {ultimo}")
            pop = pd.concat([pop, pop[pop["ano"] == ultimo].assign(ano=ano)])
    return pop


def _area(anel: list) -> float:
    """Área com sinal (fórmula do laço): positiva = anti-horário."""
    return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(anel, anel[1:])) / 2


def _orientar_para_d3(geometria: dict) -> None:
    """Anel externo horário e buracos anti-horários.

    É o sentido que o d3-geo (usado pelo Plotly e pelo Observable Plot) espera.
    No sentido contrário, cada estado vira "o globo inteiro menos o estado" e o
    mapa aparece como um retângulo pintado. O ECharts aceita os dois sentidos.
    """
    poligonos = geometria["coordinates"] if geometria["type"] == "MultiPolygon" else [geometria["coordinates"]]
    for poligono in poligonos:
        for i, anel in enumerate(poligono):
            horario = _area(anel) < 0
            if horario != (i == 0):
                anel.reverse()


def salvar_malha(ufs: pd.DataFrame, baixar_se_faltar: bool) -> None:
    malha = ler_json(URL_MALHA, "ibge_malha_uf.json", baixar_se_faltar)
    por_codigo = ufs.set_index("cod_uf")
    for f in malha["features"]:
        cod = int(f["properties"]["codarea"])
        f["properties"] = {"uf": por_codigo.at[cod, "uf"], "nome": por_codigo.at[cod, "uf_nome"]}
        _orientar_para_d3(f["geometry"])
    (PASTA_DADOS / "br_uf.geojson").write_text(json.dumps(malha, ensure_ascii=False), encoding="utf-8")


# ------------------------------------------------------------- conferência --

def conferir(df: pd.DataFrame, bruto: pd.DataFrame, anos: list[int]) -> pd.DataFrame:
    """Totais de jan até o último mês comum, por ano: a referência dos painéis."""
    periodo = df[df["comparavel"]]
    ano_a, ano_b = anos[0], anos[-1]

    # 1. a soma do dataset bate com a soma direta do bruto
    for evento, (indicador, _, coluna, _) in MEDIDAS.items():
        b = bruto[(bruto["evento"] == evento) & (bruto["data_referencia"].dt.month <= periodo["mes"].max())]
        esperado = round(b[coluna].sum())
        obtido = periodo.loc[periodo["indicador"] == indicador, "valor"].sum()
        assert abs(esperado - obtido) <= len(b) * 0.5 + 1, f"{indicador}: {esperado} != {obtido}"
    # 2. não há chave repetida
    assert not df.duplicated(["uf", "data", "indicador"]).any(), "chave UF x mês x indicador repetida"

    pop = periodo.drop_duplicates(["uf", "ano"]).groupby("ano")["populacao"].sum()
    nacional = periodo.groupby(["indicador", "unidade", "ano"])["valor"].sum().unstack("ano")
    nacional.columns = [f"valor_{c}" for c in nacional.columns]
    for ano in (ano_a, ano_b):
        nacional[f"taxa_100k_{ano}"] = nacional[f"valor_{ano}"] / pop[ano] * 1e5
    nacional["variacao_pct"] = (nacional[f"valor_{ano_b}"] / nacional[f"valor_{ano_a}"] - 1) * 100
    nacional = nacional.reset_index().assign(escopo="Brasil", uf="BR")

    p = periodo[periodo["indicador"] == INDICADOR_PADRAO]
    por_uf = p.groupby(["uf", "ano"]).agg(valor=("valor", "sum"), populacao=("populacao", "first")).unstack("ano")
    tabela_uf = pd.DataFrame(index=por_uf.index)
    for ano in (ano_a, ano_b):
        tabela_uf[f"valor_{ano}"] = por_uf[("valor", ano)]
        tabela_uf[f"taxa_100k_{ano}"] = por_uf[("valor", ano)] / por_uf[("populacao", ano)] * 1e5
    tabela_uf["variacao_pct"] = (tabela_uf[f"valor_{ano_b}"] / tabela_uf[f"valor_{ano_a}"] - 1) * 100
    tabela_uf = tabela_uf.reset_index().assign(escopo="UF", indicador=INDICADOR_PADRAO, unidade="vítimas")

    colunas = ["escopo", "uf", "indicador", "unidade",
               f"valor_{ano_a}", f"valor_{ano_b}", "variacao_pct", f"taxa_100k_{ano_a}", f"taxa_100k_{ano_b}"]
    return pd.concat([nacional[colunas], tabela_uf[colunas]], ignore_index=True)


# -------------------------------------------------------------------- main --

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--anos", type=int, nargs="+", default=[2025, 2026])
    ap.add_argument("--sem-download", action="store_true", help="não baixa nada; usa dados/brutos/")
    args = ap.parse_args()
    anos, baixar_se_faltar = sorted(args.anos), not args.sem_download
    PASTA_DADOS.mkdir(exist_ok=True)

    print("1/5 SINESP VDE")
    bruto = pd.concat([ler_vde(a, baixar_se_faltar) for a in anos], ignore_index=True)
    bruto = bruto[~bruto["evento"].isin(BOMBEIROS)]

    print("2/5 agregando por UF x mês x indicador")
    df = completar_grade(agregar_por_uf(bruto))
    df["valor"] = df["valor"].round().astype("Int64")

    print("3/5 IBGE: UFs, população e malha")
    ufs = tabela_ufs(baixar_se_faltar)
    pop = tabela_populacao(anos, baixar_se_faltar)
    df["ano"] = df["data_referencia"].dt.year
    df["mes"] = df["data_referencia"].dt.month
    df = df.merge(ufs, on="uf", how="left").merge(pop, on=["cod_uf", "ano"], how="left")
    assert df["populacao"].notna().all() and df["uf_nome"].notna().all()
    df["uf_iso"] = "BR-" + df["uf"]
    salvar_malha(ufs, baixar_se_faltar)

    print("4/5 período comparável")
    # último mês com registro no ano mais recente (2026: setembro)
    ultimo_mes = int(df.loc[(df["ano"] == anos[-1]) & df["valor"].notna(), "mes"].max())
    df["comparavel"] = df["mes"] <= ultimo_mes
    faltando = df[df["comparavel"] & df["valor"].isna()]
    if len(faltando):
        print(f"  aviso: {len(faltando)} combinações UF x mês x indicador sem registro no período comparável:")
        print(faltando.groupby(["indicador", "ano"]).size().to_string())

    df["data"] = df["data_referencia"].dt.strftime("%Y-%m-%d")
    colunas = ["data", "ano", "mes", "uf", "uf_nome", "regiao", "uf_iso", "cod_uf",
               "indicador", "categoria", "unidade", "valor", "populacao", "comparavel"]
    df = df[colunas].sort_values(["indicador", "uf", "data"]).reset_index(drop=True)
    df.to_parquet(PASTA_DADOS / "sinesp_uf_mensal.parquet", index=False)
    df.to_csv(PASTA_DADOS / "sinesp_uf_mensal.csv", index=False)

    print("5/5 conferência")
    ref = conferir(df, bruto, anos)
    ref.round(2).to_csv(PASTA_DADOS / "conferencia.csv", index=False)
    meses = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    resumo = {
        "periodo": f"jan–{meses[ultimo_mes - 1]}",
        "ultimo_mes": ultimo_mes,
        "anos": anos,
        "kpis": KPIS,
        "indicador_padrao": INDICADOR_PADRAO,
        "linhas": ref.round(2).to_dict(orient="records"),
    }
    (PASTA_DADOS / "conferencia.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n{len(df):,} linhas em dados/sinesp_uf_mensal.csv  (período comparável: {resumo['periodo']})\n")
    br = ref[ref["escopo"] == "Brasil"].set_index("indicador")
    print(br.loc[KPIS, [f"valor_{anos[0]}", f"valor_{anos[-1]}", "variacao_pct", f"taxa_100k_{anos[-1]}"]].round(2).to_string())


if __name__ == "__main__":
    main()
