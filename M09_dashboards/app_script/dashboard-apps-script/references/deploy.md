# Publicar o painel

## Caminho A — pelo editor (sem instalar nada)

1. Abra https://script.google.com e clique em **Novo projeto**. Dê um nome.
2. Crie os arquivos com estes nomes **exatos**:
   - `Code.gs`, que já existe: cole o conteúdo;
   - `+` → **HTML** → `Index`, `Estilos`, `App` e `Icone` (o editor acrescenta o `.html`).
3. Para ver o `appsscript.json`, ligue **Configurações do projeto → Mostrar arquivo de
   manifesto "appsscript.json" no editor**, e cole o conteúdo.
4. No topo, escolha a função `criarTabelaConferencia` e clique em **Executar**. O Google
   pede autorização uma vez. Aceite. Isso cria a aba de conferência na planilha.
5. **Implantar → Nova implantação → engrenagem → App da Web**:
   - Executar como: **Eu**
   - Quem pode acessar: **Qualquer pessoa** (ou o que foi combinado)
6. Copie o link `.../exec`. É ele que você compartilha.

Mudou o código? Faça **Implantar → Gerenciar implantações → editar → Nova versão**,
senão o link continua servindo a versão antiga. Para testar sem publicar, use o link
`.../dev` (**Implantar → Testar implantações**).

## Caminho B — pelo terminal com `clasp`

```bash
npm install -g @google/clasp
clasp login                       # abre o navegador
# ative a API uma vez: https://script.google.com/home/usersettings
mkdir painel && cd painel          # com os 5 arquivos do template dentro
clasp create --type standalone --title "Meu painel" --parentId <ID_DA_PASTA_NO_DRIVE>
# o create pode trocar o appsscript.json pelo padrão: restaure o do template
clasp push -f
clasp deploy --description "v1"   # imprime o id da implantação
```

O link público é `https://script.google.com/macros/s/<ID_DA_IMPLANTACAO>/exec`. Depois de
mudar o código: `clasp push -f && clasp deploy -i <ID_DA_IMPLANTACAO> -d "v2"`. Assim o
link continua o mesmo.

**Antes do primeiro acesso de visitantes**, o dono precisa autorizar os escopos rodando
uma função no editor (passo 4 do caminho A).

## Permissões (`appsscript.json`)

```json
"oauthScopes": [
  "https://www.googleapis.com/auth/spreadsheets",
  "https://www.googleapis.com/auth/drive.readonly"
],
"webapp": { "executeAs": "USER_DEPLOYING", "access": "ANYONE_ANONYMOUS" }
```

- `executeAs: USER_DEPLOYING`: o painel lê a planilha com a conta do dono. Visitantes
  não precisam de acesso à planilha.
- Remova o escopo `drive.readonly` se não usar GeoJSON do Drive.
- Se usar `geojson.url`, o navegador busca a URL. Ela precisa permitir CORS (o jsDelivr
  e o raw do GitHub permitem).
