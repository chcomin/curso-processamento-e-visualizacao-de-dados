# Painel "Segurança pública no Brasil": especificação comum

O mesmo painel de uma página é feito em quatro ferramentas: Quarto Dashboard, Dash,
Streamlit e Apps Script. Esta especificação define **o quê**. O **como se parece** está
em `app_script/dashboard-apps-script/references/ui-spec.md`, que é o estilo SnowUI e
tem prévia em `referencia_visual.png`. Siga os dois à risca. Quando a ferramenta não
permitir algo, chegue o mais perto possível e registre o desvio num comentário no topo
do arquivo.

## Dados

Os caminhos são relativos à pasta `M09_dashboards/`, que no repositório público é a
raiz.

| Arquivo | Conteúdo |
|---|---|
| `dados/sinesp_uf_mensal.csv` | 14.742 linhas. Colunas: `data` (AAAA-MM-01), `ano`, `mes`, `uf`, `uf_nome`, `regiao`, `uf_iso` (BR-SP), `cod_uf`, `indicador`, `categoria`, `unidade`, `valor` (inteiro; vazio = sem registro), `populacao` (IBGE, da UF naquele ano), `comparavel` (True se mês ≤ 9) |
| `dados/br_uf.geojson` | 27 UFs, propriedades `uf` (sigla) e `nome` |
| `dados/conferencia.json` | Números de referência que o painel precisa reproduzir |

Num app em `paineis/<ferramenta>/app.py`, leia os dados com
`Path(__file__).resolve().parents[2] / "dados"`.

## Regras de cálculo (as mesmas em todas as ferramentas)

- **Período comparável**: só as linhas com `comparavel == True`, isto é, jan–set de 2025
  e de 2026. A exceção é a linha de tendência (P4), que mostra 2025 inteiro.
- **Total** de um indicador num ano: soma de `valor` no período comparável. Linhas vazias
  são ignoradas, nunca tratadas como zero.
- **Taxa por 100 mil hab.** (UF, ano): `soma(valor) / populacao × 100000`, onde a
  população é a da UF naquele ano. No Brasil: `soma(valor das 27 UFs) / soma(populacao
  das 27 UFs, uma vez por UF) × 100000`. **Nunca tire média de taxas.** A taxa não é
  anualizada, e o subtítulo diz "jan–set".
- **Δ%** = `(total_2026 / total_2025 − 1) × 100`, com 1 casa decimal.
- **Polaridade** (que cor tem o Δ): "menor é melhor" para todos os indicadores, exceto
  `Tráfico de drogas` e `Armas de fogo apreendidas`, que são **neutros**. Neles, o Δ
  usa `--ink-80` e o segmento do dumbbell usa `--ink-40`, porque mais apreensões podem
  significar mais polícia, não mais crime.
- Os números saem formatados em pt-BR: `20.728`, `−12,9%`, `9,68`.

## Seletor de indicador (barra lateral)

São 15 indicadores em 5 grupos, nesta ordem. O padrão é **Homicídio doloso**.

- **Crimes contra a vida**: Homicídio doloso · Latrocínio · Lesão corporal seguida de morte · Morte por intervenção de agente do Estado · Tentativa de homicídio
- **Violência contra a mulher e sexual**: Feminicídio · Tentativa de feminicídio · Estupro · Estupro de vulnerável
- **Patrimônio**: Roubo de veículo · Furto de veículo · Roubo de carga
- **Drogas e armas**: Tráfico de drogas · Armas de fogo apreendidas
- **Trânsito**: Mortes no trânsito

Os nomes são exatamente os valores da coluna `indicador`.

## Filtro temporal (todos os painéis)

- **Controle**: intervalo de meses, "De [mês] até [mês]", com opções de **jan a set**. O
  limite é setembro porque é o último mês de 2026. Padrão: jan–set. Pode ser feito com
  dois *selects* ou um *range slider*.
- Fica no **topo**, ao lado do chip de período, ou na barra lateral acima do menu de
  indicadores. Em 390 px, entra no topo da coluna.
