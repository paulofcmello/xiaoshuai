// busca: ícone de lupa no menu abre um painel que filtra o catálogo enquanto a pessoa digita
(() => {
  const lg = () => { try { return localStorage.lang || "pt" } catch { return "pt" } };
  const T = (pt, cn, en) => { const l = lg(); return l == "zh" ? cn : l == "en" ? (en ?? pt) : pt };
  const norm = s => (s || "").normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const navr = document.querySelector("nav.top .navr");
  if (!navr) return;
  const STAR = ["Flamengo", "Palmeiras", "Corinthians", "Real Madrid", "Barcelona", "Manchester United", "Brasil", "Argentina"];
  const MAX = 40;
  let all = null, idx = null;

  const btn = document.createElement("button");
  btn.className = "ico lupa"; btn.type = "button";
  btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/></svg>';
  navr.prepend(btn);

  const el = document.createElement("div");
  el.className = "search"; el.hidden = true;
  el.innerHTML = `<div class="sshade" data-x></div><div class="spanel" role="dialog" aria-modal="true">
    <div class="sbar"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/></svg>
      <input type="search" id="sq" autocomplete="off" enterkeyhint="search"><button type="button" class="sclear" hidden></button>
      <button type="button" class="sclose" data-x><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg></button></div>
    <div class="sbody"></div></div>`;
  document.body.append(el);
  const q = el.querySelector("#sq"), body = el.querySelector(".sbody"), clear = el.querySelector(".sclear");

  const card = x => `<a class="sitem" href="camisa.html?id=${x.h}"><img src="fotos/all/${x.h}.webp" alt="" loading="lazy" width="440" height="440"><span>${T(x.t, x.tz, x.te)}</span>${SEM_PRECO ? "" : `<b>R$ ${x.p}</b>`}</a>`;

  function render() {
    if (!all) { body.innerHTML = `<p class="snote">${T("Carregando…", "加载中…", "Loading…")}</p>`; return }
    const words = norm(q.value).split(/\s+/).filter(Boolean);
    clear.hidden = !words.length;
    if (!words.length) {  // sem busca: sugestões, um time conhecido por vez
      const seen = new Set(), sug = STAR.map(n => all.find(x => x.n == n && !x.sh && !seen.has(n) && seen.add(n))).filter(Boolean).slice(0, 8);
      body.innerHTML = `<h3>${T("Produtos", "商品", "Products")}</h3><div class="sgrid">${sug.map(card).join("")}</div>`;
      return;
    }
    const hits = all.filter((x, i) => words.every(w => idx[i].includes(w)));
    body.innerHTML = hits.length
      ? `<h3>${T("Produtos", "商品", "Products")} <small>${hits.length}</small></h3><div class="sgrid">${hits.slice(0, MAX).map(card).join("")}</div>${hits.length > MAX ? `<p class="snote">${T(`Mostrando ${MAX} de ${hits.length}. Digite mais para refinar.`, `显示 ${hits.length} 个中的 ${MAX} 个，请输入更多关键词。`, `Showing ${MAX} of ${hits.length}. Type more to narrow it down.`)}</p>` : ""}`
      : `<p class="snote">${T(`Nada encontrado para "${q.value}".`, `未找到"${q.value}"。`, `Nothing found for "${q.value}".`)}</p>`;
  }

  function open() {
    q.placeholder = T("Pesquisa", "搜索", "Search");
    btn.setAttribute("aria-label", T("Pesquisar", "搜索", "Search"));
    clear.textContent = T("Limpar", "清除", "Clear");
    el.querySelector(".sclose").setAttribute("aria-label", T("Fechar", "关闭", "Close"));
    el.hidden = false; document.documentElement.style.overflow = "hidden";
    void el.offsetWidth; el.classList.add("on");  // reflow: a transição de entrada roda mesmo sem quadros de animação
    q.focus(); render();
    if (!all) Dados.busca().then(d => {  // [hash, time, título pt, en, zh, versão pt, en, preço, short]
      all = d.map(([h, n, t, te, tz, q, qe, p, sh]) => ({ h, n, t, te, tz, q, qe, p, sh }));
      idx = all.map(x => norm([x.t, x.te, x.tz, x.n, x.q, x.qe].join(" ")));
      render();
    });
  }
  function close() {
    el.classList.remove("on"); document.documentElement.style.overflow = "";
    setTimeout(() => { el.hidden = true }, 200); btn.focus();
  }

  btn.setAttribute("aria-label", T("Pesquisar", "搜索", "Search"));
  btn.addEventListener("click", open);
  q.addEventListener("input", render);
  clear.addEventListener("click", () => { q.value = ""; render(); q.focus() });
  el.addEventListener("click", e => { if (e.target.closest("[data-x]")) close() });
  addEventListener("keydown", e => { if (e.key == "Escape" && !el.hidden) close() });
})();
