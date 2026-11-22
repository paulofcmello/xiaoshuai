// catálogo em arquivos pequenos (gerar.py escreve a pasta dados/); cada página só baixa o que usa
const Dados = (() => {
  const cache = {};
  const get = f => cache[f] ??= fetch("dados/" + f).then(r => { if (!r.ok) throw new Error(f); return r.json() });
  const shard = h => String(h).slice(0, 2).toLowerCase();
  return {
    home: () => get("home.json"),
    liga: k => get(`l-${k}.json`),
    busca: () => get("busca.json"),
    // { hash: camisa } com tudo (tamanhos, link do álbum) só das camisas pedidas
    itens: hs => Promise.all([...new Set(hs.map(shard))].map(s => get(`i-${s}.json`).catch(() => [])))
      .then(ls => { const m = {}; ls.flat().forEach(x => m[x.h] = x); return m }),
  };
})();

// loja sem preço: os preços continuam nos dados, só não aparecem (o frete só diz se é grátis)
const SEM_PRECO = {{SEM_PRECO}};

const L = {brasileirao:["Brasileirão","巴西甲级联赛"],premier:["Premier League","英超"],laliga:["La Liga","西甲"],seriea:["Serie A","意甲"],bundesliga:["Bundesliga","德甲"],ligue1:["Ligue 1","法甲"],portugal:["Liga Portugal","葡超"],argentina:["Argentina","阿根廷联赛"],"liga-mx":["Liga MX","墨西哥联赛"],mls:["MLS","美职联"],saudi:["Saudi Pro League","沙特联赛"],"outras-ligas":["Outras ligas","其他联赛","Other leagues"],selecoes:["Seleções","国家队","National teams"],nba:["NBA","NBA","NBA"],treino:["Roupas de treino","训练服装","Training wear"],retro:["Retrô","复古球衣","Retro"],outros:["Outros","其他","Other"]};

// cartão de camisa (home, ligas, página da camisa)
const cardHTML = (x, T) => {
  const pl = (x.qe || "").split(" · ").includes("Player"), t = T(x.t, x.tz, x.te), q = T(x.q, x.qz, x.qe);
  return `<a class="card" href="camisa.html?id=${x.h}"><div class="pic">${pl ? `<span class="tag">${T("Jogador", "球员版", "Player")}</span>` : ""}<img src="fotos/all/${x.h}.webp" alt="${t}" loading="lazy" decoding="async" width="440" height="440"></div><h3>${t}</h3>${q ? `<div class="meta">${q}</div>` : ""}${SEM_PRECO ? "" : `<div class="price">R$ ${x.p}</div>`}</a>`;
};
