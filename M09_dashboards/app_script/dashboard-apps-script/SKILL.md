---
name: dashboard-apps-script
description: Cria um painel (dashboard) de uma página em Google Apps Script a partir de uma planilha do Google Sheets, com UI moderna no estilo SnowUI (KPIs com variação, mapa, comparação pareada e tendência), conferência dos números com tabela dinâmica e publicação como web app. Use quando alguém pedir um dashboard, painel ou relatório interativo no Apps Script, em cima de uma planilha, ou quiser publicar um painel gratuito no Google. Antes de gerar código, a skill pergunta ao usuário as especificações (dados, perguntas de negócio, métricas, comparação, mapa, filtros, visual e acesso).
---

# Dashboard em Apps Script

Você vai construir um painel de **uma página** que responde perguntas de negócio com
dados de uma planilha do Google. O resultado é um projeto Apps Script (`Code.gs`,
`Index.html`, `Estilos.html`, `App.html`, `Icone.html`, `appsscript.json`) publicado como web app.
O painel já vem com **filtro temporal** (De/Até, os mesmos meses nos dois anos), **menu de métricas**
e a **marca da ferramenta** (ícone + "Painel em Google Apps Script") no topo.

**Não escreva código antes da etapa 4.** Um painel bonito que responde a pergunta
errada não serve para nada.

Arquivos desta skill:

| Arquivo | Para quê |
|---|---|
| `references/perguntas.md` | O questionário de especificação (etapa 2) |
| `references/ui-spec.md` | Tokens, layout, componentes e regras de visualização. Siga à risca. |
| `references/referencia_visual.png` | Como o painel deve parecer (SnowUI) |
| `references/deploy.md` | Publicação pelo editor ou pelo `clasp` |
| `assets/templates/` | Implementação de referência que funciona. Parta dela. |

---

## Etapa 1 — Descobrir os dados

1. Peça o **link da planilha** e o nome da aba.
2. Leia o cabeçalho e 5 linhas. Se você tem acesso ao Google Sheets (conector, MCP, API),
   leia direto; senão, peça ao usuário para colar o cabeçalho e 5 linhas.
3. Classifique as colunas: tempo (data, ano, mês), área geográfica, categoria/métrica,
   valor numérico, denominador (população, clientes...), identificadores.
4. Descubra o **formato**:
   - **longo**: uma linha por período × área × métrica, com uma coluna de valor. É o
     formato que o template espera.
   - **largo**: uma coluna por métrica. Nesse caso você vai adaptar `linhas_()` em
     `Code.gs` para transformar cada coluna numa linha.
5. Veja se as métricas são **somáveis** (contagens, totais, valores em R$). O template só soma.
   - **Contar linhas** (ex.: nº de pedidos): deixe `colunas.valor = ''` e cada linha vale 1.
   - **Média ou percentual** (nota média, % de atraso): transforme em algo somável. Por exemplo,
     "pedidos com nota ≤ 2" vira uma contagem, e "% atrasados" vira atrasados ÷ total. Também dá
     para adaptar `resumo_()` para dividir duas somas. Nunca some médias.
   - **Dimensões que não são métricas** (forma de pagamento, categoria de produto) podem virar o
     grupo do menu ou entrar no recorte de `linhas_()`.
6. Veja o tamanho. Até algumas centenas de áreas (UF, região, loja) cabem no cache. Com milhares
   (municípios) ou mais de ~1 milhão de células, agregue antes numa aba resumida (período × área
   × métrica).
7. Anote o que já dá para inferir e use como **padrão proposto** nas perguntas.

## Etapa 2 — Perguntar as especificações

Siga `references/perguntas.md`. Regras:

- No máximo **duas rodadas** de perguntas. Agrupe tudo numa mensagem numerada, ou use a
  ferramenta de perguntas estruturadas do seu ambiente, se houver (no Claude Code,
  `AskUserQuestion`).
- **Proponha um padrão em cada pergunta**, a partir do que viu na etapa 1. O usuário
  só confirma ou corrige.
- Insista em uma coisa: **quais 1 a 3 perguntas de negócio o painel responde**. Cada
  cartão do painel é a resposta de uma pergunta.

## Etapa 3 — Especificar e confirmar

Escreva um `ESPEC.md` curto com:

1. as perguntas de negócio e, para cada uma, a métrica, a comparação e o visual (tabela
   pergunta → métrica → visual);
2. os KPIs fixos (até 4) e a polaridade de cada métrica: "menor é melhor", "maior é
   melhor" ou neutra;
3. o período comparável. Se o ano atual está incompleto, compare os mesmos meses dos
   dois anos (ex.: jan–set × jan–set);
4. o mapeamento de colunas para o `CONFIG`;
5. o que **não** vai entrar.

Mostre o `ESPEC.md` e **espere a confirmação** antes de seguir.

## Etapa 4 — Gerar o projeto

1. Copie `assets/templates/` para uma pasta nova do projeto.
2. Em `Code.gs`, preencha o bloco `CONFIG`: id da planilha, aba, colunas, KPIs, menu,
   polaridade, perguntas, notas e GeoJSON. Na maioria dos casos é **só isso** que muda.
