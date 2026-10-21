"""
Trajetória de um processo de Ornstein-Uhlenbeck 2D (animal residente em área de vida).

Atualização exata em passos discretos:
    x(t + dt) = x(t) e^{-dt/tau} + mu (1 - e^{-dt/tau}) + sigma_r sqrt(1 - e^{-2 dt/tau}) Z,
    Z ~ N(0, I)  (independente em x e y)

Saída: SVG com fundo transparente, sem eixos, bordas ou legenda.
    - marcador de mu (estilo em ESTILO_MU) = centro da área de vida
    - quadradinho                          = posição final do animal
"""

import uuid

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import matplotlib.patheffects as pe

# ----------------------------------------------------------------------------
# Parâmetros do modelo
# ----------------------------------------------------------------------------
TAU      = 1.                 # tempo médio de travessia da área de vida
SIGMA_R  = 1.0                 # escala espacial da área de vida
MU       = np.array([0.0, 0.0])  # centro da área de vida
DT       = 0.01                # passo de tempo
T_FINAL  = 100.0                # tempo final  <-- ajuste aqui
SEMENTE  = None              # None = aleatória a cada execução; um número = trajetória fixa

# Posição inicial: None = sorteia da distribuição estacionária N(mu, sigma_r^2 I)
X0 = None

# ----------------------------------------------------------------------------
# Aparência
# ----------------------------------------------------------------------------
ARQUIVO        = "trajetoria_ou.svg"
COR_TRAJETORIA = "#7ee787"     # verde (mesma cor do nascimento nos slides)
COR_ANIMAL     = "#8be9fd"     # ciano: contrasta com o verde do rastro
COR_MU         = "#f1fa8c"     # amarelo: centro da área de vida
COR_FUNDO      = "#191919"     # fundo do slide (usado no contorno escuro dos marcadores)
CONTORNO       = 1.5           # espessura do contorno escuro que separa os marcadores do rastro
AREA_VIDA      = 0.0           # desenha o círculo da área de vida com raio AREA_VIDA * sigma_r (0 = não desenha)
LARGURA_LINHA  = 1.2
ESMAECER       = True          # True: trecho mais antigo mais transparente
ALFA_MIN       = 0.08          # opacidade do começo do rastro (se ESMAECER)
TAM_MU         = 380           # tamanho do marcador de mu (pontos^2, como no scatter)
ESTILO_MU      = "clareira"    # "clareira", "alvo", "mira", "estrela" ou "losango"
RAIO_CLAREIRA  = 0.28          # raio da clareira em unidades de sigma_r (estilo "clareira")
TAM_QUADRADO   = 110           # tamanho do quadradinho final
TAMANHO_FIG    = 4.0           # lado da figura em polegadas


def simular_ou(tau, sigma_r, mu, dt, t_final, x0=None, semente=None):
    """Simula o OU 2D com a solução exata em passos discretos. Devolve (N+1, 2)."""
    rng = np.random.default_rng(semente)
    n = int(round(t_final / dt))
    a = np.exp(-dt / tau)                        # fator de memória
    s = sigma_r * np.sqrt(1.0 - a * a)           # desvio-padrão do ruído por passo

    x = np.empty((n + 1, 2))
    x[0] = mu + sigma_r * rng.standard_normal(2) if x0 is None else x0
    z = rng.standard_normal((n, 2))
    for k in range(n):
        x[k + 1] = x[k] * a + mu * (1.0 - a) + s * z[k]
    return x


