---
name: pvd-dashboard-apps-script-demo
description: Monta um painel (dashboard) de uma página em Google Apps Script a partir de uma planilha do Google Sheets, para responder 1 ou 2 perguntas que o usuário define. O painel tem filtro de meses, 2 gráficos (evolução no tempo e comparação entre grupos) e 1 tabela-resumo, e compara o ano atual com o anterior nos mesmos meses. Use quando pedirem um dashboard, painel ou relatório simples no Apps Script, ou sobre uma planilha do Google. Antes de gerar código, pergunta ao usuário o recorte, as perguntas e as colunas.
---

# Painel de uma página em Apps Script

Você vai entregar um web app do Google Apps Script com **uma página só**, sem abas e sem menus:

```text
┌───────────────────────────────────────────────────────────────┐
│ Título · subtítulo (recorte e fonte)        De [jan▾] até [set▾] │
├───────────────────────────────┬───────────────────────────────┤
│ Pergunta 1                     │ Pergunta 2                     │
│ resposta em uma frase          │ resposta em uma frase          │
│ gráfico de linhas: mês a mês,  │ gráfico de barras: grupos      │
│ ano atual × ano anterior       │ ordenados + barra de referência│
├───────────────────────────────┴───────────────────────────────┤
│ Tabela-resumo por grupo: anterior | atual | Δ% | taxa           │
└───────────────────────────────────────────────────────────────┘
```

**As perguntas são do usuário.** Seu trabalho é entender os dados, ligar cada pergunta a um
gráfico, preencher o `CONFIG` do modelo e conferir os números. **Não escreva código antes da
etapa 4.** Os três modelos do fim deste arquivo já funcionam: parta deles.

## 1. Ler os dados

1. Peça o link da planilha e o nome da aba (se o pedido já trouxer, siga).
2. Leia o cabeçalho e 5 linhas. Use o acesso ao Google Sheets que você tiver (conector, MCP,
   API ou um CSV exportado). Se não tiver nenhum, peça ao usuário para colar o cabeçalho e 5 linhas.
3. Identifique:
   - **tempo**: uma coluna de data, ou as colunas ano e mês;
   - **grupo**: a categoria que será comparada (estado, loja, produto, curso...);
   - **valor**: um número que se pode **somar** (contagem, total, R$). Se não houver, o painel
     conta linhas. Nesse caso, avise o usuário do que está sendo contado (ex.: número de pedidos,
     não faturamento) e escreva isso na `unidade`;
   - **denominador** (opcional): população, clientes, alunos. Precisa ser constante por grupo e ano.
     Com ele, o painel mostra taxa (valor ÷ denominador × 100 mil, por exemplo);
   - **colunas de recorte**: as que definem o segmento (tipo de evento, região, categoria).
4. Nunca some médias ou percentuais. Se a métrica pedida for uma média, avise que o modelo
   soma e proponha uma contagem ou um total no lugar.
5. Formato esperado: **longo**, com uma linha por período × grupo (× outras categorias). Se cada
   métrica estiver numa coluna (formato largo), use a coluna da métrica pedida como `valor`.

## 2. Perguntar ao usuário (uma rodada só)

Mande **uma única mensagem numerada**, ou use a ferramenta de perguntas do seu ambiente (no
Claude Code, `AskUserQuestion`). Em cada item, proponha um padrão a partir do que viu na etapa 1.
O usuário só confirma ou corrige. O que o pedido já respondeu não vira pergunta: confirme numa
linha ("Recorte: X, como você pediu").

1. **Recorte**: qual parte dos dados entra? Por exemplo, `tipo = "X"` e `regiao = "Y"`. Um painel
   bom foca num segmento.
2. **Perguntas**: 1 ou 2, nas palavras do usuário. Se vierem mais, peça para escolher 2.
3. **Colunas**: tempo, grupo, valor e denominador (proponha os nomes que encontrou).
4. **Polaridade**: subir é bom ou ruim? Crimes, custos e atrasos: menor é melhor. Vendas e
   matrículas: maior é melhor.
5. **Título** e **quem pode abrir o link**: qualquer pessoa, só a organização, ou só o dono.

## 3. Confirmar o plano

Mostre um plano curto e **espere o "ok"** do usuário:

| Pergunta do usuário | Gráfico | Métrica | Período |
|---|---|---|---|
| (pergunta 1) | linhas, mês a mês, ano atual × anterior | soma do valor | meses do filtro |
| (pergunta 2) | barras por grupo, ordenadas, com uma barra cinza de referência | taxa (ou soma) | meses do filtro |
| (resumo) | tabela por grupo | anterior, atual, Δ%, taxa | meses do filtro |

