# harmonic_phase_portrait.png  谐振子相图（稳定平衡：椭圆，中心）与倒置谐振子（不稳定平衡：双曲线，鞍点）
# 用于 微扰和摄动理论.md “微小振动近似的适用范围”一节中对相图的简介
import os
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

for f in font_manager.findSystemFonts():
    if "NotoSansCJK-Regular" in f:
        font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": ["Noto Sans CJK SC"], "mathtext.fontset": "cm",
                     "axes.unicode_minus": False, "font.size": 11, "savefig.dpi": 220})
OUT = os.path.dirname(os.path.abspath(__file__)) + "/"
BLUE = "#1f4e9c"; RED = "#c8102e"; ORANGE = "#e08a00"; GREEN = "#2e7d32"; GRAY = "#777777"


def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def arrow_on(ax, x, y, i, color):
    ax.annotate("", xy=(x[i + 1], y[i + 1]), xytext=(x[i], y[i]),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.4, mutation_scale=14))


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.2, 4.4))

# (a) stable: x = a cos(wt), v = -a w sin(wt)
w = 1.5
ph = np.linspace(0, 2 * np.pi, 400)
for a in (0.4, 0.8, 1.2, 1.6):
    x, v = a * np.cos(ph), -a * w * np.sin(ph)
    ax1.plot(x, v, color=BLUE, lw=1.5)
    k = 40
    arrow_on(ax1, x, v, k, BLUE)
    arrow_on(ax1, x, v, k + 200, BLUE)
ax1.plot([0], [0], "o", color=BLUE, ms=6)
a, t0 = 1.2, 0.75
xp, vp = a * np.cos(t0), -a * w * np.sin(t0)
ax1.plot([xp], [vp], "o", color=RED, ms=8, zorder=5)
ax1.plot([xp, xp], [0, vp], color=RED, lw=0.9, ls=":")
ax1.plot([0, xp], [vp, vp], color=RED, lw=0.9, ls=":")
ax1.text(xp + 0.08, vp - 0.12, "相点 $(\\bar x,\\dot{\\bar x})$", color=RED, fontsize=10.5, va="top")
ax1.annotate("半轴 $a$", xy=(1.2, 0), xytext=(1.45, 0.55), fontsize=10, color=GRAY, bbox=dict(fc="white", ec="none", alpha=0.9, pad=1.5),
             arrowprops=dict(arrowstyle="->", color=GRAY, lw=0.8))
ax1.annotate("半轴 $a\\omega$", xy=(0, 1.8), xytext=(0.35, 2.2), fontsize=10, color=GRAY, bbox=dict(fc="white", ec="none", alpha=0.9, pad=1.5),
             arrowprops=dict(arrowstyle="->", color=GRAY, lw=0.8))
ax1.text(0.08, -0.22, "中心", color=BLUE, fontsize=10, bbox=dict(fc="white", ec="none", alpha=0.9, pad=1.5))
ax1.axhline(0, color=GRAY, lw=0.5); ax1.axvline(0, color=GRAY, lw=0.5)
ax1.set(xlim=(-2.0, 2.1), ylim=(-2.65, 2.65), xlabel="$\\bar x$", ylabel="$\\dot{\\bar x}$")
ax1.set_title("(a) 稳定平衡 $k>0$：同心椭圆，顺时针运动", loc="left", fontsize=11)
clean(ax1)

# (b) unstable: (1/2) v^2 - (1/2) kappa^2 x^2 = E
kap = 1.0
s = np.linspace(-1.6, 1.6, 400)
for E in (0.15, 0.6, 1.2):
    r = np.sqrt(2 * E)
    smax = np.arccosh(4.0 / r)
    s = np.linspace(-smax, smax, 400)
    for sx in (1, -1):              # E > 0: branches crossing x = 0 (v = ±r cosh)
        x, v = (r / kap) * np.sinh(s), sx * r * np.cosh(s)
        x, v = (x, v) if sx > 0 else (x[::-1], v[::-1])
        ax2.plot(x, v, color=GREEN, lw=1.4); arrow_on(ax2, x, v, 270, GREEN)
    for sx in (1, -1):              # E < 0: branches crossing v = 0
        x, v = sx * (r / kap) * np.cosh(s), r * np.sinh(s)
        x, v = (x, v) if sx > 0 else (x, v[::-1])
        ax2.plot(x, v, color=ORANGE, lw=1.4); arrow_on(ax2, x, v, 270, ORANGE)
xx = np.linspace(-2.6, 2.6, 2)
ax2.plot(xx, kap * xx, color=RED, lw=1.6)
ax2.plot(xx, -kap * xx, color=RED, lw=1.6, ls="--")
ax2.text(1.15, 2.4, "$\\dot{\\bar x}=\\kappa\\bar x$：远离", color=RED, fontsize=10, bbox=dict(fc="white", ec="none", alpha=0.9, pad=1.5))
ax2.text(1.05, -2.5, "$\\dot{\\bar x}=-\\kappa\\bar x$：趋近", color=RED, fontsize=10, bbox=dict(fc="white", ec="none", alpha=0.9, pad=1.5))
ax2.plot([0], [0], "o", color=RED, ms=6)
ax2.text(0.1, -0.35, "鞍点", color=RED, fontsize=10, bbox=dict(fc="white", ec="none", alpha=0.9, pad=1.5))
ax2.axhline(0, color=GRAY, lw=0.5); ax2.axvline(0, color=GRAY, lw=0.5)
ax2.set(xlim=(-2.6, 2.6), ylim=(-2.65, 2.65), xlabel="$\\bar x$", ylabel="$\\dot{\\bar x}$")
ax2.set_title("(b) 不稳定平衡 $k<0$：双曲线，相点被推离", loc="left", fontsize=11)
clean(ax2)

fig.tight_layout()
fig.savefig(OUT + "harmonic_phase_portrait.png", bbox_inches="tight", facecolor="white")
print("harmonic_phase_portrait.png")
