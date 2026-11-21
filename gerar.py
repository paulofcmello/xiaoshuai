#!/usr/bin/env python3
"""Gera e publica a loja de um revendedor a partir do Yupoo dele.

    python3 gerar.py --nome "Xiaoshuai" --whatsapp "+86 195 2122 8559" --yupoo https://x.yupoo.com/photos/1022669895/albums
"""
import argparse, json, re, shutil, subprocess, sys, unicodedata
from collections import Counter
from pathlib import Path

from gerador import yupoo, classificar

RAIZ = Path(__file__).resolve().parent
PAGINAS = ["index.html", "classico.html", "camisa.html", "carrinho.html", "style.css", "atacado.css", "gaveta.js", "busca.js", "pedido.html", "dados.js", "liga.html"]
CAMPOS = ["h", "n", "l", "t", "tz", "te", "q", "qz", "qe", "s", "p", "u", "sh"]
LEVE = ["h", "n", "l", "t", "tz", "te", "q", "qz", "qe", "p", "sh"]  # o que um cartão precisa (sem tamanhos e link do álbum)
LIGAS = ["brasileirao", "premier", "laliga", "seriea", "bundesliga", "ligue1", "portugal", "argentina", "liga-mx", "mls",
         "saudi", "outras-ligas", "selecoes", "retro", "outros"]
STAR = ["Flamengo", "Palmeiras", "Corinthians", "Manchester United", "Arsenal", "Liverpool", "Real Madrid", "Barcelona",
        "Inter Milan", "Napoli", "Brasil", "Argentina"]


def slug(nome):
    s = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "loja"