Como ligar uma pergunta a um gráfico:

| A pergunta é sobre... | Gráfico |
|---|---|
| tendência: "caiu?", "subiu?", "quando?", "como evoluiu?" | gráfico 1 (linhas no tempo) |
| comparação: "onde?", "quem?", "qual é maior?", ranking | gráfico 2 (barras ordenadas) |
| composição: "quanto de cada tipo?" | troque o gráfico 2 por barras empilhadas em 100% |
| relação entre duas métricas | troque um dos gráficos por dispersão e avise que sai do modelo |

Se uma pergunta não cabe em nenhum gráfico, diga isso ao usuário. Não force um gráfico.

**Período comparável.** O painel compara os **dois anos mais recentes** do recorte (anos mais
antigos ficam de fora), **nos mesmos meses**. Se o ano atual vai só até setembro, o filtro vai de
jan a set e vale para os dois anos. Se os dados tiverem só um ano, o painel mostra só esse ano,
sem Δ%. Se o ano anterior tiver meses faltando, avise o usuário: a comparação fica desigual.

**Barra de referência do gráfico 2.** Com denominador, é o total do recorte (soma ÷ soma, nunca
média de taxas). Sem denominador, é a média por grupo.

## 4. Gerar o projeto

1. Crie uma pasta com os 3 arquivos da seção **Modelos**: `appsscript.json`, `Code.gs` e `Index.html`.
2. Em `Code.gs`, preencha **só o `CONFIG`**:
   - o id da planilha (o trecho do link entre `/d/` e `/edit`) e a aba;
   - o recorte e as colunas. Com uma coluna de data, preencha `data` (ano e mes são ignorados);
   - os textos: título, subtítulo, **as perguntas do usuário**, fonte, rótulos e unidade. Não
     escreva o período no subtítulo: o filtro e o selo ao lado dele já mostram os meses;
   - a polaridade (`menorMelhor`).
3. Mude o `Index.html` só se o plano trocou o tipo de um gráfico. Mantenha o layout e as regras de visual.
4. Se `webapp.access` não for "qualquer pessoa", troque `ANYONE_ANONYMOUS` por `DOMAIN` (só a organização) ou `MYSELF` (só o dono).
5. Não invente números. Tudo que aparece na tela vem da planilha.

## 5. Conferir os números

LLMs erram contas. O painel precisa bater com uma conta feita fora dele:

1. No Sheets, use **Inserir → Tabela dinâmica** sobre a aba:
   - Linhas: o grupo;
   - Colunas: o ano;
   - Valores: SOMA do valor;
   - Filtros: as colunas do recorte e o mês (só os meses do filtro do painel).
2. Compare com a tabela do painel. Confira o total por grupo nos dois anos e o Δ% = (atual ÷
   anterior − 1) × 100. Para a taxa, confira um grupo à mão: soma ÷ denominador × 100 mil.
3. Se você consegue ler os dados (CSV, pandas), calcule os mesmos totais e mostre ao usuário lado a lado.
4. Se algo não bate, o erro está no `CONFIG` (coluna ou recorte). Nunca ajuste o número na tela.

## 6. Publicar

**Pelo editor** (não precisa instalar nada):

1. Em script.google.com, crie um **Novo projeto**.
2. Cole o `Code.gs`. Em **+ → HTML**, crie `Index` (o editor acrescenta o `.html`) e cole.
3. Em **Configurações do projeto**, marque "Mostrar o arquivo de manifesto appsscript.json" e cole.
4. Escolha a função `getDados` → **Executar**. O Google pede autorização uma vez: aceite. Sem
   isso, quem abrir o link vê "acesso negado".
5. Em **Implantar → Nova implantação → App da Web**, escolha "Executar como: **Eu**" e o acesso
   combinado. Copie o link que termina em `/exec`.

**Pelo terminal (clasp)**:

```bash
clasp create-script --type standalone --title "<título>"
# o create-script troca o appsscript.json pelo padrão: restaure o do modelo antes do push
clasp push -f
clasp create-deployment -d "v1"                      # imprime o id da implantação
clasp push -f && clasp create-deployment -i <id> -d "v2"   # atualiza sem mudar o link
```

Mesmo pelo clasp, o dono executa `getDados` no editor uma vez para autorizar.
Mudou a planilha? Rode `limparCache()` (o cache dura 6 h) ou aumente `versaoCache`.

**Entregue ao usuário**: o link do web app, o plano da etapa 3 e a conferência da etapa 5.

