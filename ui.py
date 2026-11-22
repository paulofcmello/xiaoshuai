#!/usr/bin/env python3
"""Formulário local para o gerar.py:  python3 ui.py  →  http://localhost:8000"""
import base64, json, subprocess, sys, tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
PAGINA = """<!doctype html><meta charset=utf-8><title>Gerar loja</title>
<form id=f style="display:grid;gap:6px;max-width:520px;font:14px sans-serif">
Nome <input name=nome required>
WhatsApp <input name=whatsapp placeholder="+86 195 2122 8559" required>
Links do Yupoo (um por linha) <textarea name=yupoo rows=3 required></textarea>
Logo / foto de perfil <input type=file name=logo accept="image/*">
Preço torcedor <input name=preco value=58>
Preço jogador <input name=preco_jogador value=87>
Camisas por liga (vazio = catálogo inteiro) <input name=amostra value=10>
Slug (opcional) <input name=slug>
<label><input type=checkbox name=gerar_banner checked> Gerar banner (Codex)</label>
<label><input type=checkbox name=cloudflare> Publicar no Cloudflare (senão Vercel)</label>
<label><input type=checkbox name=sem_publicar> Não publicar</label>
<button>Gerar</button></form><pre id=o></pre>
<script>f.onsubmit=async e=>{e.preventDefault();const d=Object.fromEntries(new FormData(f));
for(const k of ['gerar_banner','cloudflare','sem_publicar'])d[k]=f[k].checked;
const l=f.logo.files[0];d.logo=l?{nome:l.name,b64:btoa(String.fromCharCode(...new Uint8Array(await l.arrayBuffer())))}:null;
o.textContent='';const r=await fetch('/',{method:'POST',body:JSON.stringify(d)}),rd=r.body.getReader(),t=new TextDecoder();
for(;;){const{done,value}=await rd.read();if(done)break;o.textContent+=t.decode(value);}}</script>"""


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(PAGINA.encode())

    def do_POST(self):
        d = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        cmd = [sys.executable, "-u", str(RAIZ / "gerar.py"), "--nome", d["nome"], "--whatsapp", d["whatsapp"],
               "--yupoo", *d["yupoo"].split(), "--preco", d["preco"], "--preco-jogador", d["preco_jogador"]]
        if d["amostra"].strip():
            cmd += ["--amostra", d["amostra"].strip()]
        if d["slug"].strip():
            cmd += ["--slug", d["slug"].strip()]
        for flag in ("gerar_banner", "cloudflare", "sem_publicar"):
            if d[flag]:
                cmd.append("--" + flag.replace("_", "-"))
        if d["logo"]:  # só o nome do arquivo, sem pastas
            tmp = Path(tempfile.mkdtemp()) / Path(d["logo"]["nome"]).name
            tmp.write_bytes(base64.b64decode(d["logo"]["b64"]))
            cmd += ["--logo", str(tmp)]
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        p = subprocess.Popen(cmd, cwd=RAIZ, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for linha in p.stdout:
            self.wfile.write(linha)
            self.wfile.flush()
        self.wfile.write(f"\n[terminou, código {p.wait()}]\n".encode())


if __name__ == "__main__":
    print("http://localhost:8000")
    ThreadingHTTPServer(("127.0.0.1", 8000), H).serve_forever()  # só local: o formulário roda comandos
