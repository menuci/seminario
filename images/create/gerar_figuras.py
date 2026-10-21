"""
Gera as figuras dos kernels para a apresentação:
  images/birth_dispersal.svg     (kernel de dispersão, linha do Birth)
  images/competition_kernel.svg  (kernel de competição, linha do Death)
e, se o Playwright estiver instalado, também as versões PNG com fundo transparente.

Requisitos:
  - Node.js + MathJax:     npm install mathjax-full@3.2.2
  - Python 3
  - (opcional, para PNG):  pip install playwright && playwright install chromium

Uso:
  python gerar_figuras.py
"""

import json
import math
import os
import random
import re
import subprocess

# --------------------------------------------------------------------------
# Configurações gerais
# --------------------------------------------------------------------------
PASTA_SAIDA = "images"

FG    = "#e6edf3"   # plantas e rótulos
MUTED = "#9aa5b1"   # eixos e detalhes

COR_DISPERSAO  = "#7ee787"  # verde  (mesma cor do \phi_D na equação)
COR_COMPETICAO = "#ffb86c"  # laranja (mesma cor do \phi_C na equação)

W = 576  # largura das figuras (proporção da coluna da direita no slide)


# --------------------------------------------------------------------------
# Rótulos matemáticos com MathJax
# --------------------------------------------------------------------------
def renderizar_tex(expressoes):
    """Chama o tex.js e devolve {expressão: svg} com os glifos do MathJax."""
    saida = subprocess.check_output(["node", "tex.js", json.dumps(expressoes)])
    return json.loads(saida)


def rotulo(M, tex, x, y, tamanho, cor, ancora="middle"):
    """Posiciona um rótulo do MathJax com a linha de base em y.
    ancora='middle' centraliza em x; ancora='left' começa em x."""
    s = M[tex]
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', s).group(1).split()]
    largura = vb[2] / 1000 * tamanho
    altura = vb[3] / 1000 * tamanho
    esquerda = x - largura / 2 if ancora == "middle" else x
    topo = y + vb[1] / 1000 * tamanho            # vb[1] é negativo: altura acima da linha de base
    conteudo = re.sub(r"^<svg[^>]*>", "", s)[:-len("</svg>")]
    return (f'<svg x="{esquerda:.1f}" y="{topo:.1f}" width="{largura:.1f}" height="{altura:.1f}" '
            f'viewBox="{" ".join(map(str, vb))}" color="{cor}" overflow="visible">{conteudo}</svg>')


# --------------------------------------------------------------------------
# Peças comuns
# --------------------------------------------------------------------------
def perfil_gaussiano(cx, base, amp, sig, meia_largura=105, passo=3):
    """Caminho SVG de uma gaussiana centrada em cx (y cresce para baixo)."""
    return " ".join(
        f"{'M' if k == 0 else 'L'}{x:.1f},{base - amp * math.exp(-((x - cx) ** 2) / (2 * sig ** 2)):.1f}"
        for k, x in enumerate(range(cx - meia_largura, cx + meia_largura + 1, passo))
    )


def campo(y, altura):
    """Retângulo do campo (vista de cima)."""
    return (f'<rect x="16" y="{y}" width="544" height="{altura}" rx="10" fill="#ffffff" '
            f'fill-opacity="0.025" stroke="#ffffff" stroke-opacity="0.16"/>')


def contornos(cx, cy, sig, cor, op1=0.55, op2=0.28):
    """Contornos do kernel 2D em 1 e 2 desvios-padrão (op1, op2 = opacidades)."""
    return (f'<circle cx="{cx}" cy="{cy}" r="{sig}" fill="none" stroke="{cor}" stroke-opacity="{op1}" stroke-dasharray="3 3"/>\n'
            f'  <circle cx="{cx}" cy="{cy}" r="{2 * sig}" fill="none" stroke="{cor}" stroke-opacity="{op2}" stroke-dasharray="3 3"/>')