## Regras de visual

- **Layout.** Uma página, sem abas. No topo: o rótulo "Painel em Google Apps Script", o título,
  o subtítulo (recorte e fonte) e o filtro De/Até. Duas colunas, que viram uma abaixo de 860 px,
  sem rolagem horizontal.
- **Títulos.** O título de cada cartão é a **pergunta do usuário**. Logo abaixo vem uma frase
  com a resposta em número.
- **Cores.**
  - Uma cor de destaque (`--destaque`) para o ano atual e para os grupos acima do total. O resto
    usa `--destaque-claro`.
  - O ano anterior e a barra de referência são sempre cinza (`--anterior`), e a linha do ano anterior é tracejada.
  - Verde (`--bom`) e vermelho (`--ruim`) só aparecem no Δ%, sempre com seta e sinal, para não
    depender só da cor. A polaridade decide qual é qual.
  - Para mudar a paleta, troque só `--destaque` e `--destaque-claro`.
- **Gráficos.** As barras começam no zero e vêm ordenadas. Use o rótulo direto no fim da linha
  ou da barra, em vez de legenda. O gráfico 2 mostra no máximo `maxBarras` grupos (12, os maiores), e a
  tabela mostra todos.
- **Números.** Formato pt-BR: `1.234`, `−17,7%`, taxa com 2 casas. O sinal de menos é `−`.
- **Aparência.** Fonte Inter. Fundo `#F7F9FB`. Cartões brancos com raio de 16 px e sombra leve.

## Erros comuns

| Sintoma | Causa | Correção |
|---|---|---|
| "Coluna X não existe" | nome diferente no `CONFIG` | copie o cabeçalho exato |
| "Nenhuma linha no recorte" | valor do recorte escrito diferente | copie o valor exato da planilha |
| Visitante vê "acesso negado" ou "autorização necessária" | o dono nunca autorizou | execute `getDados` no editor uma vez |
| "As permissões especificadas não são suficientes para chamar SpreadsheetApp.openById" | escopo só de leitura no `appsscript.json` | use `https://www.googleapis.com/auth/spreadsheets` (como no modelo) e autorize de novo |
| Números antigos depois de mudar a planilha | cache | `limparCache()` ou aumente `versaoCache` |
| Taxa absurda | o denominador muda dentro do grupo e ano | use outra coluna ou deixe `denominador: ''` |
| Total com o dobro do esperado | linhas de total misturadas com o detalhe | inclua no recorte a coluna que separa o total |
| Filtro de meses só vai até um mês do meio do ano | o ano atual ainda não acabou | é o esperado: o painel compara os mesmos meses |

## Modelos

Copie os três arquivos como estão e mude só o `CONFIG` (etapa 4).

### `appsscript.json`

```json
{
  "timeZone": "America/Sao_Paulo",
  "runtimeVersion": "V8",
  "exceptionLogging": "STACKDRIVER",
  "oauthScopes": ["https://www.googleapis.com/auth/spreadsheets"],
  "webapp": { "executeAs": "USER_DEPLOYING", "access": "ANYONE_ANONYMOUS" }
}
```

### `Code.gs`

