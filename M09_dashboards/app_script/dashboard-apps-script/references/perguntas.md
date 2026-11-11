# Questionário de especificação

Faça as perguntas em no máximo **duas rodadas**. Em cada uma, mostre o **padrão
proposto** que você inferiu da planilha, entre colchetes, para o usuário só confirmar.

## Rodada 1 — o problema

1. **Dados**: qual planilha (link) e qual aba? [a aba com mais linhas]
2. **Público**: quem vai olhar o painel e com que frequência? [equipe, semanalmente]
3. **Perguntas de negócio**: quais 1 a 3 perguntas o painel precisa responder? Dê exemplos
   no formato "X subiu ou caiu?", "Onde X é maior?", "Quem melhorou?", "Quando mudou?".
   [proponha 3 a partir das colunas]
4. **Métricas**: quais colunas são a medida principal? O painel **soma** (ou conta linhas).
   Média e percentual precisam virar algo somável (veja o SKILL.md, etapa 1).
   [soma da coluna numérica principal]
5. **Polaridade**: para cada métrica, subir é **bom**, **ruim** ou **neutro**? Isso decide
   a cor do Δ: verde para a mudança desejável, vermelho para a indesejável.
   [ruim para crime, custo, atraso; bom para venda, nota, conversão]

## Rodada 2 — o recorte e a forma

6. **Comparação**: comparar com o quê? [mesmo período do ano anterior; se o ano atual está
   incompleto, os mesmos meses]
7. **Geografia**: há uma coluna de área (UF, município, país, loja)? Ela entra num mapa?
   Há um GeoJSON com essa chave? [UF → malha do IBGE]
8. **Denominador**: comparar áreas por **taxa** (por 100 mil hab., por cliente)? Qual
   coluna é o denominador? [população, se existir]
9. **KPIs fixos**: até 4 números no topo, que não mudam com o seletor. [as 4 métricas
   mais importantes das perguntas]
10. **Seletor**: o menu lateral escolhe a **métrica**, e os grupos dele vêm de uma coluna de
    categoria. [a coluna de métrica, agrupada pela coluna de categoria] Filtros por região,
    loja etc. não vêm prontos no template. Se o usuário pedir, registre no `ESPEC.md` e
    adapte `linhas_()` e o `App.html`.
11. **Visual**: título, idioma, tema (claro, escuro ou os dois) e cor de destaque. [título
    a partir das perguntas, pt-BR, claro com botão de escuro, SnowUI]
12. **Notas**: fonte dos dados, data de extração e ressalvas que precisam aparecer.
13. **Acesso**: quem pode abrir? Qualquer pessoa com o link, só a sua organização ou só
    você? [qualquer pessoa com o link, se os dados forem públicos]

## Como transformar respostas em visuais

| Tipo de pergunta | Visual | Cartão do template |
|---|---|---|
| "X subiu ou caiu?" | número grande + Δ% com seta e cor de polaridade | KPI |
| "Onde X é maior?" | mapa coroplético da **taxa** + ranking top 5 | mapa |
| "Quem melhorou ou piorou?" | pareado (dumbbell) anterior → atual, ordenado | pareado |
| "Quando mudou?" | linha mensal: atual sólida, anterior tracejada | tendência |
| "Qual a composição?" | barras horizontais ordenadas, não pizza | adapte o pareado |

Se o usuário quiser algo que nenhum cartão cobre, proponha a forma mais simples que
responda a pergunta e registre isso no `ESPEC.md`.