def marcar_centro(ax, mu, estilo):
    """Desenha o centro da área de vida (mu) com o estilo escolhido."""
    halo = [pe.Stroke(linewidth=6, foreground=COR_FUNDO), pe.Normal()]

    if estilo == "clareira":
        # disco da cor do fundo que "abre" o rastro em volta de mu, com um ponto no meio
        ax.add_patch(plt.Circle(mu, RAIO_CLAREIRA * SIGMA_R, color=COR_FUNDO, alpha=0.9,
                                linewidth=0, zorder=2))
        ax.add_patch(plt.Circle(mu, RAIO_CLAREIRA * SIGMA_R, fill=False, edgecolor=COR_MU,
                                linewidth=1.4, zorder=2.5))
        ax.scatter(*mu, s=TAM_MU * 0.25, color=COR_MU, linewidths=0, zorder=3)

    elif estilo == "alvo":
        # anel + ponto (símbolo de alvo), com contorno escuro
        ax.scatter(*mu, s=TAM_MU, facecolor=COR_FUNDO, edgecolor=COR_MU, linewidths=2.2, zorder=3)
        ax.scatter(*mu, s=TAM_MU * 0.18, color=COR_MU, linewidths=0, zorder=3.5)

    elif estilo == "mira":
        # quatro traços com um vão no centro + ponto, todos com contorno escuro
        r_in, r_out = 0.10 * SIGMA_R, 0.38 * SIGMA_R
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            ax.plot([mu[0] + dx * r_in, mu[0] + dx * r_out], [mu[1] + dy * r_in, mu[1] + dy * r_out],
                    color=COR_MU, linewidth=2.4, solid_capstyle="round", path_effects=halo, zorder=3)
        ax.scatter(*mu, s=TAM_MU * 0.12, color=COR_MU, edgecolor=COR_FUNDO, linewidths=1.5, zorder=3.5)

    elif estilo == "losango":
        ax.scatter(*mu, s=TAM_MU * 0.6, marker="D", color=COR_MU,
                   edgecolor=COR_FUNDO, linewidths=CONTORNO, zorder=3)

    else:  # "estrela"
        ax.scatter(*mu, s=TAM_MU, marker="*", color=COR_MU,
                   edgecolor=COR_FUNDO, linewidths=CONTORNO, zorder=3)


