# Amostras de texto do laboratório do M08

Quatro conjuntos de 3.000 textos com os vetores já calculados. Gerados por `scripts/preparar_corpora.py`.

Em todos: amostra simples com `random_state=42` sobre o que sobrou da limpeza (HTML e entidades removidos, espaços
colapsados, vazios, duplicatas e textos curtos fora) e restrito às categorias mais frequentes. Modelo
`Qwen/Qwen3-Embedding-0.6B`, documentos **sem instrução**, vetores de norma 1 (cosseno = produto escalar), salvos em
`float16`. O CSV tem as colunas `titulo`, `texto`, `categoria`; a linha `i` do CSV é o vetor `i` de `<nome>_vetores.npy`
(forma 3000 x 1024).

```python
import numpy as np, pandas as pd
df = pd.read_csv("netflix.csv")
X = np.load("netflix_vetores.npy").astype("float32")   # (3000, 1024)
```

Para buscar com uma consulta, vetorize-a com o mesmo modelo e uma instrução (formato Qwen3: `Instruct: <instrução>\nQuery: <consulta>`).
Instruções usadas nos testes:

| Conjunto | Instrução |
|---|---|
| noticias | Given a search query, retrieve relevant news articles |
| netflix | Given a short description, retrieve movies and TV shows whose plot matches it |
| jogos | Given a short description, retrieve video games that match it |
| b2w | Given a retail product title, retrieve titles of similar products |

## b2w: produtos da Americanas (português)

- Fonte: https://github.com/americanas-tech/b2w-reviews01 (`B2W-Reviews01.csv`). Licença CC BY-NC-SA 4.0 (uso não comercial, com atribuição).
- Um registro por produto (`product_id` único; 47.191 após a limpeza, mínimo de 3 palavras no título).
- `titulo` = `texto` = `product_name`; `categoria` = `site_category_lv1`. As 8 mais frequentes.
- Categorias: Móveis 499, Utilidades Domésticas 424, Beleza e Perfumaria 413, Informática e Acessórios 379, Livros 349, Brinquedos 343, Automotivo 341, Casa e Construção 252.

## noticias: Folha de S.Paulo (português)

- Fonte: https://www.kaggle.com/datasets/marlesson/news-of-the-site-folhauol (`articles.csv`, 2015 a 2017). Licença CC0 no Kaggle (o conteúdo é da Folha; uso didático).
- Pool de 132.935 matérias.
- `titulo` = título; `texto` = título + ". " + primeira frase do corpo (sem a assinatura em caixa alta do início; corte em ~300 caracteres); `categoria` = seção da Folha.
- Fora as seções que não são assunto (`colunas`, `opiniao`, `paineldoleitor`, `sobretudo`, `asmais`); ficam as 7 maiores restantes.
- Categorias: poder (política) 571, mercado 541, esporte 510, mundo 451, ilustrada (cultura) 417, cotidiano 403, saopaulo 107.

## netflix: filmes e séries da Netflix (inglês)

- Fonte: https://www.kaggle.com/datasets/shivamb/netflix-shows (`netflix_titles.csv`). Licença CC0.
- Pool de 8.695 títulos.
- `titulo` = title; `texto` = title + ". " + description (o título entra no vetor: buscar pelo nome acha o item); `categoria` = **primeiro gênero de `listed_in` que diz algo**: pula "International Movies/TV Shows", "Independent Movies", "Movies"/"TV Shows" genéricos, "Classic/Cult/British/Spanish/Korean" e também "Dramas" (que só vale se não houver outro). Equivalentes de filme e série foram juntados (TV Comedies = Comedies, Crime TV Shows = Crime, Kids' TV e Children & Family Movies = Kids & Family, Docuseries = Documentaries, etc.). As 8 mais frequentes.
- Categorias: Comedies 621, Documentaries 533, Dramas 454, Kids & Family 410, Action & Adventure 368, Romance 254, Crime 190, Thrillers 170.

## jogos: Steam (inglês)

- Fonte: https://www.kaggle.com/datasets/nikdavis/steam-store-games (`steam.csv` + `steam_description_data.csv`, Nik Davis, 2019). Licença CC BY 4.0 (atribuição).
- Só jogos em inglês; pool de 25.242.
- `titulo` = name; `texto` = name + ". " + `short_description` sem HTML (o título entra no vetor); `categoria` = **o gênero mais raro do jogo**, depois de tirar os rótulos que não são de jogabilidade (Indie, Early Access, Free to Play, Violent, Gore, Nudity, Sexual Content e softwares utilitários). Assim "Action" e "Adventure", que estão em quase tudo, só ficam com os jogos que não têm outro gênero. As 8 mais frequentes.
- Categorias: Adventure 698, RPG 464, Casual 453, Simulation 434, Action 432, Strategy 303, Racing 110, Sports 106.