```javascript
/**
 * Painel de uma página em Google Apps Script: servidor.
 * Lê a aba, aplica o recorte e devolve, para cada grupo, o valor mês a mês do ano
 * anterior e do ano atual. O navegador (Index.html) soma os meses do filtro.
 * Para outra planilha ou outras perguntas, mude só o CONFIG.
 */
const CONFIG = {
  planilhaId: 'COLE_O_ID_DA_PLANILHA',   // trecho do link entre /d/ e /edit
  aba: 'dados',
  titulo: 'Título do painel',
  subtitulo: 'Recorte · fonte',
  ferramenta: 'Google Apps Script',

  // Recorte fixo: { coluna: 'valor' } ou { coluna: ['valor1', 'valor2'] }. {} = todas as linhas.
  recorte: {},
  colunas: {
    data: '',               // coluna de data; se preenchida, ano e mes são ignorados
    ano: 'ano', mes: 'mes',
    grupo: 'grupo',         // categoria do gráfico 2 e da tabela (estado, loja, produto...)
    grupoNome: '',          // nome por extenso do grupo (opcional)
    valor: 'valor',         // número somável; '' = conta linhas
    denominador: ''         // opcional, constante por grupo e ano (ex.: populacao); vira taxa
  },
  taxaPor: 100000, rotuloTaxa: 'por 100 mil hab.',   // só valem com denominador
  rotuloGrupo: 'Grupo', nomeTotal: 'Total', unidade: 'registros', decimais: 0,
  maxBarras: 12,            // o gráfico 2 mostra só os maiores; a tabela mostra todos
  menorMelhor: false,       // true quando cair é bom (crimes, custos, atrasos)
  perguntas: ['Pergunta 1 do usuário', 'Pergunta 2 do usuário'],
  fonte: 'Fonte: ...',
  versaoCache: 1            // aumente quando mudar a planilha ou o CONFIG
};

function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle(CONFIG.titulo + ' · ' + CONFIG.ferramenta)
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

/** Chamada pelo navegador. Rode uma vez no editor para autorizar a leitura da planilha. */
function getDados() {
  const cache = CacheService.getScriptCache();
  const chave = 'painel-' + CONFIG.versaoCache;
  const salvo = cache.get(chave);
  if (salvo) return JSON.parse(salvo);

  const aba = SpreadsheetApp.openById(CONFIG.planilhaId).getSheetByName(CONFIG.aba);
  if (!aba) throw new Error('Aba "' + CONFIG.aba + '" não encontrada.');
  const valores = aba.getDataRange().getValues();
  const cab = valores.shift().map(c => String(c).trim());
  const col = nome => {
    const i = cab.indexOf(nome);
    if (i < 0) throw new Error('Coluna "' + nome + '" não existe. Colunas: ' + cab.join(', '));
    return i;
  };
  const c = {};
  const usarData = !!CONFIG.colunas.data;
  Object.keys(CONFIG.colunas).forEach(k => {
    const ignorar = usarData && (k === 'ano' || k === 'mes');
    c[k] = CONFIG.colunas[k] && !ignorar ? col(CONFIG.colunas[k]) : -1;
  });
  const recorte = Object.keys(CONFIG.recorte).map(k => [col(k), [].concat(CONFIG.recorte[k]).map(String)]);

  const linhas = [];
  valores.forEach(r => {
    if (!recorte.every(([i, aceitos]) => aceitos.indexOf(String(r[i]).trim()) >= 0)) return;
    const t = tempo_(r, c);
    if (!t) return;
    const grupo = String(r[c.grupo]).trim();
    linhas.push({
      ano: t.ano, mes: t.mes, grupo,
      nome: c.grupoNome >= 0 ? String(r[c.grupoNome]).trim() : grupo,
      v: c.valor >= 0 ? numero_(r[c.valor]) : 1,
      den: c.denominador >= 0 ? numero_(r[c.denominador]) : null
    });
  });
  if (!linhas.length) throw new Error('Nenhuma linha no recorte ' + JSON.stringify(CONFIG.recorte) + '.');

  const anos = [...new Set(linhas.map(l => l.ano))].sort((a, b) => a - b);
  const atual = anos[anos.length - 1];
  const anterior = anos.length > 1 ? anos[anos.length - 2] : null;
  const grupos = {};
  let ultimoMes = 0;
  linhas.forEach(l => {
    if (l.ano !== atual && l.ano !== anterior) return;
    const g = grupos[l.grupo] || (grupos[l.grupo] = {
      id: l.grupo, nome: l.nome,
      anterior: Array(12).fill(null), atual: Array(12).fill(null), denAnterior: null, denAtual: null
    });
    const qual = l.ano === atual ? 'atual' : 'anterior';
    if (l.v !== null) {
      g[qual][l.mes - 1] = (g[qual][l.mes - 1] || 0) + l.v;
      if (qual === 'atual') ultimoMes = Math.max(ultimoMes, l.mes);
    }
    if (l.den) g[qual === 'atual' ? 'denAtual' : 'denAnterior'] = l.den;
  });

  const saida = { config: CONFIG, anterior, atual, ultimoMes, grupos: Object.values(grupos) };
  try { cache.put(chave, JSON.stringify(saida), 21600); } catch (e) { /* mais de 100 KB: segue sem cache */ }
  return saida;
}

/** Ano e mês da linha, a partir da coluna de data ou das colunas ano e mes. */
function tempo_(r, c) {
  if (c.data >= 0) {
    const d = r[c.data];
    if (d instanceof Date) return { ano: d.getFullYear(), mes: d.getMonth() + 1 };
    const s = String(d).trim();
    let m = s.match(/^(\d{4})-(\d{1,2})/);                 // 2026-03-01
    if (m) return { ano: +m[1], mes: +m[2] };
    m = s.match(/^\d{1,2}\/(\d{1,2})\/(\d{4})/);            // 01/03/2026
    return m ? { ano: +m[2], mes: +m[1] } : null;
  }
  const ano = Number(r[c.ano]), mes = Number(r[c.mes]);
  return ano && mes >= 1 && mes <= 12 ? { ano, mes } : null;
}

/** Número de uma célula; aceita texto em pt-BR ("1.234,5", "R$ 10"). Vazio = null. */
function numero_(x) {
  if (typeof x === 'number') return isFinite(x) ? x : null;
  const s = String(x).replace(/[^\d,.\-]/g, '');
  if (!s) return null;
  const n = s.indexOf(',') >= 0 ? Number(s.replace(/\./g, '').replace(',', '.')) : Number(s);
  return isFinite(n) ? n : null;
}

/** Rode depois de mudar a planilha (o cache dura 6 h). */
function limparCache() {
  CacheService.getScriptCache().remove('painel-' + CONFIG.versaoCache);
}
```

