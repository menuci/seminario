"""
Trajetória de um processo de Ornstein-Uhlenbeck 2D (animal residente em área de vida).

Atualização exata em passos discretos:
    x(t + dt) = x(t) e^{-dt/tau} + mu (1 - e^{-dt/tau}) + sigma_r sqrt(1 - e^{-2 dt/tau}) Z,
    Z ~ N(0, I)  (independente em x e y)

Saída: SVG com fundo transparente, sem eixos, bordas ou legenda.
    - marcador de mu (estilo em ESTILO_MU) = centro da área de vida
    - quadradinho                          = posição final do animal
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import matplotlib.patheffects as pe

# ----------------------------------------------------------------------------
# Parâmetros do modelo
# ----------------------------------------------------------------------------
TAU      = 1.0                 # tempo médio de travessia da área de vida
SIGMA_R  = 1.0                 # escala espacial da área de vida
MU       = np.array([0.0, 0.0])  # centro da área de vida
DT       = 0.01                # passo de tempo
T_FINAL  = 40.0                # tempo final  <-- ajuste aqui
SEMENTE  = None                  # semente aleatória (mesmo número = mesma trajetória)

# Posição inicial: None = sorteia da distribuição estacionária N(mu, sigma_r^2 I)
X0 = None

# ----------------------------------------------------------------------------
# Aparência
# ----------------------------------------------------------------------------
ARQUIVO        = "trajetoria_ou.svg"
COR_TRAJETORIA = "#7ee787"     # verde (mesma cor do nascimento nos slides)
COR_ANIMAL     = "#8be9fd"     # rosa: contrasta com o verde do rastro
COR_MU         = "#f1fa8c"     # amarelo: centro da área de vida
COR_FUNDO      = "#191919"     # fundo do slide (usado no contorno escuro dos marcadores)
CONTORNO       = 1.5           # espessura do contorno escuro que separa os marcadores do rastro
AREA_VIDA      = 0.0           # desenha o círculo da área de vida com raio AREA_VIDA * sigma_r (0 = não desenha)
LARGURA_LINHA  = 1.2
ESMAECER       = True          # True: trecho mais antigo mais transparente
ALFA_MIN       = 0.08          # opacidade do começo do rastro (se ESMAECER)
TAM_MU         = 180           # tamanho do marcador de mu (pontos^2, como no scatter)
ESTILO_MU      = "alvo"    # "clareira", "alvo", "mira", "estrela" ou "losango"
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


if __name__ == "__main__":
    traj = simular_ou(TAU, SIGMA_R, MU, DT, T_FINAL, X0, SEMENTE)
    desenhar(traj, MU, ARQUIVO)
    print(f"{ARQUIVO}: {len(traj) - 1} passos, t = 0 a {T_FINAL}")
