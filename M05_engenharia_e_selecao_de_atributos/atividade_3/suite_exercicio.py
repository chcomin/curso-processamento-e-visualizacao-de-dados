"""Suite do exercicio guiado do M05: engenharia e selecao de atributos no Olist.

O exercicio pergunta: **no momento da compra, o pedido vai chegar em ate 10 dias?**
Este arquivo reune o encanamento que o exercicio nao pede para escrever: baixar
os dados, montar a base, os blocos que cruzam as nove tabelas, o split por data,
os metodos de selecao e o modelo que mede tudo com a mesma regua.

O que fica por conta de quem faz o exercicio: definir o alvo, propor e construir
atributos, listar as candidatas, escolher os metodos de selecao e ler o resultado.

Leia as docstrings. Cada funcao diz o que recebe, o que devolve e o que ela
esconde de proposito.

Convencoes:

* toda funcao de bloco devolve um DataFrame **indexado por order_id**, para que
  ``base.join(bloco)`` funcione sem argumento;
* datas ja vem como ``datetime64``; o modelo nao aceita data, entao data vira
  numero (dias entre datas, hora, dia da semana) antes de entrar como atributo;
* o momento da decisao e a compra. O que nasce depois dela
  (``COLUNAS_DO_FUTURO``) nao pode virar atributo, e ``checar_atributos`` barra.

Testado com pandas 2.2 e 3.0, scikit-learn 1.5 a 1.9.
"""

import shutil
import sys
import tempfile
import time
import urllib.request
import zipfile
from collections import namedtuple
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectFromModel, SequentialFeatureSelector, f_classif
from sklearn.inspection import permutation_importance
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

# --------------------------------------------------------------------------
# 1. Dados: download, unzip e leitura (bronze)
# --------------------------------------------------------------------------

URL_KAGGLE = "https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce"
CAMINHO_PADRAO = Path("dados_olist")

TABELAS = {
    "pedidos": "olist_orders_dataset.csv",
    "itens": "olist_order_items_dataset.csv",
    "pagamentos": "olist_order_payments_dataset.csv",
    "avaliacoes": "olist_order_reviews_dataset.csv",
    "clientes": "olist_customers_dataset.csv",
    "vendedores": "olist_sellers_dataset.csv",
    "produtos": "olist_products_dataset.csv",
    "geolocalizacao": "olist_geolocation_dataset.csv",
    "traducao": "product_category_name_translation.csv",
}

COLUNAS_DE_DATA = {
    "pedidos": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "itens": ["shipping_limit_date"],
    "avaliacoes": ["review_creation_date", "review_answer_timestamp"],
}

# Com User-Agent de navegador o Kaggle devolve a pagina HTML em vez do zip.
_CABECALHOS = {"User-Agent": "curl/8.4.0"}


def _mostrar_progresso(lidos, total):
    if total:
        texto = f"  baixando: {lidos / 1e6:6.1f} de {total / 1e6:.1f} MB ({100 * lidos / total:3.0f}%)"
    else:
        texto = f"  baixando: {lidos / 1e6:6.1f} MB"
    sys.stdout.write("\r" + texto)
    sys.stdout.flush()


def baixar_dados(destino=CAMINHO_PADRAO, forcar=False):
    """Baixa o zip do Olist no Kaggle e extrai os 9 CSV em ``destino``.

    Nao precisa de conta nem de token: usa o endpoint publico de download, que
    responde com um zip de cerca de 45 MB. Se os 9 CSV ja estiverem na pasta,
    nao baixa de novo (a menos que ``forcar=True``). Devolve o caminho da pasta.
    """
    destino = Path(destino)
    faltando = [arquivo for arquivo in TABELAS.values() if not (destino / arquivo).exists()]
    if not faltando and not forcar:
        print(f"os {len(TABELAS)} CSV ja estao em {destino}/")
        return destino

    destino.mkdir(parents=True, exist_ok=True)
    print(f"baixando de {URL_KAGGLE}")
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temporario:
        caminho_zip = Path(temporario.name)
    try:
        pedido = urllib.request.Request(URL_KAGGLE, headers=_CABECALHOS)
        with urllib.request.urlopen(pedido) as resposta, open(caminho_zip, "wb") as saida:
            tipo = resposta.headers.get("Content-Type", "")
            if "zip" not in tipo and "octet-stream" not in tipo:
                raise RuntimeError(f"o Kaggle respondeu {tipo!r} em vez de um zip; a URL pode ter mudado")
            total = int(resposta.headers.get("Content-Length") or 0)
            lidos = 0
            while True:
                bloco = resposta.read(1 << 20)
                if not bloco:
                    break
                saida.write(bloco)
                lidos += len(bloco)
                _mostrar_progresso(lidos, total)
        sys.stdout.write("\n")
        extrair_zip(caminho_zip, destino)
    finally:
        caminho_zip.unlink(missing_ok=True)
    return destino


