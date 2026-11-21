// gaveta do carrinho: o ícone do menu abre o carrinho na lateral em vez de trocar de página
(() => {
  const lg = () => { try { return localStorage.lang || "pt" } catch { return "pt" } };
  const T = (pt, cn, en) => { const l = lg(); return l == "zh" ? cn : l == "en" ? (en ?? pt) : pt };
  const read = () => { try { return JSON.parse(localStorage.cart || "[]") } catch { return [] } };
  const save = c => { try { localStorage.cart = JSON.stringify(c) } catch {} };
  const brl = v => "R$ " + v.toLocaleString("pt-BR", { minimumFractionDigits: 2 });
  const icon = document.querySelector('nav.top a[href="carrinho.html"]');
  if (!icon) return;
  let byH = null;

  const el = document.createElement("div");
  el.className = "drawer"; el.hidden = true;
  el.innerHTML = `<div class="dshade" data-x></div><aside role="dialog" aria-modal="true" aria-labelledby="dtitle">
    <header><h2 id="dtitle"></h2><button class="dclose" data-x><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg></button></header>
    <div class="dbody"></div></aside>`;
  document.body.append(el);
  const body = el.querySelector(".dbody");

  // camisa + tamanho + nome/número iguais viram uma linha com quantidade
  const PERS = {{PRECO_PERS}};
  const keyOf = c => encodeURIComponent(JSON.stringify([c.h, c.size, c.nome || "", c.num || ""]));
  const pers = c => !!(c.nome || c.num), preco = c => byH[c.h].p + (pers(c) ? PERS : 0);
  const persTxt = c => [c.nome && T("Nome", "名字", "Name") + " " + c.nome, c.num && T("Nº", "号码", "No.") + " " + c.num].filter(Boolean).join(" · ");
  const lines = cart => { const m = new Map(); cart.forEach(c => { const k = keyOf(c); m.set(k, { ...c, k, q: (m.get(k)?.q || 0) + 1 }) }); return [...m.values()] };

  function render() {
    let cart = read();
    if (byH) { cart = cart.filter(c => byH[c.h]); save(cart) }
    document.getElementById("count").textContent = cart.length;
    el.querySelector("#dtitle").innerHTML = `${T("Carrinho", "购物车", "Cart")} <span>${cart.length}</span>`;
    el.querySelector(".dclose").setAttribute("aria-label", T("Fechar", "关闭", "Close"));
    if (!byH) { body.innerHTML = `<p class="dempty">${T("Carregando…", "加载中…", "Loading…")}</p>`; return }
    if (!cart.length) {
      body.innerHTML = `<div class="dempty"><p>${T("Seu carrinho está vazio.", "购物车是空的。", "Your cart is empty.")}</p><a class="btn" href="index.html#loja" data-x>${T("Ver catálogo", "查看目录", "Browse catalog")}</a></div>`;
      return;
    }
    const sub = cart.reduce((s, c) => s + preco(c), 0);
    body.innerHTML = `<div class="dlist">${lines(cart).map(l => { const x = byH[l.h], k = l.k; return `
      <div class="dline">
        <a href="camisa.html?id=${x.h}"><img src="fotos/all/${x.h}.webp" alt="" width="72" height="72"></a>
        <div><h3><a href="camisa.html?id=${x.h}">${T(x.t, x.tz, x.te)}</a></h3>
          <p>${[T(x.q, x.qz, x.qe), l.size].filter(Boolean).join(" · ")}</p>${pers(l) ? `<p class="perstag">${persTxt(l)}</p>` : ""}
          <p class="pr">${brl(preco(l))}</p>
          <div class="dact"><div class="dqty"><button data-a="-" data-k="${k}" aria-label="${T("Diminuir", "减少", "Decrease")}">−</button><output>${l.q}</output><button data-a="+" data-k="${k}" aria-label="${T("Aumentar", "增加", "Increase")}">+</button></div>
          <button class="dtrash" data-a="x" data-k="${k}" aria-label="${T("Remover", "删除", "Remove")}"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/></svg></button></div>
        </div>
        <b class="dsum">${brl(preco(l) * l.q)}</b>
      </div>` }).join("")}</div>
      <div class="dfoot">
        <div class="dtot"><span>${T("Total estimado", "预计合计", "Estimated total")}</span><b>${brl(sub)}</b></div>
        <p>${T("Frete calculado na próxima etapa.", "运费在下一步计算。", "Shipping is calculated in the next step.")}</p>
        <a class="btn" href="carrinho.html">${T("Finalizar compra", "去结算", "Checkout")}</a>
      </div>`;
  }

  function open() {
    el.hidden = false; render();
    void el.offsetWidth; el.classList.add("on");  // reflow: a transição de entrada roda mesmo sem quadros de animação
    document.documentElement.style.overflow = "hidden";
    el.querySelector(".dclose").focus();
    if (!byH) fetch("catalog.json").then(r => r.json()).then(all => { byH = {}; all.forEach(x => byH[x.h] = x); render() });
  }
  function close() {
    el.classList.remove("on"); document.documentElement.style.overflow = "";
    setTimeout(() => { el.hidden = true }, 300); icon.focus();
  }

  el.addEventListener("click", e => {
    if (e.target.closest("[data-x]")) return close();
    const b = e.target.closest("button[data-a]"); if (!b) return;
    const k = b.dataset.k; let cart = read(); const i = cart.findIndex(c => keyOf(c) == k);
    if (b.dataset.a == "+" && i > -1) cart.push({ ...cart[i] });
    else if (b.dataset.a == "-" && i > -1) cart.splice(i, 1);
    else if (b.dataset.a == "x") cart = cart.filter(c => keyOf(c) != k);
    save(cart); render();
  });
  addEventListener("keydown", e => { if (e.key == "Escape" && !el.hidden) close() });
  icon.addEventListener("click", e => { e.preventDefault(); open() });
  window.gaveta = { open };
})();
