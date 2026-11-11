# UI spec — painel de uma página

Especificação visual para qualquer agente reproduzir o mesmo painel em qualquer
ferramenta (Apps Script + ECharts, Plotly/Dash, Streamlit, Quarto, HTML puro).
A referência é o kit **SnowUI Dashboard Design System** (ByeWind, Figma Community).
A prévia está em `referencia_visual.png`.

O estilo é **claro, plano e calmo**: fundo branco, cartões em cinza quase branco,
**sem sombra e sem borda**, cantos bem arredondados, texto preto em níveis de
opacidade e cor só nos dados. Os cartões de KPI usam fundos pastel.

---

## 1. Tokens

Copie este bloco no CSS e use só as variáveis.

```css
:root {
  /* superfícies */
  --bg:            #FFFFFF;   /* página */
  --surface:       #F7F9FB;   /* cartão */
  --surface-blue:  #E3F5FF;   /* KPI 1 e 3 */
  --surface-lav:   #E5ECF6;   /* KPI 2 e 4 */
  --hover:         rgba(28, 28, 28, 0.05);
  --selected:      rgba(28, 28, 28, 0.05);
  --divider:       rgba(28, 28, 28, 0.10);

  /* texto (preto em níveis de opacidade) */
  --ink:           #1C1C1C;               /* títulos, números */
  --ink-80:        rgba(28, 28, 28, 0.80);
  --ink-40:        rgba(28, 28, 28, 0.40); /* rótulos, eixos, legendas */
  --ink-20:        rgba(28, 28, 28, 0.20); /* desabilitado, grade forte */
  --ink-10:        rgba(28, 28, 28, 0.10); /* linhas de grade */

  /* séries de dados (ordem de uso) */
  --data-1:        #1C1C1C;   /* série principal: período atual */
  --data-2:        #A8C5DA;   /* série de comparação: período anterior */
  --data-3:        #95A4FC;
  --data-4:        #BAEDBD;
  --data-5:        #B1E3FF;
  --data-6:        #A1E3CB;
  --data-7:        #FFB55B;

  /* escala sequencial (mapa, calor): do menor ao maior */
  --seq-0: #E3F5FF; --seq-1: #B1E3FF; --seq-2: #7FB8DA; --seq-3: #4A7FA8; --seq-4: #1C3D5A;

  /* semântica do Δ (texto passa AA sobre os fundos pastel) */
  --good:          #0F7B5F;   /* mudança desejável */
  --bad:           #C0362C;   /* mudança indesejável */
  --good-bg:       rgba(15, 123, 95, 0.10);
  --bad-bg:        rgba(192, 54, 44, 0.10);

  /* forma */
  --radius-card:   16px;
  --radius-control: 8px;
  --radius-pill:   999px;
  --gap:           28px;      /* entre cartões */
  --pad-card:      24px;
  --font: "Inter", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}

[data-theme="dark"] {
  --bg: #1C1C1C; --surface: rgba(255,255,255,0.05);
  --surface-blue: #E3F5FF; --surface-lav: #E5ECF6;   /* KPIs continuam claros, com texto escuro */
  --hover: rgba(255,255,255,0.08); --selected: rgba(255,255,255,0.10); --divider: rgba(255,255,255,0.10);
  --ink: #FFFFFF; --ink-80: rgba(255,255,255,0.80); --ink-40: rgba(255,255,255,0.40);
  --ink-20: rgba(255,255,255,0.20); --ink-10: rgba(255,255,255,0.10);
  --data-1: #C6C7F8;   /* o preto some no fundo escuro */
  --good: #4FD1A5; --bad: #FF7A6E;
}
```

Fonte: **Inter** do Google Fonts (`wght@400;600`). Use números tabulares
(`font-variant-numeric: tabular-nums`) em KPIs e tabelas.

| Papel | Tamanho / peso | Cor |
|---|---|---|
| Título da página | 14 px / 600 | `--ink` |
| Título do cartão | 14 px / 600 | `--ink` |
| Subtítulo do cartão (unidade, período) | 12 px / 400 | `--ink-40` |
| Número do KPI | 24 px / 600 | `--ink` (sempre escuro, porque o fundo é pastel) |
| Rótulo do KPI | 14 px / 400 | `--ink` |
| Δ do KPI | 12 px / 400 | `--good` ou `--bad` |
| Eixos, legendas, cabeçalho de tabela | 12 px / 400 | `--ink-40` |
| Corpo, linhas de tabela, itens do menu | 14 px / 400 | `--ink` |
| Nota de rodapé | 12 px / 400 | `--ink-40` |

---

## 2. Layout