def extrair_zip(caminho_zip, destino=CAMINHO_PADRAO):
    """Extrai os CSV de um zip do Olist em ``destino``, ignorando subpastas.

    E o plano B de ``baixar_dados``: se o download automatico falhar, baixe o
    zip pelo navegador na pagina do Kaggle, envie para a sessao e chame esta
    funcao com o caminho dele.
    """
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    extraidos = 0
    with zipfile.ZipFile(caminho_zip) as zip_:
        for membro in zip_.infolist():
            if membro.is_dir() or not membro.filename.lower().endswith(".csv"):
                continue
            with zip_.open(membro) as origem, open(destino / Path(membro.filename).name, "wb") as saida:
                shutil.copyfileobj(origem, saida)
            extraidos += 1
    print(f"{extraidos} CSV extraidos em {destino}/")
    return destino


def carregar_bronze(destino=CAMINHO_PADRAO):
    """Le os 9 CSV como vieram da fonte, com as colunas de data ja convertidas.

    Baixa antes, se faltar algum. Devolve um dict com as chaves de ``TABELAS``
    (pedidos, itens, pagamentos, avaliacoes, clientes, vendedores, produtos,
    geolocalizacao, traducao). Nenhuma regra de negocio e aplicada aqui: isto e
    a camada bronze.
    """
    destino = baixar_dados(destino)
    bronze = {}
    for nome, arquivo in TABELAS.items():
        codificacao = "utf-8-sig" if nome == "traducao" else "utf-8"
        bronze[nome] = pd.read_csv(destino / arquivo, encoding=codificacao)
        for coluna in COLUNAS_DE_DATA.get(nome, []):
            bronze[nome][coluna] = pd.to_datetime(bronze[nome][coluna])
    return bronze


# --------------------------------------------------------------------------
# 2. Base e regra de vazamento
# --------------------------------------------------------------------------

# A decisao e tomada no momento da compra. Tudo que so passa a existir depois
# disso descreve o desfecho, nao a situacao em que se decide.
MOMENTO_DA_DECISAO = "order_purchase_timestamp"

COLUNAS_DO_FUTURO = [
    "order_approved_at",
    "shipping_limit_date",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "review_score",
    "review_creation_date",
    "review_answer_timestamp",
    "review_comment_title",
    "review_comment_message",
]


def montar_base(bronze):
    """Uma linha por pedido entregue, com o cliente ja anexado; sem atributo ainda.

    Fica de fora quem nao foi entregue ou nao tem data de entrega: sem ela nao
    ha como saber se a entrega foi rapida. O join com ``clientes`` e 1:1 pela
    chave ``customer_id`` (cada pedido tem o seu). Devolve um DataFrame
    indexado por ``order_id`` com as colunas de ``pedidos`` mais
    ``customer_unique_id``, ``customer_zip_code_prefix``, ``customer_city`` e
    ``customer_state``.

    O alvo nao esta aqui: defini-lo faz parte do exercicio.
    """
    pedidos = bronze["pedidos"]
    entregues = pedidos[
        (pedidos["order_status"] == "delivered") & pedidos["order_delivered_customer_date"].notna()
    ]
    clientes = bronze["clientes"].drop_duplicates("customer_id").set_index("customer_id")
    base = entregues.join(clientes, on="customer_id")
    return base.set_index("order_id")