### `Index.html`

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<base target="_top">
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/echarts@5.6.0/dist/echarts.min.js"></script>
<style>
  :root {
    --fundo: #F7F9FB; --cartao: #FFFFFF; --tinta: #1C1C1C;
    --tinta-60: rgba(28,28,28,.62); --tinta-40: rgba(28,28,28,.45); --linha: rgba(28,28,28,.10);
    --destaque: #1A73E8;         /* ano atual e grupos acima do total */
    --destaque-claro: #BCD4F6;   /* grupos abaixo do total */
    --anterior: #9AA4B2;         /* ano anterior: sempre cinza e tracejado */
    --bom: #0F7B5F; --ruim: #C0362C;
    --raio: 16px; --vao: 24px;
    --fonte: "Inter", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--fundo); color: var(--tinta); font: 14px/1.45 var(--fonte); }
  h1, h2, p { margin: 0; }
  .topo, .grade, .rodape { max-width: 1240px; margin: 0 auto; }
  .topo { display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between; gap: 16px; padding: 28px 32px 0; }
  .marca { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--tinta-40); margin-bottom: 6px; }
  .marca b { color: var(--tinta-60); font-weight: 600; }
  h1 { font-size: 24px; font-weight: 600; line-height: 1.25; }
  .sub { color: var(--tinta-60); margin-top: 4px; }
  .filtro { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; font-size: 13px; color: var(--tinta-60); }
  .filtro select { font: inherit; color: var(--tinta); background: var(--cartao); border: 1px solid var(--linha); border-radius: 8px; padding: 6px 10px; cursor: pointer; }
  .chip { background: rgba(28,28,28,.05); border-radius: 999px; padding: 4px 12px; font-size: 12px; white-space: nowrap; }
  .grade { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--vao); padding: 24px 32px; }
  .cartao { background: var(--cartao); border-radius: var(--raio); padding: 24px; box-shadow: 0 1px 3px rgba(28,28,28,.06); min-width: 0; }
  .largo { grid-column: 1 / -1; }
  .cartao h2 { font-size: 16px; font-weight: 600; }
  .resposta { color: var(--tinta-60); margin: 4px 0 12px; }
  .resposta b { color: var(--tinta); font-weight: 600; }
  .grafico { height: 320px; }
  .rolagem { overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; margin-top: 8px; }
  th, td { padding: 10px 12px; text-align: right; border-bottom: 1px solid var(--linha); white-space: nowrap; }
  th:first-child, td:first-child { text-align: left; }
  th { font-weight: 400; font-size: 12px; color: var(--tinta-40); }
  tr.total td { font-weight: 600; border-bottom: 0; border-top: 2px solid var(--linha); }
  .bom { color: var(--bom); } .ruim { color: var(--ruim); }
  .rodape { padding: 0 32px 32px; font-size: 12px; color: var(--tinta-40); }
  @media (max-width: 860px) {
    .topo { padding: 20px 16px 0; }
    .grade { grid-template-columns: 1fr; padding: 16px; gap: 16px; }
    .cartao { padding: 16px; }
    .grafico { height: 280px; }
    th, td { padding: 8px 4px; font-size: 13px; }
    td:first-child { white-space: normal; }
    .rodape { padding: 0 16px 24px; }
  }
