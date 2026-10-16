# Figures for 微扰和摄动理论.md, section "能量"（谐振子的经典与量子能量）
#   quantum_levels.png       经典连续能量 vs 量子分立能级 vs n 很大时的“准连续”
#   quantum_phase_space.png  相空间：经典椭圆轨道 vs 面积为 h 的量子化环带
#   quantum_probability.png  概率分布：量子 |psi_n|^2 与经典 1/(pi sqrt(a^2-x^2)) 的比较
# 无量纲单位：x 以 x0 = sqrt(hbar/(m omega)) 为单位，p 以 p0 = sqrt(m hbar omega) 为单位，
# 能量以 hbar*omega 为单位。于是 U = x^2/2，经典振幅 A = sqrt(2E)，量子能级 E_n = n + 1/2。
import os
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, Rectangle

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


# ---------------- Fig 1: energy levels ----------------
fig, axs = plt.subplots(1, 3, figsize=(12.5, 4.0), gridspec_kw=dict(width_ratios=[1, 1, 1.45]))
x = np.linspace(-4.2, 4.2, 400)

# (a) classical
ax = axs[0]
Emax = 7.5
xx = np.linspace(-np.sqrt(2 * Emax), np.sqrt(2 * Emax), 400)
ax.fill_between(xx, xx**2 / 2, Emax, color=BLUE, alpha=0.10, lw=0)
ax.plot(x, x**2 / 2, color=BLUE, lw=1.8)
E0 = 3.3; A = np.sqrt(2 * E0)
ax.plot([-A, A], [E0, E0], color=RED, lw=2)
ax.plot([-A, A], [E0, E0], "o", color=RED, ms=4)
ax.annotate("", xy=(-A, -0.35), xytext=(A, -0.35),
            arrowprops=dict(arrowstyle="<->", color=RED, lw=1))
ax.text(0, -0.75, "振幅 $a$ 可连续变化", color=RED, ha="center", va="top", fontsize=9.5)
ax.text(A + 0.15, E0 + 0.15, "$E=\\frac{1}{2} m\\omega^2 a^2$", color=RED, fontsize=11)
ax.text(-A - 0.25, E0 + 0.1, "折返点", color=RED, fontsize=8.5, ha="right", va="bottom")
ax.text(0, 6.2, "阴影区内任何\n能量都允许", color=BLUE, ha="center", fontsize=9.5)
ax.set_title("(a) 经典：$E$ 可取任意非负值", fontsize=11.5)

# (b) quantum
ax = axs[1]
ax.plot(x, x**2 / 2, color=BLUE, lw=1.8)
for n in range(7):
    En = n + 0.5; An = np.sqrt(2 * En)
    ax.plot([-An, An], [En, En], color=ORANGE, lw=1.8)
    ax.text(An + 0.15, En, f"$n={n}$", fontsize=9, va="center", color=ORANGE)
ax.annotate("", xy=(-0.6, 3.5), xytext=(-0.6, 4.5),
            arrowprops=dict(arrowstyle="<->", color=GREEN, lw=1.2))
ax.text(-0.75, 4.0, "$\\hbar\\omega$", color=GREEN, ha="right", va="center", fontsize=11)
ax.annotate("", xy=(0, 0), xytext=(0, 0.5),
            arrowprops=dict(arrowstyle="<->", color=GREEN, lw=1.2, shrinkA=0, shrinkB=0))
ax.text(0.15, -0.55, "零点能 $\\frac{1}{2}\\hbar\\omega$", color=GREEN, fontsize=9, va="center")
ax.set_title("(b) 量子：$E_n=(n+\\frac{1}{2})\\hbar\\omega$", fontsize=11.5)

for ax in axs[:2]:
    ax.set_xlim(-4.6, 4.6); ax.set_ylim(-1.4, 7.6)
    ax.set_xlabel("$x$"); ax.set_ylabel("能量")
    ax.set_xticks([]); ax.set_yticks([]); clean(ax)
    ax.axhline(0, color="k", lw=0.6)

# (c) many levels
ax = axs[2]
N = 400
xc = np.linspace(-30, 30, 600)
for n in range(N):
    En = n + 0.5; An = np.sqrt(2 * En)
    ax.plot([-An, An], [En, En], color=ORANGE, lw=0.35)