def checar_atributos(base, colunas, alvo=None):
    """Barra o que nao pode entrar no modelo; devolve a lista se estiver tudo certo.

    Levanta ``ValueError`` quando uma coluna (a) nao existe na base, (b) esta em
    ``COLUNAS_DO_FUTURO``, (c) e o proprio alvo, (d) ainda e data ou texto. Data
    e texto precisam virar numero antes: dias entre datas, dummies, taxa.

    A barreira e **por nome**: uma coluna calculada a partir de uma coluna do
    futuro (o tempo ate a postagem, por exemplo) passa sem aviso. Quem constroi
    uma coluna nova precisa saber de quais colunas brutas ela vem.
    """
    colunas = list(colunas)
    faltando = [c for c in colunas if c not in base.columns]
    if faltando:
        raise ValueError(f"colunas que nao estao na base: {faltando}")
    do_futuro = [c for c in colunas if c in COLUNAS_DO_FUTURO]
    if do_futuro:
        raise ValueError(f"colunas que so existem depois da decisao (vazamento): {do_futuro}")
    if alvo is not None and alvo in colunas:
        raise ValueError(f"o alvo {alvo!r} nao pode ser atributo dele mesmo")
    nao_numericas = [c for c in colunas if not pd.api.types.is_numeric_dtype(base[c])]
    if nao_numericas:
        raise ValueError(f"colunas de data ou texto, que precisam virar numero antes: {nao_numericas}")
    return colunas


def conferir_alvo(base, alvo, taxa_esperada=None):
    """Confere que o alvo existe e e 0/1; imprime e devolve a taxa de positivos.

    Com ``taxa_esperada``, avisa se a taxa medida se afastar mais de um ponto
    percentual dela. Em geral e sinal de que a convencao do alvo nao foi
    seguida: dias completos (``.dt.days`` trunca as horas) e ``<= 10``.
    """
    if alvo not in base.columns:
        raise ValueError(f"a coluna {alvo!r} ainda nao existe na base")
    serie = base[alvo]
    if not (pd.api.types.is_numeric_dtype(serie) or pd.api.types.is_bool_dtype(serie)):
        raise ValueError(f"{alvo!r} nao e numerica (tipo {serie.dtype}): a lacuna foi preenchida?")
    if not serie.isin([0, 1]).all():
        raise ValueError(f"{alvo!r} precisa ter so 0 e 1; use .astype(int) no resultado da comparacao")
    taxa = float(serie.mean())
    print(f"{alvo}: {100 * taxa:.1f}% de positivos em {len(serie):,} pedidos")
    if taxa_esperada is not None and abs(taxa - taxa_esperada) > 0.01:
        print(f"AVISO: esperava {100 * taxa_esperada:.1f}%. Confira a convencao: "
              "dias completos com .dt.days e comparacao com <= 10.")
    return taxa


# --------------------------------------------------------------------------
# 3. Blocos: cada um cruza uma tabela e devolve uma linha por pedido
# --------------------------------------------------------------------------


def agregar_itens_por_pedido(itens):
    """Colapsa a tabela de itens (uma linha por item) em uma linha por pedido.

    Devolve, por ``order_id``: ``n_itens``, ``n_produtos``, ``n_vendedores``,
    ``valor_total``, ``frete_total`` e ``preco_maximo``. Sem esse colapso, o
    join com a base multiplicaria cada pedido pelo numero de itens dele.
    """
    return itens.groupby("order_id").agg(
        n_itens=("order_item_id", "size"),
        n_produtos=("product_id", "nunique"),
        n_vendedores=("seller_id", "nunique"),
        valor_total=("price", "sum"),
        frete_total=("freight_value", "sum"),
        preco_maximo=("price", "max"),
    )


def item_principal_do_pedido(itens):
    """O item mais caro de cada pedido: ``product_id``, ``seller_id`` e ``price``.

    Quando o pedido tem varios itens, e preciso escolher um para falar em "o
    produto" e "o lojista" do pedido. A escolha aqui e o de maior preco; em
    empate (7.604 pedidos), o de menor ``order_item_id``, para que a escolha
    seja a mesma em toda execucao.
    """
    return (
        itens.sort_values(["price", "order_item_id"], ascending=[False, True], kind="stable")
        .drop_duplicates("order_id")
        .set_index("order_id")[["product_id", "seller_id", "price"]]
    )


def atributos_do_produto(itens, produtos, traducao):
    """Dimensoes e categoria do produto principal de cada pedido.

    Devolve, por ``order_id``: ``peso_g``, ``comprimento_cm``, ``altura_cm``,
    ``largura_cm``, ``n_fotos``, ``tamanho_descricao`` e ``categoria`` (em
    ingles quando ha traducao; ``desconhecida`` para os 610 produtos sem
    categoria). O volume nao vem pronto de proposito.
    """
    de_para = dict(zip(traducao["product_category_name"], traducao["product_category_name_english"]))
    principal = item_principal_do_pedido(itens)
    colunas = {
        "product_weight_g": "peso_g",
        "product_length_cm": "comprimento_cm",
        "product_height_cm": "altura_cm",
        "product_width_cm": "largura_cm",
        "product_photos_qty": "n_fotos",
        # A fonte escreve "lenght" mesmo.
        "product_description_lenght": "tamanho_descricao",
        "product_category_name": "categoria",
    }
    produto = produtos.set_index("product_id")[list(colunas)].rename(columns=colunas)
    resultado = principal[["product_id"]].join(produto, on="product_id").drop(columns="product_id")
    resultado["categoria"] = (
        resultado["categoria"].map(lambda nome: de_para.get(nome, nome)).fillna("desconhecida")
    )
    return resultado