</style>
</head>
<body>
<header class="topo">
  <div>
    <p class="marca">
      <svg viewBox="0 0 24 24" width="16" height="16" fill="#4285F4" aria-hidden="true"><path d="M12.363 2.54a3.136 3.136 0 0 0-.376.022 2.864 2.864 0 0 0-1.589.828c-.562.58-.82 1.115-.773 1.943-.01.264.193 1.023.272 1.274 1.115 3.546 2.09 6.75 3.26 10.279.08.246.168.486.267.72.02.047.035.046.048-.004.077-.297.174-.612.29-.945.894-2.576 1.772-5.14 2.633-7.696a.345.345 0 0 0 .004-.217 163.054 163.054 0 0 0-1.49-4.572 2.603 2.603 0 0 0-.704-.933c-.55-.46-1.166-.694-1.842-.7Zm9.078.117a2.734 2.734 0 0 0-2.878 1.828l-4.576 13.289a2.734 2.734 0 0 0 1.695 3.475l.12.04a2.734 2.734 0 0 0 3.475-1.694L23.85 6.307a2.734 2.734 0 0 0-1.695-3.476c-.233-.1-.506-.124-.716-.174ZM12.375 3.96a1.396 1.396 0 1 1 0 2.791 1.395 1.395 0 0 1 0-2.79zm8.809.07a1.402 1.402 0 1 1 0 2.803 1.402 1.402 0 0 1 0-2.803zM5.419 7.605a2.853 2.853 0 0 0-.468.052 2.683 2.683 0 0 0-1.337.627 2.62 2.62 0 0 0-.924 1.833 3.808 3.808 0 0 0 0 .648 2.52 2.52 0 0 0 .673 1.52c.221.238.465.454.732.648 3.043 2.21 6.08 4.43 9.108 6.664a.78.78 0 0 0 .158.089c.03-.043.032-.098.007-.167a17.409 17.409 0 0 0-.317-1.066 532.752 532.752 0 0 1-2.02-6.251 41.91 41.91 0 0 0-.497-1.477c-.967-.849-2.078-1.6-3.023-2.302A3.848 3.848 0 0 0 6.153 7.7a2.388 2.388 0 0 0-.734-.094Zm.02 1.424a1.398 1.398 0 1 1 0 2.796 1.398 1.398 0 0 1 0-2.796zm-2.458 6.792c-.733-.006-1.375.202-1.927.622a2.72 2.72 0 0 0-.95 1.45 2.78 2.78 0 0 0-.09 1.04 2.74 2.74 0 0 0 .695 1.583c.664.578 1.26.85 2 .945 1.42-.005 2.84-.012 4.262-.02h.418c2.277-.003 4.513-.002 6.706.003.148.005.28.003.392-.01.06-.005.091-.031.092-.077a10.656 10.656 0 0 0-.834-.653 488.746 488.746 0 0 1-6.57-4.815.236.236 0 0 0-.14-.047c-1.34-.003-2.691-.01-4.054-.02zm-.19 1.418a1.402 1.402 0 1 1 0 2.803 1.402 1.402 0 0 1 0-2.803zm13.874.002a1.4 1.4 0 1 1 0 2.8 1.4 1.4 0 0 1 0-2.8z"/></svg>
      Painel em <b>Google Apps Script</b>
    </p>
    <h1 id="titulo">Carregando…</h1>
    <p class="sub" id="subtitulo"></p>
  </div>
  <div class="filtro" role="group" aria-label="Filtro de período">
    De <select id="de" aria-label="Mês inicial"></select>
    até <select id="ate" aria-label="Mês final"></select>
    <span class="chip" id="chip"></span>
  </div>
</header>
<main class="grade" id="grade">
  <section class="cartao"><h2 id="p1"></h2><p class="resposta" id="r1"></p><div class="grafico" id="g1"></div></section>
  <section class="cartao"><h2 id="p2"></h2><p class="resposta" id="r2"></p><div class="grafico" id="g2"></div></section>
  <section class="cartao largo"><h2 id="t-titulo"></h2><div class="rolagem"><table id="tabela"></table></div></section>
</main>
<footer class="rodape" id="fonte"></footer>
<script>
const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
const $ = id => document.getElementById(id);
const cor = nome => getComputedStyle(document.documentElement).getPropertyValue(nome).trim();
const fmt = (x, d = 0) => (x == null || !isFinite(x)) ? '—'
  : x.toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d }).replace('-', '−');
const esc = s => String(s).replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
let D, g1, g2;

google.script.run.withSuccessHandler(iniciar).withFailureHandler(e => erro(e.message || e)).getDados();