```text
┌────────────┬──────────────────────────────────────────────────────┬─────────────┐
│ BARRA       │ TOPO: ☰  Painéis / <Título>      [período] [◐ tema] │ PAINEL       │
│ LATERAL     ├──────────────────────────────────────────────────────┤ DIREITO      │
│ 212 px      │ Título da página                                     │ 280 px       │
│             │ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │ "Sobre os    │
│ logo/nome   │ │ KPI 1  │ │ KPI 2  │ │ KPI 3  │ │ KPI 4  │          │  dados"      │
│             │ └────────┘ └────────┘ └────────┘ └────────┘          │ fonte,       │
│ GRUPO A     │ ┌──────────────────────────┐ ┌───────────────┐       │ período,     │
│  • item     │ │ Gráfico principal (P2)    │ │ Detalhe (P3)  │       │ avisos,      │
│  • item ◀   │ │ mapa + ranking            │ │ alto, ocupa   │       │ como ler     │
│ GRUPO B     │ └──────────────────────────┘ │ duas linhas   │       │              │
│  • item     │ ┌──────────────────────────┐ │               │       │              │
│             │ │ Tendência (P4)            │ │               │       │              │
│             │ └──────────────────────────┘ └───────────────┘       │              │
│             │ nota de fonte                                         │              │
└────────────┴──────────────────────────────────────────────────────┴─────────────┘
```

- **Barra lateral (212 px, fundo `--bg`, divisória à direita `--divider`)**: nome do
  painel no topo (14 px/600) e, abaixo, o **seletor principal como menu**. São grupos
  com rótulo 14 px `--ink-40` e itens 14 px `--ink` com altura de 28 px, raio de 8 px e
  padding de 8 px. O item ativo tem fundo `--selected` e uma barrinha de 4×16 px em
  `--ink` à esquerda. Um menu é mais rápido de ler que um dropdown quando há até
  cerca de 20 opções.
- **Topo (68 px, divisória embaixo)**: o caminho "Painéis / Título" (14 px; "Painéis"
  em `--ink-40`), um chip do período à direita (pill, fundo `--hover`, 12 px) e o botão
  de tema claro/escuro (ícone ◐).
- **Área principal (padding 28 px)**: a ordem de leitura é **KPI → onde → quem → quando**,
  de cima para baixo e da esquerda para a direita.
  - Grid de 12 colunas, com espaço de 28 px entre os cartões.
  - KPIs: 4 cartões de 3 colunas cada, com 112 px de altura.
  - Gráfico principal: 7 colunas, com 320 a 360 px de altura.
  - Detalhe: 5 colunas, ocupando duas linhas.
  - Tendência: 7 colunas, com 280 a 320 px de altura.
- **Painel direito (280 px, divisória à esquerda)**: "Sobre os dados", com itens no
  estilo das notificações do SnowUI. Cada item tem um ícone em círculo de 24 px com
  fundo `--surface-blue`, um texto de 14 px e um meta de 12 px em `--ink-40`. O conteúdo
  é a fonte, o período comparável, os avisos de qualidade e uma linha "como ler".

**Responsivo**

| Largura | O que muda |
|---|---|
| ≥ 1440 px | Os três painéis. |
| 1024–1439 px | O painel direito sai e "Sobre os dados" vai para o rodapé. |
| 768–1023 px | A barra lateral vira um `select` no topo. Os KPIs ficam 2×2 e os gráficos ocupam a largura toda. |
| < 768 px | Uma coluna só. Os KPIs ficam 2×2 e o mapa tem 280 px de altura. |

---

## 3. Componentes