def atributos_do_vendedor(itens, vendedores):
    """O lojista principal de cada pedido e onde ele esta.

    Devolve, por ``order_id``: ``seller_id``, ``seller_zip_code_prefix``,
    ``seller_city`` e ``seller_state``.
    """
    principal = item_principal_do_pedido(itens)[["seller_id"]]
    return principal.join(vendedores.set_index("seller_id"), on="seller_id")


def resumo_pagamentos(pagamentos):
    """Uma linha por pedido a partir da tabela de pagamentos.

    Devolve ``n_pagamentos``, ``n_parcelas`` (o maximo entre os pagamentos),
    ``valor_pago`` e ``tipo_pagamento`` (o do pagamento de maior valor). Cerca
    de 3% dos pedidos tem mais de um pagamento, por isso a agregacao.
    """
    principal = (
        pagamentos.sort_values("payment_value", ascending=False)
        .drop_duplicates("order_id")
        .set_index("order_id")["payment_type"]
        .rename("tipo_pagamento")
    )
    resumo = pagamentos.groupby("order_id").agg(
        n_pagamentos=("payment_sequential", "size"),
        n_parcelas=("payment_installments", "max"),
        valor_pago=("payment_value", "sum"),
    )
    return resumo.join(principal)


def _haversine_km(lat1, lon1, lat2, lon2):
    raio = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * raio * np.arcsin(np.sqrt(a))


def distancia_cliente_vendedor(base, geolocalizacao):
    """Distancia em linha reta, em km, entre o CEP do cliente e o do lojista.

    A base precisa ja ter ``customer_zip_code_prefix`` (vem de ``montar_base``)
    e ``seller_zip_code_prefix`` (vem de ``atributos_do_vendedor``). A tabela de
    geolocalizacao tem um milhao de linhas, varias por prefixo de CEP: ela e
    colapsada para uma coordenada mediana por prefixo antes de qualquer
    cruzamento. Devolve uma Series ``distancia_km`` alinhada ao indice da base
    (NaN para CEP sem coordenada).
    """
    for coluna in ["customer_zip_code_prefix", "seller_zip_code_prefix"]:
        if coluna not in base.columns:
            raise ValueError(f"a base ainda nao tem {coluna!r}; junte o bloco que a traz antes")
    coordenadas = geolocalizacao.groupby("geolocation_zip_code_prefix")[
        ["geolocation_lat", "geolocation_lng"]
    ].median()
    cliente = coordenadas.reindex(base["customer_zip_code_prefix"]).to_numpy()
    vendedor = coordenadas.reindex(base["seller_zip_code_prefix"]).to_numpy()
    distancia = _haversine_km(cliente[:, 0], cliente[:, 1], vendedor[:, 0], vendedor[:, 1])
    return pd.Series(distancia, index=base.index, name="distancia_km")


REGIAO_POR_ESTADO = {
    "AC": "norte", "AM": "norte", "AP": "norte", "PA": "norte", "RO": "norte", "RR": "norte", "TO": "norte",
    "AL": "nordeste", "BA": "nordeste", "CE": "nordeste", "MA": "nordeste", "PB": "nordeste",
    "PE": "nordeste", "PI": "nordeste", "RN": "nordeste", "SE": "nordeste",
    "DF": "centro_oeste", "GO": "centro_oeste", "MS": "centro_oeste", "MT": "centro_oeste",
    "ES": "sudeste", "MG": "sudeste", "RJ": "sudeste", "SP": "sudeste",
    "PR": "sul", "RS": "sul", "SC": "sul",
}