# --------------------------------------------------------------------------
# Figura 1: kernel de dispersão (nascimento)
# --------------------------------------------------------------------------
def figura_dispersao(M):
    COR = COR_DISPERSAO
    H = 245
    px, py = 225, 168      # planta-mãe
    ox, oy = 283, 140      # filhote
    sig = 30               # 1 desvio-padrão (px) -> parâmetro s

    # outras plantas espalhadas (semente fixa: sempre o mesmo desenho)
    random.seed(7)
    pts = []
    while len(pts) < 17:
        x, y = random.uniform(40, 540), random.uniform(112, 222)
        if math.hypot(x - px, y - py) < 26 or math.hypot(x - ox, y - oy) < 24:
            continue
        if any(math.hypot(x - a, y - b) < 30 for a, b in pts):
            continue
        pts.append((x, y))

    base, amp = 84, 56
    curva = perfil_gaussiano(px, base, amp, sig)
    y_meio = base - amp * math.exp(-0.5)   # altura da curva em 1 desvio-padrão

    # seta reta: da borda da mãe até a borda do anel do filhote
    dx, dy = ox - px, oy - py
    d = math.hypot(dx, dy)
    ux, uy = dx / d, dy / d
    x1, y1 = px + ux * 11, py + uy * 11
    x2, y2 = ox - ux * 13, oy - uy * 13

    plantas = "\n".join(f'    <circle cx="{x:.1f}" cy="{y:.1f}" r="5"/>' for x, y in pts)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W * 2}" height="{H * 2}">
  <defs>
    <marker id="seta" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M0,0 L10,5 L0,10 z" fill="{COR}"/>
    </marker>
    <marker id="dupla" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="{MUTED}"/>
    </marker>
  </defs>

  <!-- campo (vista de cima) -->
  {campo(100, 136)}

  <!-- kernel 2D -->
  {contornos(px, py, sig, COR, 0.6, 0.3)}

  <!-- outras plantas -->
  <g fill="{FG}" fill-opacity="0.85">
{plantas}
  </g>

  <!-- perfil do kernel, pico em cima da mãe -->
  <line x1="{px - 115}" y1="{base}" x2="{px + 115}" y2="{base}" stroke="{MUTED}" stroke-opacity="0.6"/>
  <path d="{curva}" fill="none" stroke="{COR}" stroke-width="2.2" stroke-linejoin="round"/>
  <line x1="{px}" y1="{base - amp}" x2="{px}" y2="{py - 10}" stroke="{COR}" stroke-opacity="0.45" stroke-dasharray="2 4"/>
  <line x1="{px + 3}" y1="{y_meio:.1f}" x2="{px + sig - 3}" y2="{y_meio:.1f}" stroke="{MUTED}" stroke-width="1.2"
        marker-start="url(#dupla)" marker-end="url(#dupla)"/>
  {rotulo(M, "s", px + sig / 2, y_meio - 5, 13, MUTED)}
  {rotulo(M, r"\phi_D", px + 60, base - amp + 14, 17, COR)}

  <!-- dispersão: seta reta mãe -> filhote -->
  <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{COR}" stroke-width="2"
        stroke-dasharray="5 3" marker-end="url(#seta)"/>

  <!-- planta-mãe -->
  <circle cx="{px}" cy="{py}" r="8" fill="{FG}" stroke="{COR}" stroke-width="2.5"/>
  {rotulo(M, r"\mathbf{x}_i", px, py + 25, 15, FG)}

  <!-- filhote -->
  <circle cx="{ox}" cy="{oy}" r="6.5" fill="{FG}"/>
  <circle cx="{ox}" cy="{oy}" r="11" fill="none" stroke="{COR}" stroke-width="1.4" stroke-dasharray="2.5 2.5"/>
  {rotulo(M, r"\mathbf{x}", ox, oy + 26, 15, FG)}