3. Se a planilha for larga ou tiver outra estrutura, adapte **apenas** `linhas_()`, que
   precisa devolver `{ano, mes, metrica, grupo, unidade, geo, geoNome, valor,
   denominador}`.
4. **Mapa.** O mapa precisa de um GeoJSON cujas feições tenham uma propriedade igual à
   coluna de área (ex.: `uf` = "SP"). Ponha o arquivo no Drive (`geojson.driveId`) ou
   use uma URL pública (`geojson.url`). Para as UFs do Brasil, a malha vem da API do IBGE
   (`servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=UF`),
   mas a propriedade dela é o código numérico (`codarea`). Há uma versão pronta, com a
   propriedade `uf` (sigla) e os anéis no sentido certo para qualquer biblioteca:
   `https://cdn.jsdelivr.net/gh/chcomin/curso-processamento-e-visualizacao-de-dados@main/M09_dashboards/dados/br_uf.geojson`.
   Use-a em `geojson.url`. Sem área geográfica, deixe `colunas.geo = ''`: os cartões de mapa
   e pareado somem.
   - **Sem denominador**, o mapa mostra totais. Avise o usuário que um mapa de contagem
     mostra onde há mais gente, não onde o risco é maior.
   - **Ano atual incompleto**: o template compara o último ano com o anterior, só nos meses
     que o último ano tem. O usuário não precisa fazer nada.
5. **Marca e cores.** O ícone fica em `Icone.html` e o nome da ferramenta em `CONFIG.ferramenta`.
   Para mudar a cor de destaque, troque só os tokens `--surface-blue`, `--surface-lav`, `--data-1`,
   `--data-2` e `--seq-0…4` em `Estilos.html`. `--good` e `--bad` ficam: são o significado do Δ.
6. **Formato.** Para totais em R$, kg ou com casas decimais, preencha `CONFIG.formato`, por
   exemplo `{decimais: 2, prefixo: 'R$ '}`.
7. **Visual.** Mantenha os tokens e os componentes de `references/ui-spec.md`. Pode
   mudar textos, quais cartões aparecem e a cor de destaque, se o usuário pedir. Não
   troque o estilo por outro: o template já está no padrão.
8. Não invente dados nem números. Tudo que aparece na tela vem da planilha.

## Etapa 5 — Conferir os números

LLMs erram contas. Antes de entregar:

1. Rode `criarTabelaConferencia()` no editor. Ela cria a aba **conferencia** com uma
   **tabela dinâmica nativa**: a soma do valor por métrica e ano, só nos meses do
   período comparável.
2. Compare cada KPI da tela com a tabela dinâmica. Para conferir o Δ%, calcule
   `(atual / anterior − 1) × 100`.
3. Para as taxas, confira uma área à mão: `soma(valor) / denominador × 100000`.
4. Se algo não bater, o erro está no `CONFIG` (coluna errada) ou em `linhas_()`. Nunca
   "ajuste" o número na tela.

Mostre ao usuário a tabela de conferência ao lado dos KPIs.

## Etapa 6 — Publicar

Siga `references/deploy.md`. Resumo:

- Pelo **editor**: crie um projeto em script.google.com, cole os 6 arquivos, rode uma
  função uma vez para autorizar e faça **Implantar → Nova implantação → App da Web**.
- Pelo **clasp**: `clasp create --type standalone --parentId <pasta>`, depois
  `clasp push` e `clasp deploy`.
- O acesso vem de `appsscript.json` → `webapp.access`, e a escolha da etapa 2 decide:
  - `ANYONE_ANONYMOUS`: qualquer pessoa com o link;
  - `DOMAIN`: só a organização;
  - `MYSELF`: só você.
- Depois de mudar a planilha, rode `limparCache()` (ou aumente `versaoCache`). O cache
  dura 6 h. **Sempre aumente `versaoCache` quando mudar o formato do que o servidor devolve**
  (em `resumo_()`). Se não aumentar, o navegador recebe o formato antigo do cache e a página
  quebra.

## Entrega

Entregue ao usuário:

- o link do web app;
- o link do projeto;
- a tabela de conferência;
- o que ficou fora do escopo.

## Erros comuns

| Sintoma | Causa | Correção |
|---|---|---|
| "Coluna X não encontrada" | Nome de coluna diferente no `CONFIG` | Copie o cabeçalho exato |
| Mapa vazio | Propriedade do GeoJSON ≠ valores da coluna de área | Ajuste `geojson.propriedade`, ou a coluna |
| "Métricas do CONFIG que não existem" | Nome em `kpis` ou `menu` diferente da planilha | Copie o nome exato |
| Números grandes demais ou vazios | Valores como texto ("1.234,5", "R$ 10") | O template converte; se ainda falhar, limpe a coluna |
| KPI com o dobro do esperado | Linhas repetidas, ou "total" misturado com detalhe | Filtre em `linhas_()` |
| Taxa absurda | Denominador somado várias vezes | O denominador deve ser constante por área e ano. O template usa um valor por área e ano. |
| Página "Autorização necessária" para visitantes | O dono nunca autorizou os escopos | O dono roda uma função no editor uma vez |
| Números antigos depois de editar a planilha | Cache | `limparCache()` |