def desenhar(x, mu, arquivo):
    fig, ax = plt.subplots(figsize=(TAMANHO_FIG, TAMANHO_FIG))

    # trajetória
    pontos = x.reshape(-1, 1, 2)
    segmentos = np.concatenate([pontos[:-1], pontos[1:]], axis=1)
    if ESMAECER:
        alfas = np.linspace(ALFA_MIN, 1.0, len(segmentos))
        cores = np.tile(matplotlib.colors.to_rgba(COR_TRAJETORIA), (len(segmentos), 1))
        cores[:, 3] = alfas
    else:
        cores = COR_TRAJETORIA
    ax.add_collection(LineCollection(segmentos, colors=cores, linewidths=LARGURA_LINHA,
                                     capstyle="round", joinstyle="round", zorder=1))

    # área de vida: círculo tracejado em volta de mu
    if AREA_VIDA > 0:
        ax.add_patch(plt.Circle(mu, AREA_VIDA * SIGMA_R, fill=False, linestyle=(0, (4, 4)),
                                edgecolor=COR_MU, alpha=0.45, linewidth=1.2, zorder=0))

    # centro da área de vida
    marcar_centro(ax, mu, ESTILO_MU)

    # posição final do animal: quadrado preenchido com contorno escuro
    ax.scatter(*x[-1], s=TAM_QUADRADO, marker="s", color=COR_ANIMAL,
               edgecolor=COR_FUNDO, linewidths=CONTORNO, zorder=4)

    # sem eixos, bordas, margens ou legenda; mesma escala em x e y
    ax.set_aspect("equal")
    ax.autoscale_view()
    ax.margins(0.03)
    ax.set_axis_off()
    fig.subplots_adjust(0, 0, 1, 1)

    fig.savefig(arquivo, format="svg", transparent=True,
                bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


# ----------------------------------------------------------------------------
# Versão animada (SVG com animação embutida: roda em qualquer navegador, sem vídeo)
# ----------------------------------------------------------------------------
ANIMAR          = True                       # também gera a versão animada
ARQUIVO_ANIMADO = "trajetoria_ou_animada.svg"
VELOCIDADE      = 0.4                    # unidades de tempo do modelo por segundo de animação
                                             # (com TAU = 1: 1 tempo de travessia por segundo).
                                             # A duração é T_FINAL / VELOCIDADE: aumentar T_FINAL
                                             # deixa a animação mais longa, não mais rápida.
PAUSA           = 2.0                        # segundos parada no fim antes de recomeçar
REPETIR         = True                       # False: desenha uma vez e para no final


def svg_animado(x, mu, largura=None):
    """Devolve o texto de um SVG em que o rastro vai sendo desenhado e o animal (quadrado)
    percorre a trajetória. O centro da área de vida aparece fixo desde o início (anel + ponto).

    largura: None = tamanho fixo (para salvar em arquivo); "100%" = ocupa a largura do lugar
             onde for colocado (para usar direto num slide, dentro de uma célula de Python)."""
    pad = 0.05
    xmin, ymin = x.min(axis=0)
    xmax, ymax = x.max(axis=0)
    xmin, xmax = min(xmin, mu[0]), max(xmax, mu[0])
    ymin, ymax = min(ymin, mu[1]), max(ymax, mu[1])
    ext = max(xmax - xmin, ymax - ymin)
    xmin, xmax = xmin - pad * ext, xmax + pad * ext
    ymin, ymax = ymin - pad * ext, ymax + pad * ext
    W, H = xmax - xmin, ymax - ymin

    # SVG tem o eixo y para baixo: espelha y
    def p(px, py):
        return f"{px - xmin:.4f},{ymax - py:.4f}"

    caminho = "M" + " L".join(p(px, py) for px, py in x)

    # tempo: cada passo DT da simulação dura DT / VELOCIDADE segundos na animação
    duracao = (len(x) - 1) * DT / VELOCIDADE
    # posição do animal a cada passo (intervalos de tempo iguais = tempo real do modelo)
    posicoes = ";".join(p(px, py) for px, py in x)
    # quanto do rastro já foi desenhado a cada passo (fração do comprimento total)
    comp = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(x, axis=0), axis=1))])
    restante = ";".join(f"{v:.5f}" for v in 1.0 - comp / comp[-1])
    lw = 0.0045 * ext                              # espessura proporcional ao tamanho do desenho
    lado = 0.035 * ext                             # quadrado do animal
    r_mu = 0.035 * ext                             # anel do centro de vida
    mx, my = p(*mu).split(",")

    # id único: permite ter mais de uma animação na mesma página
    ident = "desenho" + uuid.uuid4().hex[:8]
    inicio = f"0s;{ident}.end+{PAUSA:.1f}s" if REPETIR else "0s"

    if largura is None:
        tamanho = f'width="{400 * W / ext:.0f}" height="{400 * H / ext:.0f}"'
    else:
        tamanho = f'width="{largura}" style="height: auto;"'

    return f'''<svg xmlns="http://www.w3.org/2000/svg" class="animada" viewBox="0 0 {W:.4f} {H:.4f}" {tamanho}>
  <!-- rastro: desenhado progressivamente (stroke-dashoffset vai de 1 a 0) -->
  <path d="{caminho}" fill="none" stroke="{COR_TRAJETORIA}" stroke-width="{lw:.4f}"
        stroke-linejoin="round" stroke-linecap="round" pathLength="1"
        stroke-dasharray="1 1" stroke-dashoffset="1">
    <animate id="{ident}" attributeName="stroke-dashoffset" values="{restante}"
             calcMode="linear" dur="{duracao:.3f}s" begin="{inicio}" fill="freeze"/>
  </path>

  <!-- centro da área de vida -->
  <circle cx="{mx}" cy="{my}" r="{r_mu:.4f}" fill="{COR_FUNDO}" stroke="{COR_MU}" stroke-width="{1.6 * lw:.4f}"/>
  <circle cx="{mx}" cy="{my}" r="{0.38 * r_mu:.4f}" fill="{COR_MU}"/>

  <!-- animal: percorre a trajetória no tempo do modelo, junto com a ponta do rastro -->
  <rect x="{-lado / 2:.4f}" y="{-lado / 2:.4f}" width="{lado:.4f}" height="{lado:.4f}"
        fill="{COR_ANIMAL}" stroke="{COR_FUNDO}" stroke-width="{0.8 * lw:.4f}">
    <animateMotion values="{posicoes}" calcMode="linear" dur="{duracao:.3f}s"
                   begin="{ident}.begin" fill="freeze"/>
  </rect>
</svg>'''


def salvar_svg_animado(x, mu, arquivo):
    with open(arquivo, "w", encoding="utf-8") as f:
        f.write(svg_animado(x, mu))


if __name__ == "__main__":
    # se a semente for aleatória, sorteia uma e mostra, para poder repetir a trajetória depois
    semente = SEMENTE if SEMENTE is not None else int(np.random.SeedSequence().entropy % 2**32)
    traj = simular_ou(TAU, SIGMA_R, MU, DT, T_FINAL, X0, semente)
    desenhar(traj, MU, ARQUIVO)
    print(f"{ARQUIVO}: {len(traj) - 1} passos, t = 0 a {T_FINAL}, semente = {semente}")
    if ANIMAR:
        salvar_svg_animado(traj, MU, ARQUIVO_ANIMADO)
        print(f"{ARQUIVO_ANIMADO}: animação de {T_FINAL / VELOCIDADE:.1f} s")
