/* Ajuda "?" (fecha com Esc e clique fora) e barras laterais recolhíveis. */
(function () {
  function fecharAjudas(exceto) {
    document.querySelectorAll("details.ajuda[open]").forEach(function (d) {
      if (d !== exceto) d.removeAttribute("open");
    });
  }
  function raiz() { return document.getElementById("dashboard-root"); }
  function estreito() { return window.innerWidth < 1024; }
  function aberta(alvo) {
    var r = raiz();
    if (!r) return true;
    return alvo === "left"
      ? (estreito() ? r.classList.contains("left-open") : !r.classList.contains("left-closed"))
      : !r.classList.contains("right-closed");
  }
  function sincronizar() {
    document.querySelectorAll("[data-alvo]").forEach(function (b) {
      b.setAttribute("aria-expanded", aberta(b.getAttribute("data-alvo")) ? "true" : "false");
    });
  }
  function redimensionar() {
    [60, 320].forEach(function (t) {
      setTimeout(function () { window.dispatchEvent(new Event("resize")); }, t);
    });
  }
  function alternar(alvo) {
    var r = raiz();
    if (!r) return;
    if (alvo === "left") r.classList.toggle(estreito() ? "left-open" : "left-closed");
    else r.classList.toggle("right-closed");
    sincronizar();
    redimensionar();
  }
  document.addEventListener("click", function (e) {
    var btn = e.target.closest && e.target.closest("[data-alvo]");
    if (btn) { alternar(btn.getAttribute("data-alvo")); return; }
    var det = e.target.closest && e.target.closest("details.ajuda");
    fecharAjudas(det);
    // clique no balão não fecha; clique no "?" alterna nativamente
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      fecharAjudas(null);
      var r = raiz();
      if (r && r.classList.contains("left-open")) alternar("left");
    }
  });
  window.addEventListener("resize", sincronizar);
  new MutationObserver(function () { sincronizar(); }).observe(document.documentElement, { childList: true, subtree: true });
  document.addEventListener("DOMContentLoaded", sincronizar);
})();
