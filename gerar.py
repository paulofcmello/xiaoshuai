#!/usr/bin/env python3
"""Gera e publica a loja de um revendedor a partir do Yupoo dele.

    python3 gerar.py --nome "Xiaoshuai" --whatsapp "+86 195 2122 8559" --yupoo https://x.yupoo.com/photos/1022669895/albums
"""
import argparse, json, re, subprocess, sys, unicodedata
from collections import Counter
from pathlib import Path

from gerador import yupoo, classificar

RAIZ = Path(__file__).resolve().parent
PAGINAS = ["index.html", "camisa.html", "carrinho.html", "style.css"]
CAMPOS = ["h", "n", "l", "t", "tz", "te", "q", "qz", "qe", "s"]


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


def montar(saida, nome, whatsapp, preco, cat):
    total = len(cat)
    modelos = total if total < 100 else total // 100 * 100
    d = escolher_destaque(cat)
    trocas = {
        "{{NOME}}": nome,
        "{{LOGO}}": logo(nome),
        "{{WA}}": whatsapp,
        "{{PRECO}}": str(preco),
        "{{TOTAL}}": numero(total, "."),
        "{{TOTAL_ZH}}": numero(total, ","),
        "{{MODELOS}}": numero(modelos, "."),
        "{{MODELOS_ZH}}": numero(modelos, ","),
        "{{HERO}}": json.dumps({"n": d["t"], "z": d["tz"], "e": d["te"], "img": f"fotos/all/{d['h']}.webp"}, ensure_ascii=False),
    }
    for p in PAGINAS:
        s = (RAIZ / "modelo" / p).read_text()
        for k, v in trocas.items():
            s = s.replace(k, v)
        sobrou = re.findall(r"\{\{[A-Z_]+\}\}", s)
        assert not sobrou, f"{p}: marcador sem valor {sobrou}"
        (saida / p).write_text(s)
    (saida / "catalog.json").write_text(json.dumps([{k: x[k] for k in CAMPOS} for x in cat], ensure_ascii=False, separators=(",", ":")))
    (saida / ".vercelignore").write_text("_albuns.json\n")


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
    ap.add_argument("--yupoo", required=True, help="link da loja no Yupoo")
    ap.add_argument("--extra", nargs=2, action="append", metavar=("LINK", "N"),
                    help="mais N camisas de outra categoria do Yupoo (pode repetir)")
    ap.add_argument("--preco", type=int, default=52, help="preço único em reais (padrão 52)")
    ap.add_argument("--slug", help="nome da pasta e do projeto na Vercel (padrão: a partir do nome)")
    ap.add_argument("--sem-publicar", action="store_true", help="só gera a pasta, não publica")
    a = ap.parse_args()

    wa = re.sub(r"\D", "", a.whatsapp)
    if not 8 <= len(wa) <= 15:
        sys.exit(f"Número de WhatsApp inválido: {a.whatsapp!r} (use o DDI, ex.: +55 11 91234-5678)")
    nome_slug = a.slug or slug(a.nome)
    saida = RAIZ / "sites" / nome_slug
    (saida / "fotos" / "all").mkdir(parents=True, exist_ok=True)

    print(f"1/4 Lendo o Yupoo: {a.yupoo}")
    itens = yupoo.scrape(a.yupoo)
    for url, n in a.extra or []:
        mais = amostra(url, int(n), {i["h"] for i in itens})
        print(f"    + {len(mais)} de {url}")
        itens += mais
    (saida / "_albuns.json").write_text(json.dumps(itens, ensure_ascii=False))
    print(f"    {len(itens)} álbuns")

    print("2/4 Separando por liga e modelo")
    cat = classificar.classify_all(itens)

    print("3/4 Baixando fotos (pula as que já existem)")
    falhas = set(yupoo.download(itens, saida / "fotos" / "all"))
    cat = [x for x in cat if x["h"] not in falhas]
    if falhas:
        print(f"    {len(falhas)} fotos falharam e ficaram de fora")
    if not cat:
        sys.exit("Nenhuma camisa com foto; nada a gerar.")

    montar(saida, a.nome, wa, a.preco, cat)
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