ax.plot(xc, xc**2 / 2, color=BLUE, lw=1.6)
ax.set_xlim(-31, 72); ax.set_ylim(-10, N + 10)
ax.set_xticks([]); ax.set_xlabel("$x$")
ax.set_ylabel("$E/\\hbar\\omega$"); clean(ax)
ax.set_title("(c) 前 400 条能级：远看几乎连续", fontsize=11.5)
# zoom box
y0, h = 300, 6
ax.add_patch(Rectangle((-6, y0 - h / 2), 12, h, fill=False, ec=RED, lw=1.2, zorder=5))
ins = ax.inset_axes([0.66, 0.40, 0.30, 0.42])
for n in range(y0 - 6, y0 + 6):
    En = n + 0.5
    ins.plot([-6, 6], [En, En], color=ORANGE, lw=1.4)
ins.set_xlim(-6, 6); ins.set_ylim(y0 - h / 2, y0 + h / 2)
ins.set_xticks([]); ins.set_yticks([])
for s in ins.spines.values():
    s.set_color(RED)
ins.set_title("放大红框：仍然分立，\n但 $\\Delta E/E\\approx1/300$", fontsize=9, color=RED)
ax.annotate("", xy=(37, y0 - 15), xytext=(7, y0),
            arrowprops=dict(arrowstyle="->", color=RED, lw=1))
fig.tight_layout(w_pad=2.0)
fig.savefig(OUT + "quantum_levels.png", bbox_inches="tight", facecolor="white")
plt.close(fig)

# ---------------- Fig 2: phase space ----------------
fig, axs = plt.subplots(1, 2, figsize=(10.0, 4.6))
# (a) classical ellipse in physical units
ax = axs[0]
for a, c, lw in [(1.6, BLUE, 2.0), (2.15, GRAY, 0.8)]:
    ax.add_patch(Ellipse((0, 0), 2 * a, 2 * 0.7 * a, fill=(c == BLUE), fc=BLUE if c == BLUE else "none",
                         alpha=0.12 if c == BLUE else 1, ec="none" if c == BLUE else c, lw=lw,
                         ls="-" if c == BLUE else "--"))
    if c == BLUE:
        ax.add_patch(Ellipse((0, 0), 2 * a, 2 * 0.7 * a, fill=False, ec=BLUE, lw=2))
a = 1.6; b = 0.7 * a
th = np.deg2rad(40)
ax.annotate("", xy=(a * np.cos(th - 0.25), -b * np.sin(th - 0.25) * -1),
            xytext=(a * np.cos(th), b * np.sin(th)),
            arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=1.6, mutation_scale=14))
ax.plot([0, a], [0, 0], color=RED, lw=1.2); ax.text(a / 2, -0.17, "$a$", color=RED, ha="center", va="top")
ax.plot([0, 0], [0, b], color=RED, lw=1.2); ax.text(0.08, b / 2, "$m\\omega a$", color=RED, va="center")
ax.text(-0.6, -0.5, "面积\n$\\pi m\\omega a^2=\\dfrac{2\\pi E}{\\omega}$", color=BLUE, ha="center", fontsize=10)
ax.text(2.4, 1.75, "更大的 $E$（虚线）\n或更小的 $E$ 同样允许", color=GRAY, fontsize=9, ha="right")
ax.set_title("(a) 经典：相轨道是椭圆，大小任意", fontsize=11.5)
ax.set_xlabel("位置 $x$"); ax.set_ylabel("动量 $p=m\\dot x$")
lim = 2.5

# (b) quantum rings (dimensionless: circles)
ax2 = axs[1]
nmax = 6
for n in reversed(range(nmax)):
    R = np.sqrt(2 * (n + 1))
    ax2.add_patch(Circle((0, 0), R, fc=(BLUE if n % 2 == 0 else "white"), alpha=0.13 if n % 2 == 0 else 1,
                         ec="none"))
for n in range(nmax):
    R = np.sqrt(2 * (n + 1))
    ax2.add_patch(Circle((0, 0), R, fill=False, ec=BLUE, lw=0.7))
    r = np.sqrt(2 * n + 1)
    ax2.add_patch(Circle((0, 0), r, fill=False, ec=ORANGE, lw=1.6, ls="-"))
for n in range(4):
    r = np.sqrt(2 * n + 1)
    ang = np.deg2rad(-90 + 27 * n)
    ax2.text(r * np.cos(ang), r * np.sin(ang), f"$n={n}$", fontsize=8, color=ORANGE,
             ha="center", va="center", bbox=dict(fc="white", ec="none", pad=0.4))
