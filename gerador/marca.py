"""Cor da marca (tirada do banner ou do logo) e prompt do banner para o ChatGPT. Sem IA, sem tokens."""
import colorsys
from PIL import Image

PADRAO = "#E1251B"  # vermelho do modelo


def _lum(rgb):
    f = lambda c: (c / 255 / 12.92) if c / 255 <= .03928 else ((c / 255 + .055) / 1.055) ** 2.4
    r, g, b = map(f, rgb)
    return .2126 * r + .7152 * g + .0722 * b


def _hex(rgb):
    return "#%02X%02X%02X" % tuple(round(c) for c in rgb)


def cor_principal(img):
    """A cor mais viva e frequente da imagem (ignora branco, cinza e preto), escurecida até o texto branco ler bem."""
    im = Image.open(img).convert("RGB")
    if im.width > 2.5 * im.height:  # banner: as camisas fixas (amarelo do Brasil etc.) ficam à direita, não contam
        im = im.crop((0, 0, im.width * 2 // 5, im.height))
    im.thumbnail((160, 160))
    melhor, nota = None, 0
    for n, rgb in im.quantize(12).convert("RGB").getcolors():
        h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
        pt = n * s * s * v if v > .25 else 0
        if pt > nota:
            melhor, nota = (h, s, v), pt
    if not melhor:
        return PADRAO
    h, s, v = melhor
    s, v = max(s, .6), max(v, .55)
    rgb = [c * 255 for c in colorsys.hsv_to_rgb(h, s, v)]
    while _lum(rgb) > .2 and v > .3:  # contraste >= ~4 com branco
        v -= .03
        rgb = [c * 255 for c in colorsys.hsv_to_rgb(h, s, v)]
    return _hex(rgb)


def aplicar(css, cor):
    """Troca o vermelho do modelo pela cor da marca num texto de CSS/HTML."""
    r, g, b = (int(cor[i:i + 2], 16) for i in (1, 3, 5))
    escura = _hex([c * .75 for c in (r, g, b)])
    clara = _hex([c + (255 - c) * .8 for c in (r, g, b)])
    for velho, novo in (("#E1251B", cor), ("#B81A12", escura), ("#D30005", cor), ("#FFD5D2", clara)):
        css = css.replace(velho, novo)
    return css.replace("rgba(225,37,27,", f"rgba({r},{g},{b},")


def prompt_banner(nome, titulo, cor=None):  # só o cenário: as camisas entram depois (gerador/camisas.png)
    """Texto para colar no ChatGPT (anexe o logo ou foto de perfil do fornecedor, se tiver)."""
    paleta = (f"Use {cor} as the dominant accent color and derive every other color from the attached logo/profile picture"
              if cor else "Pick the palette from the attached logo/profile picture (dominant color + dark + white)")
    return f"""Create a wide website hero banner, aspect ratio 3:1 (2000x667 px), for a Brazilian football-jersey wholesale store.

STYLE: bold, energetic sports-poster look, glossy 3D render, dramatic stadium lights, grass at the bottom, glowing particles, strong depth.
PALETTE: {paleta}. The whole scene (background, glow, text panels) must follow this palette so a website can match it.

LAYOUT:
- Left third: the store logo "{nome}" large (use the attached logo exactly if there is one), then the big white headline "{titulo}" in heavy condensed italic type with a dark outline, then a rounded badge below it: "ENVIO PARA TODO O BRASIL".
- Right 60% of the image: NO jerseys, NO mascot, NO people. Only the stadium, bright floodlights, a big glowing light swirl and the grass, with the center-right area kept visually calm and empty because jerseys will be added there later.
- Keep clean margins; all text sharp and spelled exactly as written in Portuguese. No other text, no watermarks, no phone numbers.

Output a single image, no borders."""


def gerar_banner(prompt_txt, logo, destino):
    """Cenário pelo Codex CLI (login do ChatGPT, sem chave de API) + as 5 camisas fixas coladas por cima. True se salvou."""
    import subprocess, time
    from pathlib import Path
    from PIL import ImageFilter
    inicio = time.time()
    ped = f"Use your image generation tool (not code) to generate the image described below, using the attached image as the store logo. Print only the saved image path.\n\n{prompt_txt}"
    cmd = ["codex", "exec", "--skip-git-repo-check"] + (["-i", str(logo)] if logo else []) + ["-"]
    subprocess.run(cmd, input=ped, text=True, capture_output=True, timeout=600)
    novas = [p for p in (Path.home() / ".codex" / "generated_images").glob("**/*.png") if p.stat().st_mtime > inicio]
    if not novas:
        return False
    cena = Image.open(max(novas, key=lambda p: p.stat().st_mtime)).convert("RGBA").resize((2000, 667))
    camisas = Image.open(Path(__file__).with_name("camisas.png"))
    camisas = camisas.resize((1250, round(1250 * camisas.height / camisas.width)))
    x, y = 2000 - camisas.width - 30, 667 - camisas.height - 45
    sombra = Image.new("RGBA", cena.size, (0, 0, 0, 0))
    sombra.paste((0, 0, 0, 150), (x, y + 18), camisas.split()[3])
    cena.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(14)))
    cena.alpha_composite(camisas, (x, y))
    cena.convert("RGB").save(destino, quality=82)
    return True