### Cartão (base)
O cartão tem fundo `--surface`, raio `--radius-card`, padding `--pad-card`, sem sombra e
sem borda. O cabeçalho mostra o **título como pergunta** ("Onde o risco é maior?") e,
embaixo, um subtítulo com a métrica, a unidade e o período ("Taxa por 100 mil hab. ·
jan–set 2026"). Depois vêm 16 px de espaço e o gráfico.

### KPI
- Fundo alternado: o 1º e o 3º usam `--surface-blue`; o 2º e o 4º, `--surface-lav`.
  Raio de 16 px e padding de 24 px.
- Linha 1: o rótulo (14 px).
- Linha 2: o número (24 px/600) à esquerda e o Δ à direita, na mesma linha de base.
- O Δ é `+11,0% ↗` ou `−12,9% ↘`: sinal, valor com 1 casa decimal, vírgula decimal e uma
  seta. A cor vem da **polaridade**. Quando subir é ruim (crime, custo), a alta usa
  `--bad` e a queda usa `--good`; quando subir é bom, é o inverso. **A cor nunca é o
  único sinal**: o sinal e a seta também aparecem.
- Linha 3, opcional (12 px, `--ink-40`): "vs 23.808 em jan–set 2025".

### Seletor
Em telas largas, é o menu da barra lateral. Em telas estreitas, é um `select` com raio
de 8 px, fundo `--hover` e sem borda. O estado do seletor nunca muda os KPIs
fixos.

### Mapa coroplético + ranking (P2)
- O mapa ocupa cerca de 60% da largura do cartão. As áreas usam a escala `--seq-0…4` em
  5 classes por quantis, com contorno de 0,5 px em `--bg`.
- A legenda fica embaixo do mapa: 5 quadradinhos de 12 px e os limites em 12 px
  `--ink-40`.
- O ranking fica à direita: as 5 maiores, no padrão "Revenue by Location" do SnowUI. Cada
  linha tem o nome e o valor (12 px) e, embaixo, uma barra de 2 px com trilho `--ink-10`
  e preenchimento `--data-2`, proporcional ao maior valor.
- O tooltip mostra o nome da área, o valor do período atual, o do anterior e o Δ.

### Pareado / dumbbell (P3)
- Uma linha por categoria, com 18 a 20 px de altura cada, ordenadas pelo valor atual
  (maior em cima).
- O ponto do anterior é um círculo de 6 px em `--data-2`, e o do atual é um círculo de
  8 px em `--data-1`.
- O segmento que liga os dois tem 2 px, em `--good` quando a mudança é desejável e em
  `--bad` quando não é.
- O eixo x começa em 0, com grade vertical `--ink-10` e sem eixo y desenhado (só os
  rótulos, em 12 px).

### Tendência (P4)
- O **período atual** é uma linha sólida de 2 px em `--data-1`. O **período anterior** é
  tracejado (4-4), com 2 px, em `--data-2`.
- A legenda fica no cabeçalho do cartão, como no SnowUI: "● 2026 **20.728** · ○ 2025
  **23.808**".
- Também há rótulo direto no último ponto de cada série.
- Os pontos aparecem só no hover. Sem área preenchida. O eixo y começa em 0, com grade
  horizontal `--ink-10`.
- Os meses ficam abreviados no eixo x (jan, fev…). Um período ainda incompleto
  simplesmente termina no último mês com dado: **nunca preencha o futuro com zero**.

### Tabela (quando houver)
O cabeçalho tem 12 px em `--ink-40` com divisória de 1 px embaixo. As linhas têm 40 px de
altura, 12 a 14 px de texto e não são listradas. Os números são alinhados à direita e
tabulares.

### Estados
- **Carregando**: *skeleton* com os mesmos tamanhos dos cartões, em `--hover`, com
  pulsação de opacidade entre 0,5 e 1 a cada 1,2 s.
- **Vazio**: o texto "Sem dados para este recorte", centralizado, 14 px, em `--ink-40`.
- **Erro**: um cartão com a mensagem e um botão "Tentar de novo".

---

## 4. Regras de visualização

São as regras que valem em qualquer ferramenta. Elas retomam os fundamentos da aula
de visualização.

1. **Cada cartão responde uma pergunta**, e a pergunta é o título.
2. Compare **períodos iguais** (ex.: jan–set × jan–set). Se o período atual está
   incompleto, diga isso no chip do topo e no subtítulo.
3. Em mapa, compare **taxas** (por 100 mil hab., por cliente...), não contagens
   absolutas: contagem só mostra onde há mais gente. Calcule a taxa como
   **soma(numerador) / soma(denominador)** depois de agregar; nunca tire média de taxas.
4. Barras e eixos de quantidade **começam no zero**.
5. Use **uma cor de destaque** por gráfico. As outras séries ficam neutras.
6. Use rótulos diretos no lugar de legenda sempre que couber.
7. Escolha a escala de cor pelo tipo de dado: sequencial para nível (mapa), divergente
   para desvio em torno de zero, categórica só para categorias sem ordem. **Nunca use
   arco-íris.**
8. Formate os números em pt-BR com `Intl.NumberFormat('pt-BR')`: milhar com ponto,
   decimal com vírgula, Δ com 1 casa e taxa com 1 ou 2 casas.
9. Ponha sempre uma nota de fonte com a origem dos dados, a data de extração e as
   ressalvas.
10. Garanta contraste AA (4,5:1) para texto. Os pastéis são fundo, nunca cor de texto.

---

## 5. Tradução para bibliotecas

| Elemento | ECharts | Plotly | Observable Plot |
|---|---|---|---|
| Fundo do gráfico | `backgroundColor: 'transparent'` | `paper_bgcolor/plot_bgcolor = 'rgba(0,0,0,0)'` | `style: {background: 'transparent'}` |
| Fonte | `textStyle.fontFamily: 'Inter'` | `font.family = 'Inter'` | `style.fontFamily` |
| Grade | `splitLine.lineStyle.color: 'rgba(28,28,28,.1)'` | `gridcolor='rgba(28,28,28,.1)'` | `grid: true` + `stroke-opacity .1` |
| Linhas de eixo | `axisLine.show: false`, `axisTick.show: false` | `showline=False`, `ticks=''`, `zeroline=False` | `axis line` omitido |
| Rótulos de eixo | 12 px, `rgba(28,28,28,.4)` | `tickfont=dict(size=12, color='rgba(28,28,28,.4)')` | idem |
| Tracejado | `lineStyle.type: [4,4]` | `line.dash='dash'` | `strokeDasharray: '4,4'` |
| Mapa | `echarts.registerMap(nome, geojson)` + `visualMap` em `piecewise` | `go.Choropleth(geojson=..., featureidkey='properties.uf')` + `geo.fitbounds='locations'`, `visible=False` | `Plot.geo(geojson, {fill})` + `projection: {type:'mercator', domain: geojson}` |
| Barra de modo | — | `config={'displayModeBar': False}` | — |
