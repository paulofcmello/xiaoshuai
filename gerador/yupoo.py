"""Scrape a Yupoo store's album listing and download covers as small webp."""
import concurrent.futures as cf
import html
import os
import re
import shutil
import subprocess
import tempfile
import urllib.request
from urllib.parse import urlparse

UA = {"User-Agent": "Mozilla/5.0"}


def _get(url, headers=UA, timeout=30):
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as r:
                return r.read()
        except Exception:
            if i == 2:
                raise


def _base(url):
    u = urlparse(url if "//" in url else "https://" + url)
    m = re.match(r"/photos/([^/?#]+)/categories/(\d+)", u.path)
    if u.netloc == "x.yupoo.com" and m:  # x.yupoo.com/photos/<loja>/categories/<id> só funciona no subdomínio da loja
        return f"https://{m.group(1)}.x.yupoo.com/categories/{m.group(2)}?isSubCate=false"
    m = re.search(r"/categories/(\d+)", u.path)
    if m:  # .../categories/<id>: só essa categoria
        return f"{u.scheme}://{u.netloc}/categories/{m.group(1)}?isSubCate=false"
    m = re.search(r"/photos/([^/?#]+)", u.path)
    if m:  # .../photos/<id>/albums
        return f"{u.scheme}://{u.netloc}/photos/{m.group(1)}/albums?tab=gallery"
    return f"{u.scheme}://{u.netloc}/albums?tab=gallery"


def _parse(page):
    out = []
    # categorias põem o título só no <a> e a foto em data-src; a galeria usa alt e src
    for a in re.findall(r'<a\s[^>]*class="album__main".*?</a>', page, re.S):
        al = re.search(r'href="/albums/(\d+)', a)
        t, s = re.search(r'title="([^"]*)"', a), re.search(r'<img\s[^>]*?\b(?:data-)?src="([^"]+)"', a)
        if not (t and s) or "im_photo_album" in s.group(1):  # placeholder = álbum vazio
            continue
        src = s.group(1)
        if src.startswith("//"):
            src = "https:" + src
        parts = src.split("?")[0].split("/")
        if len(parts) < 2:
            continue
        out.append({"t": html.unescape(t.group(1)).strip(), "img": src, "h": parts[-2], "a": al and al.group(1)})
    return out


def scrape(url, paginas=None):
    base = _base(url)
    seen, items = set(), []
    page = 1
    while True:
        new = [i for i in _parse(_get(f"{base}&page={page}").decode("utf-8", "replace")) if i["h"] not in seen]
        if not new or (paginas and page > paginas):
            break
        for i in new:
            seen.add(i["h"])
            al = i.pop("a")
            i["u"] = al and f"{urlparse(base).scheme}://{urlparse(base).netloc}/albums/{al}?uid=1"
        items += new
        page += 1
    if not items:
        raise RuntimeError(f"Nenhum álbum encontrado em {base} (link errado, loja privada ou layout mudou)")
    return items


def categorias(url, maximo=30):
    """Links das categorias da loja no Yupoo; lista vazia se a loja não usa categorias."""
    u = urlparse(url if "//" in url else "https://" + url)
    m = re.match(r"/photos/([^/?#]+)", u.path)
    host = f"{m.group(1)}.x.yupoo.com" if u.netloc == "x.yupoo.com" and m else u.netloc
    if host == "x.yupoo.com":
        return []
    try:
        page = _get(f"https://{host}/categories").decode("utf-8", "replace")
    except Exception:  # loja sem página de categorias
        return []
    ids = list(dict.fromkeys(re.findall(r'href="/categories/(\d+)', page)))[:maximo]
    return [f"https://{host}/categories/{i}" for i in ids]


def download(items, outdir, workers=16):
    if not shutil.which("cwebp"):
        raise RuntimeError("cwebp não encontrado. Instale com: brew install webp")
    os.makedirs(outdir, exist_ok=True)
    todo = [i for i in items if not os.path.exists(os.path.join(outdir, i["h"] + ".webp"))]
    failed, done = [], 0
    with tempfile.TemporaryDirectory() as tmp:
        def one(it):
            h = it["h"]
            try:
                src = os.path.join(tmp, h + os.path.splitext(it["img"].split("?")[0])[1])
                with open(src, "wb") as f:
                    f.write(_get(it["img"], {**UA, "Referer": "https://x.yupoo.com/"}))
                dst = os.path.join(outdir, h + ".webp")
                subprocess.run(["cwebp", "-quiet", "-q", "42", "-m", "6", "-resize", "440", "0", src, "-o", dst],
                               check=True, capture_output=True)
                os.remove(src)
                return None
            except Exception:
                return h
        with cf.ThreadPoolExecutor(workers) as ex:
            for r in ex.map(one, todo):
                done += 1
                if r:
                    failed.append(r)
                if done % 250 == 0:
                    print(f"{done}/{len(todo)} ({len(failed)} falhas)", flush=True)
    return failed
