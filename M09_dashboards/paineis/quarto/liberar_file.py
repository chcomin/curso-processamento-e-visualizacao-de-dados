"""Pos-render: o Quarto bloqueia OJS em file://. Aqui liberamos, para o painel
abrir com duplo clique (os dados ja vao embutidos no HTML; so as bibliotecas
Plot/d3 vem da CDN, entao e preciso internet)."""
from pathlib import Path

p = Path(__file__).parent / "painel.html"
s = p.read_text(encoding="utf-8")
s = s.replace('if (window.location.protocol === "file:") {\n    displayFileProtocolError();\n    return;\n  }', '')
s = s.replace('if (window.location.protocol === "file:") { alert("The OJS runtime does not work with file:// URLs. Please use a web server to view this document."); }', '')
p.write_text(s, encoding="utf-8")
print("painel.html liberado para file://")

# Emagrecimento (o painel e aberto no celular): o Quarto embute o CSS do
# Bootstrap 3 vezes (claro, alternativo, extra) e a fonte de icones (nao usada).
import re
s = p.read_text(encoding="utf-8")
antes = len(s)
links = re.findall(r'<link[^>]*id="quarto-bootstrap"[^>]*>', s)
for extra in links[1:]:
    s = s.replace(extra, "", 1)
s = re.sub(r'<style type="text/css">\s*@font-face \{ font-display: block; font-family: "bootstrap-icons".*?</style>', "", s, count=1, flags=re.S)
p.write_text(s, encoding="utf-8")
print(f"emagrecido: {antes/1e6:.1f} MB -> {len(s.encode())/1e6:.1f} MB")