- O intervalo vale para **os dois anos** (mesmos meses em 2025 e 2026) e altera:
  - **KPIs** (totais, Δ% e linha "vs ... em {intervalo} 2025"): o filtro temporal mexe
    nos KPIs; o seletor de indicador, não;
  - **mapa e ranking** (taxa de 2026 no intervalo);
  - **dumbbell** (taxas de 2025 → 2026 no intervalo);
  - **legenda da tendência** (totais do intervalo);
  - **chip e subtítulos**, que passam a mostrar o rótulo do intervalo ("jan–jun", "jul–set";
    um mês só: "mar").
- A **tendência** continua mostrando 2025 inteiro e 2026 até setembro, com o intervalo
  selecionado **sombreado** (faixa vertical `rgba(28,28,28,0.05)`).
- Se o mês inicial for maior que o final, troque os dois.

| Intervalo | Homicídio doloso | Latrocínio | Feminicídio | Estupro | Top 5 (taxa 2026) |
|---|---|---|---|---|---|
| jan–jun | 16.075 → 13.963 (−13,1%) | 416 → 322 (−22,6%) | 768 → 745 (−3,0%) | 10.180 → 10.292 (+1,1%) | PE 13,36 · RN 13,25 · AL 12,91 · MA 12,61 · AP 11,24 |
| jul–set | 7.733 → 6.765 (−12,5%) | 195 → 126 (−35,4%) | 365 → 338 (−7,4%) | 4.931 → 4.973 (+0,9%) | AL 6,89 · PE 6,71 · RN 6,67 · PB 5,74 · MA 5,71 |

## Identificação da ferramenta (todos os painéis)

- Cada painel mostra **de qual ferramenta ele é**. No canto superior esquerdo (topo da barra
  lateral, onde fica a marca), coloque o **ícone da ferramenta** (24 px, na cor da marca) e,
  ao lado, em duas linhas:
  - "Segurança pública no Brasil" (14 px/600);
  - "Painel em **<Ferramenta>**" (12 px, `--ink-40`).
- O título da aba do navegador é "Segurança pública no Brasil · <Ferramenta>".
- Ícones (Simple Icons, em `imagens/`; copie para a pasta do painel para ele ficar autocontido):

| Ferramenta | Arquivo | Cor da marca |
|---|---|---|
| Quarto | `logo_quarto.svg` | `#39729E` |
| Dash (Plotly) | `logo_plotly.svg` | `#3F4F75` |
| Streamlit | `logo_streamlit.svg` | `#FF4B4B` |
| Google Apps Script | `logo_googleappsscript.svg` | `#4285F4` |

  Os SVGs são monocromáticos (um `<path>`). Pinte com `fill` na cor da marca, inline ou em CSS.

## Paleta de cada painel

A estrutura (SnowUI) é a mesma, mas cada painel tem **o seu matiz**, para os alunos perceberem
que são ferramentas diferentes. Troque só estes tokens do ui-spec. `--good`/`--bad` (cores do Δ
e do segmento do dumbbell), o fundo branco, `--surface` e os níveis de `--ink` **não mudam**.

| Token | Apps Script (azul, base) | Quarto (verde-azulado) | Dash (violeta) | Streamlit (âmbar) |
|---|---|---|---|---|
| `--surface-blue` (KPI 1 e 3) | `#E3F5FF` | `#DDF3EF` | `#ECE9FF` | `#FFF1E3` |
| `--surface-lav` (KPI 2 e 4) | `#E5ECF6` | `#E6EFEC` | `#EEEDF7` | `#F8EEE6` |
| `--data-1` (2026, ponto atual) | `#1C1C1C` | `#0F3D38` | `#2B1F6B` | `#4A2412` |
| `--data-2` (2025, barrinhas) | `#A8C5DA` | `#93CFC5` | `#B9B0F0` | `#F2BE94` |
| `--seq-0…4` (mapa) | `#E3F5FF #B1E3FF #7FB8DA #4A7FA8 #1C3D5A` | `#DDF3EF #A6DDD3 #62BCAD #2A8C7E #0E4F47` | `#ECE9FF #C8C0FA #9A8CEF #6A56D4 #37278A` | `#FFF1E3 #FFD2A8 #FFA766 #E07834 #9C4415` |
| Destaque (item ativo, marcador) | `#1C1C1C` | `#2A8C7E` | `#6A56D4` | `#E07834` |

