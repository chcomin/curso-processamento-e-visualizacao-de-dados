# Skill `dashboard-apps-script`

Uma *skill* é uma pasta de instruções que um agente de IA de código (Claude Code,
Gemini CLI, Antigravity, Codex...) carrega quando a tarefa pede. Esta ensina o agente a
montar um **painel de uma página em Google Apps Script** a partir de uma planilha.

Ao ser chamada, a skill segue 6 etapas:

1. pergunta o que você quer responder com os dados;
2. confirma uma especificação curta;
3. gera o projeto a partir de um template que já funciona, com a UI no estilo SnowUI;
4. confere os números contra uma tabela dinâmica;
5. publica como web app;
6. entrega os links e a conferência.

```text
dashboard-apps-script/
├── SKILL.md                      instruções para o agente (o fluxo de 6 etapas)
├── references/
│   ├── perguntas.md              questionário de especificação
│   ├── ui-spec.md                design: tokens, layout, componentes, regras
│   ├── referencia_visual.png     o alvo visual
│   └── deploy.md                 publicação (editor ou clasp)
└── assets/templates/             Code.gs, Index.html, Estilos.html, App.html, Icone.html, appsscript.json
```

## Instalar

Copie (ou crie um link para) a pasta inteira no diretório de skills do seu agente.

| Agente | Para todos os projetos | Só neste projeto |
|---|---|---|
| **Claude Code** | `~/.claude/skills/dashboard-apps-script/` | `.claude/skills/dashboard-apps-script/` |
| **Gemini CLI** | `gemini skills install ./dashboard-apps-script` (ou `gemini skills link`) | `--scope workspace` |
| **Antigravity** | `~/.gemini/antigravity/skills/dashboard-apps-script/` | `.agents/skills/dashboard-apps-script/` |
| **Codex** | `~/.codex/skills/dashboard-apps-script/` | `.agents/skills/dashboard-apps-script/` |

No macOS ou Linux:

```bash
# Claude Code
mkdir -p ~/.claude/skills && cp -r dashboard-apps-script ~/.claude/skills/
# Gemini CLI
gemini skills install ./dashboard-apps-script
# Antigravity
mkdir -p ~/.gemini/antigravity/skills && cp -r dashboard-apps-script ~/.gemini/antigravity/skills/
```

No Windows (PowerShell), copie a pasta para `$HOME\.claude\skills\`, ou o equivalente
do seu agente.

**Sem agente instalado?** Num chat (Claude, Gemini, ChatGPT), anexe o `SKILL.md`, os
arquivos de `references/` e os de `assets/templates/` e escreva: "Siga o SKILL.md para
montar meu painel".

## Usar

Abra o agente numa pasta vazia e peça, por exemplo:

> Quero um dashboard no Apps Script com os dados desta planilha: <link>.
> Ele precisa responder se os homicídios caíram em 2026 e onde o risco é maior.

O agente vai ler a planilha (ou pedir que você cole o cabeçalho), fazer as perguntas
de `references/perguntas.md` e mostrar um `ESPEC.md` antes de escrever qualquer código.

## Exemplo pronto

`../painel_sinesp/` é esta skill aplicada aos dados de segurança pública (SINESP
2025–2026, por UF). Compare o `CONFIG` de `painel_sinesp/Code.gs` com o do template:
foi a única coisa que mudou.

---

O visual é baseado no *SnowUI Dashboard Design System* (ByeWind, Figma Community), e os
gráficos usam Apache ECharts.