ax2.annotate("每个环带面积 = $h$", xy=(-np.sqrt(5) * 0.72, np.sqrt(5) * 0.69),
             xytext=(-3.9, 3.9), fontsize=10, color=BLUE,
             arrowprops=dict(arrowstyle="->", color=BLUE, lw=1))
ax2.annotate("允许的轨道：所围面积\n$=(n+\\frac{1}{2})h$", xy=(np.sqrt(11) * np.cos(-0.25), np.sqrt(11) * np.sin(-0.25)),
             xytext=(2.0, -4.25), fontsize=10, color=ORANGE, va="center",
             arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1))
ax2.set_title("(b) 量子：只允许“面积”为 $(n+\\frac{1}{2})h$ 的轨道", fontsize=11.5)
ax2.set_xlabel("$x/x_0$"); ax2.set_ylabel("$p/p_0$")
for ax_, L in [(ax, lim), (ax2, 4.7)]:
    ax_.set_xlim(-L, L); ax_.set_ylim(-L, L); ax_.set_aspect("equal")
    ax_.axhline(0, color="k", lw=0.5); ax_.axvline(0, color="k", lw=0.5)
    ax_.set_xticks([]); ax_.set_yticks([]); clean(ax_)
fig.tight_layout(w_pad=3)
fig.savefig(OUT + "quantum_phase_space.png", bbox_inches="tight", facecolor="white")
plt.close(fig)


# ---------------- Fig 3: probability densities ----------------
def psi(n, xi):
    """Normalized harmonic-oscillator eigenfunction via stable recurrence."""
    p0 = np.pi**-0.25 * np.exp(-xi**2 / 2)
    if n == 0:
        return p0
    p1 = np.sqrt(2) * xi * p0
    for k in range(1, n):
        p0, p1 = p1, np.sqrt(2 / (k + 1)) * xi * p1 - np.sqrt(k / (k + 1)) * p0
    return p1


fig, axs = plt.subplots(1, 3, figsize=(12, 3.6))
for ax, n in zip(axs, [0, 3, 30]):
    A = np.sqrt(2 * n + 1)
    L = A + 2.2
    xi = np.linspace(-L, L, 4000)
    P = psi(n, xi)**2
    ax.fill_between(xi, P, color=BLUE, alpha=0.18, lw=0)
    ax.plot(xi, P, color=BLUE, lw=1.0 if n == 30 else 1.6, label="量子 $|\\psi_n(x)|^2$")
    xc = np.linspace(-A * 0.9995, A * 0.9995, 2000)
    Pc = 1 / (np.pi * np.sqrt(A**2 - xc**2))
    ax.plot(xc, Pc, color=RED, lw=1.8, ls="--", label="经典 $P(x)$")
    top = max(P.max(), 1 / (np.pi * A)) * 1.35 if n < 30 else 0.30
    for s in (-1, 1):
        ax.axvspan(s * A, s * L, color=GRAY, alpha=0.12, lw=0)
        ax.axvline(s * A, color=GRAY, lw=0.8, ls=":")
    ax.set_xlim(-L, L); ax.set_ylim(0, top)
    ax.set_yticks([]); clean(ax)
    ax.set_xticks([-A, 0, A]); ax.set_xticklabels(["$-a$", "0", "$a$"])
    ax.set_title(f"$n={n}$", fontsize=12)
    if n == 0:
        ax.text(0.98, 0.95, "灰色：经典禁区\n（$|x|>a$）", transform=ax.transAxes, ha="right", va="top",
                fontsize=8.5, color=GRAY)
        ax.annotate("量子：\n中心最可能", xy=(-0.25, P.max()*0.97), xytext=(-A - 0.2, P.max() * 0.95), color=BLUE, ha="right", va="center", fontsize=9, arrowprops=dict(arrowstyle="->", color=BLUE, lw=0.9))
        ax.annotate("经典：\n折返点附近\n最可能", xy=(A * 0.85, 1 / (np.pi * A * np.sqrt(1 - 0.85**2))), xytext=(A + 0.25, P.max() * 0.62), color=RED, ha="left", va="center", fontsize=8.5, arrowprops=dict(arrowstyle="->", color=RED, lw=0.9))
    if n == 30:
        ax.legend(loc="upper center", fontsize=9, frameon=False, ncol=2)
        ax.text(0, 0.035, "局部平均后与经典曲线重合", color=GREEN, ha="center", fontsize=9,
                bbox=dict(fc="white", ec="none", alpha=0.8, pad=1))
fig.tight_layout(w_pad=2)
fig.savefig(OUT + "quantum_probability.png", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("done")
