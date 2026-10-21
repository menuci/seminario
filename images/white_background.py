"""
Coloca um fundo branco (com cantos arredondados e uma margem) num arquivo SVG.
Uso:  python white_background.py images/var_full.svg            -> sobrescreve o arquivo
      python white_background.py entrada.svg saida.svg          -> salva em outro arquivo
"""
import re
import sys

MARGEM = 0.01   # margem branca em volta, como fração do tamanho da figura
RAIO   = 0.001   # arredondamento dos cantos (0 = cantos retos)

entrada = sys.argv[1]
saida = sys.argv[2] if len(sys.argv) > 2 else entrada
svg = open(entrada, encoding="utf-8").read()

abertura = re.search(r"<svg\b[^>]*>", svg)
tag = abertura.group(0)
vb = re.search(r'viewBox="([^"]+)"', tag)
if vb:
    x, y, w, h = (float(v) for v in vb.group(1).replace(",", " ").split())
else:  # sem viewBox: usa width/height (ex.: "432pt")
    num = lambda s: float(re.match(r"[\d.]+", s).group(0))
    w = num(re.search(r'width="([^"]+)"', tag).group(1))
    h = num(re.search(r'height="([^"]+)"', tag).group(1))
    x = y = 0.0

m = MARGEM * max(w, h)
r = RAIO * max(w, h)
nx, ny, nw, nh = x - m, y - m, w + 2 * m, h + 2 * m

# aumenta o viewBox para caber a margem e mantém a proporção do width/height
nova_tag = re.sub(r'\sviewBox="[^"]*"', "", tag)
nova_tag = nova_tag[:-1] + f' viewBox="{nx:g} {ny:g} {nw:g} {nh:g}">'
for atr, antigo, novo in (("width", w, nw), ("height", h, nh)):
    mm = re.search(rf'\s{atr}="([\d.]+)([a-z%]*)"', nova_tag)
    if mm:
        valor = float(mm.group(1)) * novo / antigo
        nova_tag = nova_tag.replace(mm.group(0), f' {atr}="{valor:g}{mm.group(2)}"')

fundo = f'<rect x="{nx:g}" y="{ny:g}" width="{nw:g}" height="{nh:g}" rx="{r:g}" fill="white"/>'
svg = svg.replace(tag, nova_tag + "\n" + fundo, 1)

open(saida, "w", encoding="utf-8").write(svg)
print(f"{saida}: fundo branco adicionado")