def logo(nome):
    nome = nome.strip().upper()
    partes = nome.split(None, 1)
    a, b = (partes[0] + " ", partes[1]) if len(partes) == 2 else (nome[: len(nome) // 2], nome[len(nome) // 2 :])
    return f"{a}<span>{b}</span>"


def numero(n, sep):
    return f"{n:,}".replace(",", sep)


def escolher_destaque(cat):
    for regra in (lambda x: x["l"] == "brasileirao" and x["t"].startswith("Camisa 1"),
                  lambda x: x["t"].startswith("Camisa 1"),
                  lambda x: x["l"] != "outros"):
        achou = next((x for x in cat if regra(x)), None)
        if achou:
            return achou
    return cat[0]


def _json(caminho, dado):
    caminho.write_text(json.dumps(dado, ensure_ascii=False, separators=(",", ":")))


def previa(itens, n=12):
    """Um por time primeiro (times conhecidos antes), depois o resto; para a vitrine de cada liga na home."""
    vistos, prim = set(), []
    for x in itens:
        if not x.get("sh") and x["n"] not in vistos:
            vistos.add(x["n"])
            prim.append(x)
    prim.sort(key=lambda x: x["n"] not in STAR)
    ids = {id(x) for x in prim}
    return (prim + [x for x in itens if id(x) not in ids])[:n]


def dados(saida, cat):
    """Catálogo em arquivos pequenos, para o celular não ler tudo de uma vez:
    home.json (contagem e 12 por liga), l-<liga>.json (a liga inteira), i-<xx>.json (camisas pelos 2 primeiros
    caracteres do hash, para página da camisa, carrinho e pedido) e busca.json (só o que a busca usa)."""
    d = saida / "dados"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir()
    leve = lambda x: {k: x[k] for k in LEVE if k in x}
    por_liga = {}
    for x in cat:
        por_liga.setdefault(x["l"], []).append(x)
    ordem = [k for k in LIGAS if k in por_liga] + [k for k in por_liga if k not in LIGAS]
    _json(d / "home.json", {"n": len(cat), "c": {k: len(por_liga[k]) for k in ordem},
                            "p": {k: [leve(x) for x in previa(por_liga[k])] for k in ordem}})
    for k in ordem:
        _json(d / f"l-{k}.json", [leve(x) for x in por_liga[k]])
    shards = {}
    for x in cat:
        shards.setdefault(x["h"][:2].lower(), []).append({k: x[k] for k in CAMPOS if k in x})
    for k, v in shards.items():
        _json(d / f"i-{k}.json", v)
    _json(d / "busca.json", [[x["h"], x["n"], x["t"], x["te"], x["tz"], x.get("q", ""), x.get("qe", ""), x["p"], x.get("sh", 0)] for x in cat])


def montar(saida, nome, whatsapp, cotacao, frete, cat, imagem=None, banner=None, classico=True, pers=0, patch=0):
    total = len(cat)
    modelos = total if total < 100 else total // 100 * 100
    d = escolher_destaque(cat)
    trocas = {
        "{{NOME}}": nome,
        "{{LOGO}}": f'<img src="{imagem}" alt="{nome}">' if imagem else logo(nome),
        "{{WA}}": whatsapp,
        "{{PRECO_PERS}}": str(pers),
        "{{PRECO_PATCH}}": str(patch),
        "{{CLASSICO_REDIRECT}}": '<script>try{if(localStorage.visual=="classico")location.replace("classico.html"+location.search+location.hash)}catch{}</script>' if classico else "",
        "{{CLASSICO_BOTAO}}": '    <a class="ico vis" href="classico.html" data-en="Classic look" data-zh="经典外观">Visual clássico</a>\n' if classico else "",
        "{{BANNER}}": f'<a class="bigbanner" href="#colecoes"><img src="{banner}" alt="{nome}"></a>' if banner else "",
        "{{COTACAO}}": str(cotacao),
        "{{FRETE}}": json.dumps(frete),
        "{{TOTAL}}": numero(total, "."),
        "{{TOTAL_ZH}}": numero(total, ","),
        "{{MODELOS}}": numero(modelos, "."),
        "{{MODELOS_ZH}}": numero(modelos, ","),
        "{{HERO}}": json.dumps({"n": d["t"], "z": d["tz"], "e": d["te"], "p": d["p"], "img": f"fotos/all/{d['h']}.webp"}, ensure_ascii=False),
    }
    if not classico:
        (saida / "classico.html").unlink(missing_ok=True)
    for p in PAGINAS:
        if p == "classico.html" and not classico:
            continue
        s = (RAIZ / "modelo" / p).read_text()
        for k, v in trocas.items():
            s = s.replace(k, v)
        sobrou = re.findall(r"\{\{[A-Z_]+\}\}", s)
        assert not sobrou, f"{p}: marcador sem valor {sobrou}"
        (saida / p).write_text(s)
    # catalog.json inteiro: só a home clássica lê; fica na pasta (para gerar de novo) mas só vai pro ar com ela
    _json(saida / "catalog.json", [{k: x[k] for k in CAMPOS if k in x} for x in cat])
    dados(saida, cat)
    (saida / ".vercelignore").write_text("_albuns.json\n_sem-classico\n" + ("" if classico else "catalog.json\n"))


def amostra(url, n, vistos):
    """Até n álbuns da 1ª página de uma categoria: só da liga dominante, um por time primeiro."""
    itens = [i for i in yupoo.scrape(url, paginas=1) if i["h"] not in vistos]
    cl = classificar.classify_all(itens)
    liga = Counter(c["l"] for c in cl if c["l"] != "outros").most_common(1)
    ok = [(i, c) for i, c in zip(itens, cl) if liga and c["l"] == liga[0][0]]
    times, primeiro, resto = set(), [], []
    for i, c in ok:
        (resto if c["n"] in times else primeiro).append(i)
        times.add(c["n"])
    return (primeiro + resto)[:n]


def publicar(saida, nome_projeto):
    # --archive=tgz: sem ele a Vercel conta cada foto como um upload e o plano grátis trava em 5.000/dia
    r = subprocess.run(["npx", "-y", "vercel@latest", "deploy", "--prod", "--yes", "--archive=tgz", "--name", nome_projeto],
                       cwd=saida, capture_output=True, text=True)
    url = re.search(r"Aliased\s+(https://\S+)", r.stdout + r.stderr)
    if r.returncode or not url:
        sys.exit("Falha ao publicar na Vercel:\n" + (r.stderr or r.stdout)[-2000:])
    return url.group(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nome", required=True, help="nome da loja, ex.: Xiaoshuai")
    ap.add_argument("--whatsapp", required=True, help="número com DDI, ex.: +86 195 2122 8559")
    ap.add_argument("--yupoo", required=True, nargs="+", action="extend", help="link da loja no Yupoo (pode passar vários, separados por espaço)")
    ap.add_argument("--extra", nargs=2, action="append", metavar=("LINK", "N"),
                    help="mais N camisas de outra categoria do Yupoo (pode repetir)")
    ap.add_argument("--preco", type=int, default=58, help="preço da versão torcedor em reais (padrão 58)")
    ap.add_argument("--cotacao", type=float, default=5.8, help="reais por dólar, para o frete (padrão 5.8)")
    ap.add_argument("--preco-jogador", type=int, default=87, help="preço da versão jogador em reais (padrão 87)")
    ap.add_argument("--preco-retro", type=int, help="preço das retrô em reais (padrão: o mesmo da versão torcedor)")
    ap.add_argument("--personalizacao", type=float, default=0, help="preço de nome e número por peça, em reais (padrão 0: a combinar no WhatsApp)")
    ap.add_argument("--patch", type=float, default=0, help="preço de cada patch, em reais; o cliente escolhe de 0 a 4 (padrão 0: sem opção de patch)")
    ap.add_argument("--frete", default="5,4,3", help="frete em dólar com 1, 2, 3… camisas; depois disso é grátis (padrão 5,4,3)")
    ap.add_argument("--logo", type=Path, help="imagem que substitui o nome escrito no topo e no rodapé (fica guardada na pasta da loja)")
    ap.add_argument("--banner", type=Path, help="imagem larga (3:1) que substitui o topo da home (fica guardada na pasta da loja)")
    ap.add_argument("--sem-classico", action="store_true", help="tira a home antiga e o botão de trocar de visual (fica guardado na pasta da loja)")
    ap.add_argument("--slug", help="nome da pasta e do projeto na Vercel (padrão: a partir do nome)")
    ap.add_argument("--sem-publicar", action="store_true", help="só gera a pasta, não publica")
    a = ap.parse_args()

    wa = re.sub(r"\D", "", a.whatsapp)
    if not 8 <= len(wa) <= 15:
        sys.exit(f"Número de WhatsApp inválido: {a.whatsapp!r} (use o DDI, ex.: +55 11 91234-5678)")
    try:
        frete = [float(v) for v in a.frete.split(",")]
    except ValueError:
        sys.exit(f"Frete inválido: {a.frete!r} (use valores em dólar separados por vírgula, ex.: 5,4,3)")
    if a.logo and not a.logo.is_file():
        sys.exit(f"Logo não encontrado: {a.logo}")
    if a.banner and not a.banner.is_file():
        sys.exit(f"Banner não encontrado: {a.banner}")
    nome_slug = a.slug or slug(a.nome)
    saida = RAIZ / "sites" / nome_slug
    (saida / "fotos" / "all").mkdir(parents=True, exist_ok=True)

    itens = []
    for link in a.yupoo:
        print(f"1/4 Lendo o Yupoo: {link}")
        vistos = {i["h"] for i in itens}
        novos = [i for i in yupoo.scrape(link) if i["h"] not in vistos]
        print(f"    {len(novos)} álbuns")
        itens += novos
    for url, n in a.extra or []:
        mais = amostra(url, int(n), {i["h"] for i in itens})
        print(f"    + {len(mais)} de {url}")
        itens += mais
    (saida / "_albuns.json").write_text(json.dumps(itens, ensure_ascii=False))
    print(f"    {len(itens)} álbuns")

    print("2/4 Separando por liga e modelo")
    cat = classificar.classify_all(itens)
    links = {i["h"]: i.get("u") or "" for i in itens}
    for x in cat:
        x["p"] = (a.preco_jogador if "Player" in x["qe"].split(" · ")
                  else a.preco_retro if x["l"] == "retro" and a.preco_retro else a.preco)
        x["u"] = links[x["h"]]

    print("3/4 Baixando fotos (pula as que já existem)")
    falhas = set(yupoo.download(itens, saida / "fotos" / "all"))
    cat = [x for x in cat if x["h"] not in falhas]
    if falhas:
        print(f"    {len(falhas)} fotos falharam e ficaram de fora")
    if not cat:
        sys.exit("Nenhuma camisa com foto; nada a gerar.")

    if a.logo:
        for velho in saida.glob("logo.*"):
            velho.unlink()
        shutil.copy(a.logo, saida / ("logo" + a.logo.suffix.lower()))
    if a.banner:
        for velho in saida.glob("banner.*"):
            velho.unlink()
        shutil.copy(a.banner, saida / ("banner" + a.banner.suffix.lower()))
    imagem = next((f.name for f in saida.glob("logo.*")), None)  # sem --logo, reaproveita o da última vez
    banner = next((f.name for f in saida.glob("banner.*")), None)
    if a.sem_classico:
        (saida / "_sem-classico").touch()
    montar(saida, a.nome, wa, a.cotacao, frete, cat, imagem, banner, classico=not (saida / "_sem-classico").exists(),
           pers=a.personalizacao, patch=a.patch)
    ligas = {}
    for x in cat:
        ligas[x["l"]] = ligas.get(x["l"], 0) + 1
    print(f"    {len(cat)} camisas: " + ", ".join(f"{k} {v}" for k, v in sorted(ligas.items(), key=lambda kv: -kv[1])))
    print(f"    Pasta: sites/{nome_slug}")

    if a.sem_publicar:
        print("4/4 Publicação pulada. Para ver: cd sites/%s && python3 -m http.server" % nome_slug)
        return
    print("4/4 Publicando na Vercel")
    print("    No ar:", publicar(saida, nome_slug))


if __name__ == "__main__":
    main()