## Conteúdo da página

- **Topo**: o caminho "Painéis / Segurança pública" e o chip "jan–set · 2026 × 2025".
- **Título da página**: "Segurança pública no Brasil".

| Bloco | Título do cartão (pergunta) | Subtítulo | O que mostra |
|---|---|---|---|
| **P1: KPIs fixos**, não mudam com o seletor | (cada cartão tem o nome do indicador) | linha 3: "vs {total 2025} em jan–set 2025" | 4 cartões: **Homicídio doloso, Latrocínio, Feminicídio, Estupro**. Número: total de 2026. Δ% com seta e polaridade. |
| **P2: mapa + ranking** | "Onde o risco é maior?" | "{indicador} · taxa por 100 mil hab. · jan–set 2026" | Coroplético das 27 UFs, com a taxa de 2026 em 5 classes por quantis na escala `--seq`. À direita, as 5 UFs com maior taxa, com o nome, a taxa com **2 casas** (20,07) e uma barrinha. |
| **P3: dumbbell** | "Quais estados melhoraram ou pioraram?" | "{indicador} · taxa por 100 mil hab. · jan–set 2025 → 2026" | 27 linhas (rótulo = sigla da UF), ordenadas pela taxa de 2026 (maior em cima). Ponto de 2025 em `--data-2`, ponto de 2026 em `--data-1` e segmento na cor da polaridade. Tooltip: UF, as duas taxas e o Δ%. |
| **P4: tendência** | "A mudança é de um mês ou do ano todo?" | "{indicador} · total no Brasil por mês ({unidade})" | Linha de 2026 sólida (jan–set) e linha de 2025 tracejada (jan–dez). Legenda no cabeçalho: "● 2026 {total jan–set} · ○ 2025 {total jan–set}". |
| **Sobre os dados** (painel direito ou rodapé) | — | — | Os 5 itens abaixo. |

Os 5 itens de "Sobre os dados":

1. **Fonte**: SINESP VDE / Ministério da Justiça e Segurança Pública, bases de 2025 e 2026 (extraídas em 11/11/2026). População: estimativas do IBGE para 2025 e 2026.
2. **Período comparável**: jan–set. A base de 2026 vai até setembro.
3. **Dados preliminares**: os estados ainda podem revisar os números.
4. **Atenção a MS**: a série de homicídios muda de patamar entre 2025 e 2026. Compare com cautela.
5. **Como ler a taxa**: ocorrências (ou vítimas) no período ÷ população × 100 mil. Não é anualizada.

## Números que o painel precisa mostrar (de `dados/conferencia.json`)

| KPI | jan–set 2025 | jan–set 2026 | Δ% |
|---|---|---|---|
| Homicídio doloso | 23.808 | 20.728 | −12,9% |
| Latrocínio | 611 | 448 | −26,7% |
| Feminicídio | 1.133 | 1.083 | −4,4% |
| Estupro | 15.111 | 15.265 | +1,0% |

A taxa de homicídio doloso no Brasil em 2026 é 9,68 por 100 mil. As maiores taxas por UF
em 2026 são **PE 20,07, RN 19,92, AL 19,81, MA 18,32 e AP 16,17**, que formam o top 5 do
ranking do P2.

## Critérios de aceite

1. O painel roda a partir da própria pasta com o comando indicado no README do
   repositório, sem erro no console.
2. Os 4 KPIs e o top 5 batem exatamente com a tabela acima.
3. Trocar o indicador atualiza P2, P3 e P4 e não mexe nos KPIs.
4. Não aparece barra de ferramentas do Plotly, título padrão de biblioteca, legenda
   automática supérflua nem eixo com linha preta.
5. Em 390 px de largura, a página vira uma coluna só e nada fica cortado.