function iniciar(dados) {
  D = dados;
  const C = D.config;
  $('titulo').textContent = C.titulo;
  $('subtitulo').textContent = C.subtitulo;
  $('p1').textContent = C.perguntas[0] || '';
  $('p2').textContent = C.perguntas[1] || '';
  $('fonte').textContent = C.fonte;
  const opcoes = MESES.slice(0, D.ultimoMes).map((m, i) => '<option value="' + (i + 1) + '">' + m + '</option>').join('');
  $('de').innerHTML = opcoes;
  $('ate').innerHTML = opcoes;
  $('de').value = 1;
  $('ate').value = D.ultimoMes;
  $('de').onchange = $('ate').onchange = () => {
    if (+$('de').value > +$('ate').value) { const t = $('de').value; $('de').value = $('ate').value; $('ate').value = t; }
    desenhar();
  };
  g1 = echarts.init($('g1'));
  g2 = echarts.init($('g2'));
  window.addEventListener('resize', () => { g1.resize(); g2.resize(); });
  desenhar();
}

// soma dos meses a..b (1 a 12); null se não houver nenhum dado
function soma(meses, a, b) {
  let s = null;
  for (let m = a; m <= b; m++) if (meses[m - 1] != null) s = (s || 0) + meses[m - 1];
  return s;
}
const variacao = (atu, ant) => (ant ? (atu / ant - 1) * 100 : null);
function textoDelta(d) {
  if (d == null) return '—';
  const piorou = D.config.menorMelhor ? d > 0 : d < 0;
  const classe = Math.abs(d) < 0.05 ? '' : (piorou ? 'ruim' : 'bom');
  return '<span class="' + classe + '">' + (d > 0 ? '▲ +' : d < 0 ? '▼ ' : '') + fmt(d, 1) + '%</span>';
}