def dummies(base, coluna, minimo=500, prefixo=None):
    """One-hot de uma coluna de texto, com as categorias raras agrupadas em ``outros``.

    Uma categoria so ganha coluna propria se aparece ao menos ``minimo`` vezes;
    as demais, e tambem os valores ausentes, caem em ``<prefixo>_outros``.
    Devolve um DataFrame de 0/1 alinhado ao indice da base, pronto para
    ``base.join``.
    """
    prefixo = prefixo or coluna
    contagem = base[coluna].value_counts()
    frequentes = set(contagem[contagem >= minimo].index)
    valores = base[coluna].where(base[coluna].isin(frequentes), "outros")
    return pd.get_dummies(valores, prefix=prefixo, dtype=int)


def taxa_por_faixa(base, coluna, alvo, cortes=None, rotulos=None):
    """Taxa do alvo (em %) e contagem por faixa da coluna: a evidencia de que um atributo separa.

    Sem ``cortes``, agrupa pelos valores da coluna; com ``cortes``, usa ``pd.cut``.
    E a mesma forma de evidencia da aula: a pergunta nao e se o modelo melhora,
    e se a coluna separa quem recebe rapido de quem nao recebe.
    """
    grupos = base[coluna] if cortes is None else pd.cut(base[coluna], cortes, labels=rotulos, include_lowest=True)
    resumo = base.groupby(grupos, observed=True).agg(n=(alvo, "size"), taxa=(alvo, "mean"))
    resumo["taxa"] = (100 * resumo["taxa"]).round(1)
    return resumo


# --------------------------------------------------------------------------
# 4. Split por data
# --------------------------------------------------------------------------

Dados = namedtuple("Dados", ["X_treino", "X_teste", "y_treino", "y_teste"])

CORTE = "2018-03-01"


def dividir_por_data(base, colunas, alvo, corte=CORTE, momento=MOMENTO_DA_DECISAO):
    """Treino antes do corte, teste a partir dele; NaN preenchido com a mediana do treino.

    Passa por ``checar_atributos`` antes de qualquer coisa. A mediana e
    calculada so no treino e aplicada aos dois lados, para que o teste nao
    influencie o numero que preenche o treino. Devolve ``Dados(X_treino,
    X_teste, y_treino, y_teste)`` com os indices da base preservados.
    """
    colunas = checar_atributos(base, colunas, alvo)
    treino = base[momento] < pd.Timestamp(corte)
    X = base[colunas].astype(float)
    y = base[alvo].astype(int)
    medianas = X[treino].median()
    return Dados(X[treino].fillna(medianas), X[~treino].fillna(medianas), y[treino], y[~treino])


def resumo_do_split(dados):
    """Linhas e taxa do alvo em cada lado, para conferir o split."""
    return pd.DataFrame(
        {
            "linhas": [len(dados.y_treino), len(dados.y_teste)],
            "positivos": [int(dados.y_treino.sum()), int(dados.y_teste.sum())],
            "taxa_%": [round(100 * dados.y_treino.mean(), 1), round(100 * dados.y_teste.mean(), 1)],
        },
        index=["treino", "teste"],
    )


# --------------------------------------------------------------------------
# 5. O modelo e a metrica: a mesma regua para todo mundo
# --------------------------------------------------------------------------


def modelo(n_estimators=200, n_jobs=-1):
    """A floresta de referencia. Todo conjunto de colunas e medido com ela.

    Os hiperparametros sao fixos de proposito: o exercicio compara conjuntos de
    colunas, nao modelos. Mudar o modelo muda a regua.
    """
    return RandomForestClassifier(
        n_estimators=n_estimators, min_samples_leaf=20, n_jobs=n_jobs, random_state=0
    )


def acuracia_da_maioria(dados):
    """A acuracia de quem responde sempre a classe mais comum do teste: a referencia minima."""
    taxa = dados.y_teste.mean()
    return round(float(max(taxa, 1 - taxa)), 3)


def avaliar(colunas, dados):
    """Ajusta o modelo de referencia nas colunas dadas e mede a acuracia no teste.

    A metrica oficial do exercicio e a acuracia com limiar 0,5: a fracao de
    pedidos do teste em que o modelo acertou se a entrega seria rapida ou nao.
    Compare sempre com ``acuracia_da_maioria``. Devolve um dict com
    ``n_colunas`` e ``acuracia``.

    Uma acuracia acima de 0,95 neste problema e sinal de vazamento, nao de
    merito, e a funcao avisa. O aviso pega so o vazamento flagrante: uma
    coluna que carrega parte do desfecho (o tempo ate a postagem, por exemplo)
    sobe a acuracia sem chegar a 0,95.
    """
    colunas = list(colunas)
    floresta = modelo().fit(dados.X_treino[colunas], dados.y_treino)
    previsao = floresta.predict(dados.X_teste[colunas])
    acuracia = accuracy_score(dados.y_teste, previsao)
    if acuracia > 0.95:
        print(f"AVISO: acuracia de {acuracia:.3f} com {len(colunas)} colunas. Alguma delas conhece o desfecho?")
    return {"n_colunas": len(colunas), "acuracia": round(float(acuracia), 3)}


