# M09 · Dashboards: o mesmo painel em 4 ferramentas

Slides da aula: [1_dashboards.html](https://chcomin.github.io/curso-processamento-e-visualizacao-de-dados/M09_dashboards/1_dashboards.html)

O painel responde a uma pergunta: **a violência caiu no Brasil em 2026?** Ele usa os
dados do SINESP (Ministério da Justiça e Segurança Pública) de 2025 e 2026, por UF.
O mesmo painel de uma página foi feito em quatro ferramentas gratuitas, para comparar
como cada uma funciona.

| Ferramenta | Painel publicado | Código | Como funciona |
|---|---|---|---|
| **Quarto Dashboard** | [abrir](https://chcomin.github.io/curso-processamento-e-visualizacao-de-dados/M09_dashboards/paineis/quarto/painel.html) | [`paineis/quarto/`](paineis/quarto/) | declarativo (Markdown + Python + Observable JS); vira um HTML estático |
| **Dash (Plotly)** | [abrir](https://pvd-sinesp-dash.onrender.com) | [`paineis/dash/`](paineis/dash/) | app Python com *callbacks*; precisa de servidor |
| **Streamlit** | [abrir](https://pvd-sinesp-streamlit.onrender.com) | [`paineis/streamlit/`](paineis/streamlit/) | script Python que roda de novo a cada clique; precisa de servidor |
| **Google Apps Script** | [abrir](https://script.google.com/macros/s/AKfycbzveUVAHfTnYVZ4SKn-_aNEEPKepW6r3ztBLYDpJYuczfJ3FbS5ugmicIJs2Qw5B2YVFg/exec) | [`app_script/painel_sinesp/`](app_script/painel_sinesp/) | HTML/JS servido pelo Google, lendo uma planilha |

Os painéis no Render "dormem" quando ninguém acessa. O primeiro acesso pode levar cerca
de 1 minuto.

## As perguntas do painel

1. **A violência caiu em 2026?** 4 números com a variação jan–set 2026 × jan–set 2025.
2. **Onde o risco é maior?** Mapa da taxa por 100 mil habitantes, por UF.
3. **Quais estados melhoraram ou pioraram?** A taxa de 2025 e a de 2026, lado a lado.
4. **A mudança é de um mês ou do ano todo?** A série mensal dos dois anos.

O menu lateral troca o indicador (homicídio, latrocínio, feminicídio, estupro, roubo de
veículo...).

## Os dados

`montar_dataset.py` baixa as bases do SINESP VDE e a população e a malha das UFs do IBGE,
e grava em `dados/`:

- `sinesp_uf_mensal.csv`: UF × mês × indicador, com a população da UF;
- `br_uf.geojson`: o contorno das 27 UFs;
- `conferencia.csv`: os totais que todo painel precisa reproduzir.

```bash
pip install pandas openpyxl pyarrow
python montar_dataset.py
```

Os dados de 2026 vão até setembro, por isso as comparações são sempre **jan–set ×
jan–set**. Os dados são preliminares e os estados podem revisá-los.

## Rodar no seu computador

```bash
# Quarto (precisa do Quarto instalado: https://quarto.org)
cd paineis/quarto && quarto render painel.qmd    # abre painel.html no navegador

# Dash
cd paineis/dash && pip install -r requirements.txt && python app.py          # http://localhost:8050

# Streamlit
cd paineis/streamlit && pip install -r requirements.txt && streamlit run app.py
```

## Criar o seu painel em Apps Script com IA

A pasta [`app_script/dashboard-apps-script/`](app_script/dashboard-apps-script/) é uma **skill**: um conjunto de
instruções que um agente de IA de código (Claude Code, Gemini CLI, Antigravity, Codex)
segue para montar um painel em Apps Script a partir de **qualquer** planilha. Ela
pergunta o que você quer responder, mostra uma especificação, gera o código, confere os
números com uma tabela dinâmica e publica. Para instalar e usar, leia o
[README da skill](app_script/dashboard-apps-script/README.md).

`app_script/painel_sinesp/` é a skill aplicada a estes dados.

---

Fontes: SINESP VDE / MJSP (bases 2025 e 2026, extraídas em 11/11/2026); IBGE (estimativas
de população e malha territorial). O visual segue o *SnowUI Dashboard Design System*
(ByeWind, Figma Community).

Material da disciplina Processamento e Visualização de Dados (UFSCar), do Prof. Cesar
Henrique Comin e de Wesley Galvão.