function desenhar() {
  const C = D.config, a = +$('de').value, b = +$('ate').value;
  const comTaxa = !!C.colunas.denominador, temAnterior = D.anterior != null;
  const periodo = a === b ? MESES[a - 1] : MESES[a - 1] + '–' + MESES[b - 1];
  $('chip').textContent = periodo + ' · ' + (temAnterior ? D.anterior + ' × ' + D.atual : D.atual);

  // ---- agregação do intervalo, por grupo e no total
  const linhas = D.grupos.map(g => {
    const atu = soma(g.atual, a, b), ant = temAnterior ? soma(g.anterior, a, b) : null;
    return { id: g.id, nome: g.nome, atu, ant, delta: variacao(atu, ant), den: g.denAtual,
      taxa: comTaxa && g.denAtual && atu != null ? atu / g.denAtual * C.taxaPor : null };
  });
  const tot = { nome: C.nomeTotal, atu: 0, ant: temAnterior ? 0 : null, den: 0 };
  linhas.forEach(l => {
    tot.atu += l.atu || 0;
    if (temAnterior) tot.ant += l.ant || 0;
    if (l.atu != null) tot.den += l.den || 0;
  });
  tot.delta = variacao(tot.atu, tot.ant);
  tot.taxa = comTaxa && tot.den ? tot.atu / tot.den * C.taxaPor : null;
  const medida = comTaxa ? 'taxa' : 'atu', casas = comTaxa ? 2 : C.decimais;
  linhas.sort((p, q) => (q[medida] == null ? -Infinity : q[medida]) - (p[medida] == null ? -Infinity : p[medida]));
  const base = { animationDuration: 300, textStyle: { fontFamily: 'Inter, system-ui, sans-serif' } };

  // ---- gráfico 1 (pergunta 1): mês a mês, ano atual × anterior
  const meses = [];
  for (let m = a; m <= b; m++) meses.push(m);
  const serie = qual => meses.map(m => D.grupos.reduce((s, g) => g[qual][m - 1] == null ? s : (s || 0) + g[qual][m - 1], null));
  $('r1').innerHTML = temAnterior
    ? textoDelta(tot.delta) + ' · <b>' + fmt(tot.atu, C.decimais) + '</b> em ' + D.atual + ' contra ' + fmt(tot.ant, C.decimais) + ' em ' + D.anterior + ' (' + periodo + ')'
    : '<b>' + fmt(tot.atu, C.decimais) + '</b> ' + esc(C.unidade) + ' em ' + D.atual + ' (' + periodo + ')';
  const series = [];
  if (temAnterior) series.push({ name: String(D.anterior), type: 'line', data: serie('anterior'), showSymbol: meses.length === 1,
    lineStyle: { color: cor('--anterior'), width: 2, type: 'dashed' }, itemStyle: { color: cor('--anterior') },
    endLabel: { show: true, formatter: String(D.anterior), color: cor('--tinta-60') } });
  series.push({ name: String(D.atual), type: 'line', data: serie('atual'), symbolSize: 6,
    lineStyle: { color: cor('--destaque'), width: 3 }, itemStyle: { color: cor('--destaque') },
    endLabel: { show: true, formatter: String(D.atual), color: cor('--destaque'), fontWeight: 600 } });
  g1.setOption(Object.assign({}, base, {
    grid: { left: 8, right: 48, top: 16, bottom: 8, containLabel: true },
    tooltip: { trigger: 'axis', valueFormatter: v => fmt(v, C.decimais) },
    xAxis: { type: 'category', data: meses.map(m => MESES[m - 1]), boundaryGap: false, axisTick: { show: false },
      axisLine: { lineStyle: { color: cor('--linha') } }, axisLabel: { color: cor('--tinta-40') } },
    yAxis: { type: 'value', min: 0, splitLine: { lineStyle: { color: cor('--linha') } },
      axisLabel: { color: cor('--tinta-40'), formatter: v => fmt(v) } },
    series
  }), true);

  // ---- gráfico 2 (pergunta 2): grupos ordenados + uma barra cinza de referência (total ou média)
  const comDado = linhas.filter(l => l[medida] != null);
  const ref = comTaxa ? tot.taxa : tot.atu / Math.max(1, comDado.length);
  const nomeRef = comTaxa ? C.nomeTotal : 'Média';
  const lider = comDado[0];
  const maximo = C.maxBarras || 12;
  $('r2').innerHTML = lider ? '<b>' + esc(lider.nome) + '</b>: ' + fmt(lider[medida], casas) + ' ' + esc(comTaxa ? C.rotuloTaxa : C.unidade)
    + ' · ' + esc(nomeRef) + ': ' + fmt(ref, casas) + (comDado.length > maximo ? ' · ' + maximo + ' maiores de ' + comDado.length : '') : '';
  const barras = comDado.slice(0, maximo).map(l => ({ nome: l.id, valor: l[medida], cor: l[medida] > ref ? cor('--destaque') : cor('--destaque-claro') }));
  barras.push({ nome: nomeRef, valor: ref, cor: cor('--anterior'), ref: true });
  barras.sort((p, q) => p.valor - q.valor);   // o ECharts desenha a primeira categoria embaixo
  g2.setOption(Object.assign({}, base, {
    grid: { left: 8, right: 64, top: 8, bottom: 8, containLabel: true },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: v => fmt(v, casas) },
    xAxis: { type: 'value', min: 0, show: false },
    yAxis: { type: 'category', data: barras.map(x => x.nome), axisTick: { show: false }, axisLine: { show: false },
      axisLabel: { interval: 0, color: cor('--tinta-60'), fontSize: 13, formatter: v => (v === nomeRef ? '{ref|' + v + '}' : v), rich: { ref: { fontWeight: 600, color: cor('--tinta') } } } },
    series: [{ type: 'bar', barMaxWidth: 32, itemStyle: { borderRadius: [0, 6, 6, 0] },
      data: barras.map(x => ({ value: x.valor, itemStyle: { color: x.cor } })),
      label: { show: true, position: 'right', color: cor('--tinta-60'), formatter: p => fmt(p.value, casas) } }]
  }), true);

  // ---- tabela-resumo: um grupo por linha, total no fim
  const th = t => '<th>' + esc(t) + '</th>';
  const cab = th(C.rotuloGrupo) + (temAnterior ? th(D.anterior) : '') + th(D.atual)
    + (temAnterior ? th('Δ%') : '') + (comTaxa ? th('Taxa ' + D.atual) : '');
  const linha = (l, classe) => '<tr' + (classe ? ' class="' + classe + '"' : '') + '><td>' + esc(l.nome) + '</td>'
    + (temAnterior ? '<td>' + fmt(l.ant, C.decimais) + '</td>' : '') + '<td>' + fmt(l.atu, C.decimais) + '</td>'
    + (temAnterior ? '<td>' + textoDelta(l.delta) + '</td>' : '') + (comTaxa ? '<td>' + fmt(l.taxa, 2) + '</td>' : '') + '</tr>';
  $('t-titulo').textContent = 'Resumo por ' + C.rotuloGrupo.toLowerCase() + ' · ' + periodo + (comTaxa ? ' · taxa ' + C.rotuloTaxa : '');
  $('tabela').innerHTML = '<thead><tr>' + cab + '</tr></thead><tbody>' + linhas.map(l => linha(l)).join('') + linha(tot, 'total') + '</tbody>';
}

function erro(msg) {
  $('titulo').textContent = 'Não foi possível carregar o painel';
  $('subtitulo').textContent = String(msg);
  $('grade').style.display = 'none';
}
</script>
</body>
</html>
```