</svg>'''


# --------------------------------------------------------------------------
# Figura 2: kernel de competição (morte)
# --------------------------------------------------------------------------
def figura_competicao(M):
    COR = COR_COMPETICAO
    H = 205
    cx, cy = 262, 138      # planta focal
    sig = 30               # 1 desvio-padrão (px)

    # vizinhos: (ângulo em graus, distância em px) a partir da focal
    vizinhos = [(165, 36), (20, 40), (110, 44), (-60, 42), (200, 72), (-14, 86), (58, 60)]
    nb = [(cx + d * math.cos(math.radians(a)), cy - d * math.sin(math.radians(a)), d) for a, d in vizinhos]

    # setas: espessura e opacidade proporcionais ao peso do kernel (mais perto = mais forte)
    setas = []
    for x, y, d in nb:
        k = math.exp(-d * d / (2 * sig * sig))
        ux, uy = (cx - x) / d, (cy - y) / d
        x1, y1 = x + ux * 8, y + uy * 8        # sai da borda do vizinho
        x2, y2 = cx - ux * 13, cy - uy * 13    # chega na borda da focal
        setas.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{COR}" '
                     f'stroke-width="{0.7 + 1.5 * k:.2f}" stroke-opacity="{0.35 + 0.65 * k:.2f}" marker-end="url(#seta)"/>')

    base, amp = 62, 46
    curva = perfil_gaussiano(cx, base, amp, sig)
    R, alt = 1.6 * sig, amp * 0.62             # top-hat (alternativa ao gaussiano)
    tophat = (f"M{cx - 105},{base} L{cx - R:.1f},{base} L{cx - R:.1f},{base - alt:.1f} "
              f"L{cx + R:.1f},{base - alt:.1f} L{cx + R:.1f},{base} L{cx + 105},{base}")

    jx, jy, _ = nb[5]                          # vizinho rotulado como x_j
    plantas = "\n".join(f'    <circle cx="{x:.1f}" cy="{y:.1f}" r="5"/>' for x, y, _ in nb)
    setas_svg = "\n  ".join(setas)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W * 2}" height="{H * 2}">
  <defs>
    <marker id="seta" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="4.5" markerHeight="4.5" orient="auto">
      <path d="M0,0 L10,5 L0,10 z" fill="{COR}"/>
    </marker>
  </defs>

  <!-- campo (vista de cima) -->
  {campo(76, 124)}

  <!-- kernel 2D -->
  {contornos(cx, cy, sig, COR)}

  <!-- perfil do kernel (contínua: gaussiana; tracejada: top-hat) -->
  <line x1="{cx - 115}" y1="{base}" x2="{cx + 115}" y2="{base}" stroke="{MUTED}" stroke-opacity="0.6"/>
  <path d="{tophat}" fill="none" stroke="{COR}" stroke-opacity="0.45" stroke-width="1.4" stroke-dasharray="4 3"/>
  <path d="{curva}" fill="none" stroke="{COR}" stroke-width="2.2" stroke-linejoin="round"/>
  <line x1="{cx}" y1="{base - amp}" x2="{cx}" y2="{cy - 10}" stroke="{COR}" stroke-opacity="0.4" stroke-dasharray="2 4"/>
  {rotulo(M, r"\phi_C", cx + 70, base - amp + 16, 17, COR)}

  <!-- competição: setas dos vizinhos para a focal -->
  {setas_svg}

  <!-- vizinhos -->
  <g fill="{FG}" fill-opacity="0.9">
{plantas}
  </g>
  {rotulo(M, r"\mathbf{x}_j", jx + 11, jy + 5, 14, FG, ancora="left")}

  <!-- planta focal -->
  <circle cx="{cx}" cy="{cy}" r="8" fill="{FG}" stroke="{COR}" stroke-width="2.5"/>
  {rotulo(M, r"\mathbf{x}_i", cx - 17, cy + 27, 15, FG)}
</svg>'''


# --------------------------------------------------------------------------
# PNG (opcional)
# --------------------------------------------------------------------------
def exportar_png(caminho_svg):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  (Playwright não instalado: PNG não gerado, só o SVG)")
        return
    svg = open(caminho_svg, encoding="utf-8").read()
    w, h = (int(v) for v in re.search(r'width="(\d+)" height="(\d+)"', svg).groups())
    caminho_png = caminho_svg[:-4] + ".png"
    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page(viewport={"width": w, "height": h})
        pagina.set_content(f'<body style="margin:0;background:transparent">{svg}</body>')
        pagina.screenshot(path=caminho_png, omit_background=True)
        navegador.close()
    print(f"  {caminho_png}")


# --------------------------------------------------------------------------
if __name__ == "__main__":
    os.makedirs(PASTA_SAIDA, exist_ok=True)
    M = renderizar_tex([r"\phi_D", r"\phi_C", r"\mathbf{x}_i", r"\mathbf{x}_j", r"\mathbf{x}", "s"])

    for nome, funcao in [("birth_dispersal", figura_dispersao),
                         ("competition_kernel", figura_competicao)]:
        caminho = os.path.join(PASTA_SAIDA, nome + ".svg")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(funcao(M))
        print(caminho)
        exportar_png(caminho)
