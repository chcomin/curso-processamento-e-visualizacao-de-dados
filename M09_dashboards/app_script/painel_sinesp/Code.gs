/**
 * Painel de uma página em Google Apps Script (servidor).
 *
 * Fluxo: a planilha (formato longo: uma linha por período x área x métrica) é
 * lida uma vez, agregada aqui no servidor e guardada no CacheService por
 * métrica. O navegador (App.html) só recebe os números prontos.
 *
 * Para adaptar a outra base, mude só o CONFIG e, se a planilha não estiver
 * no formato longo, a função linhas_().
 */

// ============================================================== CONFIG ===
const CONFIG = {
  planilhaId: '1I3bmr8fdEFjqUF-r5kv1-B4SaFrJFvJAoFLqbCiU07Q',   // "SINESP VDE 2025-2026 — UF mensal"
  aba: 'dados',

  titulo: 'Segurança pública no Brasil',
  ferramenta: 'Google Apps Script',
  caminho: ['Painéis', 'Segurança pública'],

  colunas: {
    ano: 'ano', mes: 'mes', data: '',
    metrica: 'indicador', grupo: 'categoria', unidade: 'unidade',
    geo: 'uf', geoNome: 'uf_nome',
    valor: 'valor', denominador: 'populacao'
  },
  metricaUnica: 'Total',

  taxaPor: 100000,
  rotuloTaxa: 'taxa por 100 mil hab.',

  kpis: ['Homicídio doloso', 'Latrocínio', 'Feminicídio', 'Estupro'],
  padrao: 'Homicídio doloso',
  menu: [
    { grupo: 'Crimes contra a vida', itens: ['Homicídio doloso', 'Latrocínio', 'Lesão corporal seguida de morte', 'Morte por intervenção de agente do Estado', 'Tentativa de homicídio'] },
    { grupo: 'Violência contra a mulher e sexual', itens: ['Feminicídio', 'Tentativa de feminicídio', 'Estupro', 'Estupro de vulnerável'] },
    { grupo: 'Patrimônio', itens: ['Roubo de veículo', 'Furto de veículo', 'Roubo de carga'] },
    { grupo: 'Drogas e armas', itens: ['Tráfico de drogas', 'Armas de fogo apreendidas'] },
    { grupo: 'Trânsito', itens: ['Mortes no trânsito'] }
  ],

  // mais apreensões podem significar mais polícia, não mais crime
  polaridade: { padrao: 'menor_melhor', excecoes: { 'Tráfico de drogas': 'neutro', 'Armas de fogo apreendidas': 'neutro' } },

  geojson: { driveId: '1k0iN63nMqaQmLOrHso3NosVKzyU_-3pW', url: '', propriedade: 'uf' },   // br_uf.geojson

  perguntas: {
    mapa: 'Onde o risco é maior?',
    pareado: 'Quais estados melhoraram ou pioraram?',
    tendencia: 'A mudança é de um mês ou do ano todo?'
  },

  notas: [
    { titulo: 'Fonte', texto: 'SINESP VDE / Ministério da Justiça e Segurança Pública, bases 2025 e 2026 (extraídas em 11/11/2026). População: estimativas do IBGE para 2025 e 2026.' },
    { titulo: 'Período comparável', texto: 'jan–set. A base de 2026 vai até setembro.' },
    { titulo: 'Dados preliminares', texto: 'Os estados ainda podem revisar os números.' },
    { titulo: 'Atenção a MS', texto: 'A série de homicídios muda de patamar entre 2025 e 2026. Compare com cautela.' },
    { titulo: 'Como ler a taxa', texto: 'Ocorrências (ou vítimas) no período ÷ população × 100 mil. Não é anualizada.' }
  ],

  versaoCache: 2   // v2: séries mensais (filtro temporal)
};
// =========================================================================

const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
const TTL_CACHE = 6 * 60 * 60;   // 6 horas (máximo do CacheService)