def comparar(conjuntos, dados):
    """Mede varios conjuntos de colunas com a mesma regua e devolve uma tabela.

    ``conjuntos`` e um dict ``{nome: lista de colunas}``. Cada linha da tabela
    e um conjunto, com ``n_colunas``, ``acuracia`` e o tempo de ajuste. A
    primeira linha impressa e a referencia da maioria.
    """
    print(f"{'maioria (sem modelo)':<30}      acuracia {acuracia_da_maioria(dados):.3f}")
    linhas = {}
    for nome, colunas in conjuntos.items():
        inicio = time.time()
        medida = avaliar(colunas, dados)
        medida["segundos"] = round(time.time() - inicio, 1)
        linhas[nome] = medida
        print(f"{nome:<30} {medida['n_colunas']:>3} colunas  acuracia {medida['acuracia']:.3f}")
    return pd.DataFrame.from_dict(linhas, orient="index")


def grafico_comparacao(tabela, dados=None, ax=None):
    """Barras horizontais de acuracia por conjunto; com ``dados``, marca a linha da maioria."""
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(7, 0.5 * len(tabela) + 1))
    ordem = tabela.sort_values("acuracia")
    rotulos = [f"{nome} ({int(n)} col.)" for nome, n in zip(ordem.index, ordem["n_colunas"])]
    ax.barh(rotulos, ordem["acuracia"], color="#4C72B0")
    for i, valor in enumerate(ordem["acuracia"]):
        ax.text(valor + 0.002, i, f"{valor:.3f}", va="center", fontsize=9)
    esquerda = ordem["acuracia"].min() - 0.05
    if dados is not None:
        maioria = acuracia_da_maioria(dados)
        ax.axvline(maioria, color="gray", linestyle="--")
        ax.text(maioria, len(ordem) - 0.4, f" maioria {maioria:.3f}", color="gray", fontsize=9)
        esquerda = min(esquerda, maioria - 0.02)
    ax.set_xlim(esquerda, ordem["acuracia"].max() + 0.04)
    ax.set_xlabel(f"acuracia no teste (compras a partir de {CORTE})")
    ax.spines[["top", "right"]].set_visible(False)
    return ax


# --------------------------------------------------------------------------
# 6. Selecao de atributos: filtros, wrapper, embedded
# --------------------------------------------------------------------------


def podar_por_correlacao(X, limite=0.85, relevancia=None):
    """Filtro: de cada par com |correlacao| acima do limite, uma coluna sai.

    Sem ``relevancia``, sai a coluna que vem depois na ordem; com ``relevancia``
    (Series indexada por coluna, maior e melhor), sai a menos relevante do par.
    Devolve ``(mantidas, pares)``: a lista do que ficou e um DataFrame com cada
    par podado. Nao usa o alvo.
    """
    correlacao = X.corr().abs()
    colunas = list(correlacao.columns)
    removidas, pares = [], []
    for i in range(len(colunas)):
        for j in range(i):
            valor = correlacao.iloc[i, j]
            if not valor > limite:
                continue
            depois, antes = colunas[i], colunas[j]
            if depois in removidas or antes in removidas:
                continue
            if relevancia is None or relevancia[depois] <= relevancia[antes]:
                sai, fica = depois, antes
            else:
                sai, fica = antes, depois
            removidas.append(sai)
            pares.append({"mantida": fica, "removida": sai, "correlacao": round(float(valor), 3)})
    pares = pd.DataFrame(pares, columns=["mantida", "removida", "correlacao"])
    mantidas = [c for c in colunas if c not in removidas]
    return mantidas, pares.sort_values("correlacao", ascending=False).reset_index(drop=True)


def ranking_f_classif(X, y):
    """Filtro: a estatistica F de cada coluna contra o alvo, da maior para a menor.

    Univariado: olha uma coluna de cada vez, sem ver redundancia nem interacao.
    Devolve uma Series indexada por coluna.
    """
    F, _ = f_classif(X, y)
    return pd.Series(F, index=X.columns).sort_values(ascending=False)