/** Entrada do web app. */
function doGet() {
  const t = HtmlService.createTemplateFromFile('Index');
  t.titulo = CONFIG.titulo;
  t.ferramenta = CONFIG.ferramenta;
  t.geojsonInline = geojsonDoDrive_();   // embutido na página: evita o limite de 100 KB do cache
  return t.evaluate()
    .setTitle(CONFIG.titulo + ' · ' + CONFIG.ferramenta)
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/** Permite <?!= incluir('Estilos') ?> no Index.html. */
function incluir(nome) {
  return HtmlService.createHtmlOutputFromFile(nome).getContent();
}

// ------------------------------------------------------------- leitura ---

function planilha_() {
  return SpreadsheetApp.openById(CONFIG.planilhaId);
}

/**
 * Lê a planilha e devolve linhas normalizadas:
 * {ano, mes, metrica, grupo, unidade, geo, geoNome, valor, denominador}.
 * Se a sua planilha for "larga" (uma coluna por métrica), transforme-a aqui
 * em uma linha por métrica.
 */
function linhas_() {
  const ss = planilha_();
  const aba = ss.getSheetByName(CONFIG.aba) || ss.getSheets()[0];
  const valores = aba.getDataRange().getValues();
  const cab = valores.shift().map(String);
  const c = CONFIG.colunas;
  const col = nome => {
    if (!nome) return -1;
    const k = cab.indexOf(nome);
    if (k < 0) throw new Error('Coluna "' + nome + '" não encontrada. Cabeçalho: ' + cab.join(', '));
    return k;
  };
  const ix = {
    ano: col(c.ano), mes: col(c.mes), data: col(c.data), metrica: col(c.metrica),
    grupo: col(c.grupo), unidade: col(c.unidade), geo: col(c.geo), geoNome: col(c.geoNome),
    valor: col(c.valor), denominador: col(c.denominador)
  };
  const num = paraNumero_;
  return valores.map(r => {
    let ano = ix.ano >= 0 ? Number(r[ix.ano]) : null;
    let mes = ix.mes >= 0 ? Number(r[ix.mes]) : null;
    if ((ano === null || mes === null) && ix.data >= 0) {
      const d = new Date(r[ix.data]);
      ano = d.getFullYear(); mes = d.getMonth() + 1;
    }
    return {
      ano: ano, mes: mes,
      metrica: ix.metrica >= 0 ? String(r[ix.metrica]) : CONFIG.metricaUnica,
      grupo: ix.grupo >= 0 ? String(r[ix.grupo]) : '',
      unidade: ix.unidade >= 0 ? String(r[ix.unidade]) : '',
      geo: ix.geo >= 0 ? String(r[ix.geo]) : '',
      geoNome: ix.geoNome >= 0 ? String(r[ix.geoNome]) : (ix.geo >= 0 ? String(r[ix.geo]) : ''),
      valor: ix.valor >= 0 ? num(r[ix.valor]) : 1,
      denominador: ix.denominador >= 0 ? num(r[ix.denominador]) : null
    };
  }).filter(l => l.ano && l.mes);
}

/** Número de uma célula: aceita 1234.5, "1.234,5", "R$ 10", "12%"; o resto vira null. */
function paraNumero_(v) {
  if (v === '' || v === null || v === undefined) return null;
  if (typeof v === 'number') return isNaN(v) ? null : v;
  let s = String(v).replace(/[^\d,.\-]/g, '');
  if (s.indexOf(',') >= 0) s = s.replace(/\./g, '').replace(',', '.');   // formato brasileiro
  const n = Number(s);
  return s === '' || isNaN(n) ? null : n;
}

function geojsonDoDrive_() {
  if (!CONFIG.geojson.driveId) return 'null';
  return DriveApp.getFileById(CONFIG.geojson.driveId).getBlob().getDataAsString();
}

// ------------------------------------------------------------ agregação ---

/** Ano atual, ano anterior e último mês com dado no ano atual (período comparável). */
function periodo_(linhas) {
  const anoAtual = Math.max.apply(null, linhas.map(l => l.ano));
  const doAtual = linhas.filter(l => l.ano === anoAtual && l.valor !== null);
  if (!doAtual.length) throw new Error('Nenhuma linha com valor numérico no ano ' + anoAtual + '. Confira colunas.valor e colunas.ano.');
  const ultimoMes = Math.max.apply(null, doAtual.map(l => l.mes));
  return {
    anoAtual: anoAtual, anoAnterior: anoAtual - 1, ultimoMes: ultimoMes,
    rotulo: (ultimoMes === 12 ? 'jan–dez' : 'jan–' + MESES[ultimoMes - 1])
  };
}

function polaridade_(metrica) {
  return CONFIG.polaridade.excecoes[metrica] || CONFIG.polaridade.padrao;
}

function variacao_(antes, depois) {
  return antes ? (depois / antes - 1) * 100 : null;
}

/**
 * Séries MENSAIS de UMA métrica: no Brasil e por área, nos dois anos.
 * O navegador soma os meses do intervalo escolhido no filtro temporal,
 * então o filtro não precisa chamar o servidor de novo.
 */
function resumo_(linhas, metrica, p) {
  const ls = linhas.filter(l => l.metrica === metrica);
  const vazia = () => MESES.map(() => null);
  const somar = (serie, mes, v) => { serie[mes - 1] = (serie[mes - 1] || 0) + v; };
  const qual = ano => (ano === p.anoAtual ? 'atual' : ano === p.anoAnterior ? 'anterior' : null);

  const serie = { anterior: vazia(), atual: vazia() };
  const areas = {};
  ls.forEach(l => {
    const k = qual(l.ano);
    if (!k) return;
    let a = null;
    if (l.geo) {
      a = areas[l.geo] || (areas[l.geo] = {
        geo: l.geo, nome: l.geoNome, anterior: vazia(), atual: vazia(), denAnterior: null, denAtual: null
      });
      // denominador: um valor por área e ano (ex.: população)
      if (l.denominador !== null) a[k === 'atual' ? 'denAtual' : 'denAnterior'] = l.denominador;
    }
    if (l.valor === null) return;
    somar(serie[k], l.mes, l.valor);
    if (a) somar(a[k], l.mes, l.valor);
  });
  // o ano atual termina no último mês com dado: nada de zeros no futuro
  serie.atual = serie.atual.map((v, i) => (i < p.ultimoMes ? v : null));

  const primeira = ls[0] || {};
  return {
    metrica: metrica, unidade: primeira.unidade || '', grupo: primeira.grupo || '',
    polaridade: polaridade_(metrica),
    serie: serie,
    porGeo: Object.keys(areas).map(k => areas[k])
  };
}

function menu_(linhas) {
  if (CONFIG.menu.length) return CONFIG.menu;
  const grupos = {};
  linhas.forEach(l => {
    const g = grupos[l.grupo] || (grupos[l.grupo] = []);
    if (g.indexOf(l.metrica) < 0) g.push(l.metrica);
  });
  return Object.keys(grupos).map(g => ({ grupo: g, itens: grupos[g] }));
}

/** Lê a planilha uma vez, calcula tudo e guarda no cache (um item por métrica). */
function montarTudo_() {
  const linhas = linhas_();
  const p = periodo_(linhas);
  const menu = menu_(linhas);
  const metricas = [];
  menu.forEach(g => g.itens.forEach(m => metricas.push(m)));
  CONFIG.kpis.forEach(m => { if (metricas.indexOf(m) < 0) metricas.push(m); });
  const existentes = {};
  linhas.forEach(l => { existentes[l.metrica] = true; });
  const faltando = metricas.filter(m => !existentes[m]);
  if (faltando.length) throw new Error('Métricas do CONFIG que não existem na planilha: ' + faltando.join(', '));

  const itens = {};
  metricas.forEach(m => { itens[chave_(m)] = JSON.stringify(Object.assign(resumo_(linhas, m, p), { periodo: p })); });
  const inicio = {
    titulo: CONFIG.titulo, caminho: CONFIG.caminho, ferramenta: CONFIG.ferramenta, periodo: p, menu: menu,
    padrao: CONFIG.padrao || metricas[0], perguntas: CONFIG.perguntas, notas: CONFIG.notas,
    rotuloTaxa: CONFIG.rotuloTaxa, taxaPor: CONFIG.taxaPor, temGeo: Boolean(CONFIG.colunas.geo),
    temTaxa: Boolean(CONFIG.colunas.denominador), urlGeojson: CONFIG.geojson.url,
    propriedadeGeo: CONFIG.geojson.propriedade,
    formato: Object.assign({ decimais: 0, prefixo: '', sufixo: '' }, CONFIG.formato || {}),
    kpis: CONFIG.kpis.map(m => {
      const r = JSON.parse(itens[chave_(m)]);
      return { metrica: m, unidade: r.unidade, polaridade: r.polaridade, serie: r.serie };
    })
  };
  itens[chave_('__inicio__')] = JSON.stringify(inicio);
  // o CacheService guarda até 100 KB por item: o que passar disso é recalculado a cada visita
  // (com muitas áreas, ex.: municípios, agregue antes ou mostre só UFs)
  const cabem = {};
  Object.keys(itens).forEach(k => { if (itens[k].length < 95000) cabem[k] = itens[k]; });
  CacheService.getScriptCache().putAll(cabem, TTL_CACHE);
  return itens;
}

function chave_(m) {
  const hash = Utilities.computeDigest(Utilities.DigestAlgorithm.MD5, m, Utilities.Charset.UTF_8);
  return 'v' + CONFIG.versaoCache + ':' + Utilities.base64EncodeWebSafe(hash);
}

function doCache_(m) {
  const k = chave_(m);
  const achado = CacheService.getScriptCache().get(k);
  if (achado) return JSON.parse(achado);
  const itens = montarTudo_();
  if (!itens[k]) throw new Error('Métrica desconhecida: ' + m);
  return JSON.parse(itens[k]);
}

// ------------------------------------------------- chamadas do navegador ---

/** Menu, KPIs fixos, notas e período. */
function getInicio() {
  return doCache_('__inicio__');
}

/** Mapa, pareado e tendência de uma métrica. */
function getPainel(metrica) {
  return doCache_(metrica);
}

// ------------------------------------------------------------ utilidades ---

/** Rode no editor depois de mudar a planilha ou o CONFIG. */
function limparCache() {
  CacheService.getScriptCache().removeAll([chave_('__inicio__')]);
  montarTudo_();
}

/**
 * Cria a aba "conferencia" com uma tabela dinâmica nativa do Sheets:
 * soma de valor por métrica (linhas) e ano (colunas), só nos meses do
 * período comparável. Os KPIs do painel precisam bater com ela.
 */
function criarTabelaConferencia() {
  const ss = planilha_();
  const c = CONFIG.colunas;
  const p = periodo_(linhas_());
  const antiga = ss.getSheetByName('conferencia');
  if (antiga) ss.deleteSheet(antiga);
  const aba = ss.insertSheet('conferencia');
  aba.getRange('A1').setValue(
    'Conferência: soma do valor por métrica e ano, meses 1 a ' + p.ultimoMes + ' (' + p.rotulo +
    '). Os KPIs do painel precisam mostrar estes mesmos números.'
  );

  let origem, colMetrica, colAno, colMes, colValor;
  if (c.ano && c.mes && c.valor) {
    // Caso comum: a tabela dinâmica lê a planilha ORIGINAL, sem passar pelo código do painel.
    // Assim ela confere o painel de forma independente.
    const dados = ss.getSheetByName(CONFIG.aba) || ss.getSheets()[0];
    const cab = dados.getRange(1, 1, 1, dados.getLastColumn()).getValues()[0].map(String);
    const col = nome => cab.indexOf(nome) + 1;
    origem = dados.getDataRange();
    colMetrica = c.metrica ? col(c.metrica) : 0;
    colAno = col(c.ano); colMes = col(c.mes); colValor = col(c.valor);
  } else {
    // Planilha com coluna de data (ou contagem de linhas): monta uma aba auxiliar com ano e mês.
    const linhas = linhas_();
    const base = [['ano', 'mes', 'metrica', 'valor']].concat(linhas.map(l => [l.ano, l.mes, l.metrica, l.valor]));
    const antigaBase = ss.getSheetByName('_conferencia_base');
    if (antigaBase) ss.deleteSheet(antigaBase);
    const aux = ss.insertSheet('_conferencia_base');
    aux.getRange(1, 1, base.length, 4).setValues(base);
    aux.hideSheet();
    origem = aux.getRange(1, 1, base.length, 4);
    colAno = 1; colMes = 2; colMetrica = 3; colValor = 4;
  }

  const tabela = aba.getRange('A3').createPivotTable(origem);
  if (colMetrica) tabela.addRowGroup(colMetrica);
  tabela.addColumnGroup(colAno);
  tabela.addPivotValue(colValor, SpreadsheetApp.PivotTableSummarizeFunction.SUM);
  tabela.addFilter(colMes, SpreadsheetApp.newFilterCriteria().whenNumberLessThanOrEqualTo(p.ultimoMes).build());
  return 'Aba "conferencia" criada em ' + ss.getUrl();
}