def selecionar_por_f_classif(X, y, k=10):
    """As ``k`` colunas de maior F. Devolve a lista, na ordem do ranking."""
    return list(ranking_f_classif(X, y).head(k).index)


def selecionar_sequencial(X, y, k=8, amostra=8000, cv=3, n_estimators=30, random_state=0):
    """Wrapper: forward selection, uma coluna por vez, guiada pela acuracia em validacao cruzada.

    Comeca do vazio; a cada passo testa cada candidata que falta e fica com a
    que mais sobe a acuracia media nas ``cv`` dobras, ate ter ``k`` colunas.
    Sao dezenas de ajustes por passo, entao roda sobre uma amostra de
    ``amostra`` linhas do treino e com uma floresta menor (``n_estimators``).
    Devolve a lista escolhida. Nao imprime nada ate terminar; leva de segundos
    (maquina com varios nucleos) a poucos minutos (Colab). O resultado depende
    da amostra: trocar ``random_state`` mostra quanto.
    """
    if amostra and len(X) > amostra:
        X = X.sample(amostra, random_state=random_state)
        y = y.loc[X.index]
    seletor = SequentialFeatureSelector(
        modelo(n_estimators=n_estimators, n_jobs=1),
        n_features_to_select=k, direction="forward", scoring="accuracy", cv=cv, n_jobs=-1,
    )
    inicio = time.time()
    seletor.fit(X, y)
    print(f"SequentialFeatureSelector: {k} colunas em {time.time() - inicio:.0f} s")
    return list(X.columns[seletor.get_support()])


def ranking_impureza(X, y):
    """Embedded: ``feature_importances_`` da floresta, da maior para a menor.

    Sai de graca do ajuste. Mede quanto cada coluna reduziu a impureza nas
    arvores, o que infla colunas continuas com muitos valores distintos.
    Devolve uma Series indexada por coluna.
    """
    floresta = modelo().fit(X, y)
    return pd.Series(floresta.feature_importances_, index=X.columns).sort_values(ascending=False)


def selecionar_por_importancia(X, y, k=10):
    """As ``k`` colunas de maior ``feature_importances_``. Devolve a lista."""
    return list(ranking_impureza(X, y).head(k).index)


def ranking_permutacao(X, y, n_repeats=5, random_state=0):
    """Embedded: quanto a acuracia cai quando cada coluna e embaralhada.

    Separa 30% do treino como validacao (sorteio estratificado, e nao um corte
    por data como na aula; e mais simples e o teste continua intocado), ajusta
    a floresta nos outros 70% e mede a queda na validacao. Custa uma predicao
    por coluna e por repeticao. Devolve uma Series indexada por coluna, da
    maior queda para a menor; valor perto de zero ou negativo significa que o
    modelo nao usa a coluna.
    """
    X_ajuste, X_val, y_ajuste, y_val = train_test_split(
        X, y, test_size=0.3, random_state=random_state, stratify=y
    )
    floresta = modelo().fit(X_ajuste, y_ajuste)
    resultado = permutation_importance(
        floresta, X_val, y_val, scoring="accuracy",
        n_repeats=n_repeats, random_state=random_state, n_jobs=-1,
    )
    return pd.Series(resultado.importances_mean, index=X.columns).sort_values(ascending=False)


def selecionar_por_modelo(X, y, limiar="median"):
    """Transformador baseado em modelo: ``SelectFromModel`` sobre a floresta.

    Ajusta a floresta uma vez e fica com as colunas cuja importancia passa de
    ``limiar`` (``"median"``, ``"mean"``, ``"1.5*mean"`` ou um numero). E o
    metodo que entra num ``Pipeline`` de producao sem custo extra. Devolve a
    lista escolhida.
    """
    seletor = SelectFromModel(modelo(), threshold=limiar).fit(X, y)
    return list(X.columns[seletor.get_support()])


def matriz_de_escolhas(conjuntos, todas):
    """Tabela colunas x metodos com 1 onde o metodo escolheu a coluna, e o total."""
    tabela = pd.DataFrame(
        {nome: [int(c in colunas) for c in todas] for nome, colunas in conjuntos.items()},
        index=todas,
    )
    tabela["total"] = tabela.sum(axis=1)
    return tabela.sort_values("total", ascending=False)
