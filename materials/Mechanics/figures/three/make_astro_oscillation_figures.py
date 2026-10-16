# Figures for 微扰和摄动理论.md「天体物理应用」小节
#   kirkwood_gaps.png    小行星半长轴分布与木星平运动共振（真实数据：Lowell astorb 子集，经 CRAN 包 Dimodal）
#   bh_ringdown.png      黑洞铃宕：低 Q 的阻尼振动；准正规模频率与质量的关系
#   hubble_friction.png  膨胀宇宙中的标量场：过阻尼→欠阻尼
#   io_forced_ecc.png    木卫一：拉普拉斯共振与受迫偏心率
import os
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Circle, FancyArrowPatch
from scipy.special import jv, gamma as Gamma

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


# ---------------- Fig 1: Kirkwood gaps ----------------
try:
    import rdata
    a_ast = np.asarray(rdata.read_rda(OUT + "kirkwood.rda")["kirkwood"], float)
except Exception:  # fallback: plain text copy
    a_ast = np.loadtxt(OUT + "kirkwood_a.txt")
aJ = 5.2026
fig, ax = plt.subplots(figsize=(9.5, 3.9))
bins = np.arange(1.9, 4.25, 0.02)
ax.hist(a_ast, bins=bins, color=BLUE, alpha=0.75, lw=0)
res = [("4:1", 4, 1), ("3:1", 3, 1), ("5:2", 5, 2), ("7:3", 7, 3), ("2:1", 2, 1), ("3:2", 3, 2)]
ymax = 125
for lab, p, q in res:
    ar = aJ * (q / p) ** (2 / 3)
    c = GREEN if lab == "3:2" else RED
    ax.axvline(ar, color=c, ls="--", lw=1.1)
    ax.text(ar, ymax * 0.97, lab, color=c, ha="center", va="bottom", fontsize=10,
            bbox=dict(fc="white", ec="none", pad=0.5))
ax.text(3.85, 32, "希尔达群\n（3:2 共振处\n反而聚集）", color=GREEN, ha="right", fontsize=9)
ax.text(2.50, 70, "空隙", color=RED, ha="center", fontsize=9.5)
ax.set_xlim(1.9, 4.2); ax.set_ylim(0, ymax * 1.08)
ax.set_xlabel("半长轴 $a$ (AU)"); ax.set_ylabel("小行星数目（每 0.02 AU）")
clean(ax)
sec = ax.secondary_xaxis("top", functions=(lambda a: (aJ / np.maximum(a, 1e-3)) ** 1.5,
                                            lambda r: aJ / np.maximum(r, 1e-3) ** (2 / 3)))
sec.set_xticks([4, 3, 2.5, 2, 1.5]); sec.set_xlabel("木星周期 / 小行星周期  $P_{\\rm J}/P=n/n_{\\rm J}$", fontsize=10)
ax.text(0.005, -0.25, f"数据：Lowell Observatory astorb 数据库中 {len(a_ast)} 颗有直径测量的小行星（经 R 包 Dimodal 整理）",
        transform=ax.transAxes, fontsize=8, color=GRAY)
fig.savefig(OUT + "kirkwood_gaps.png", bbox_inches="tight", facecolor="white"); plt.close(fig)

# ---------------- Fig 2: black-hole ringdown ----------------
tsun = 4.925491e-6  # G Msun / c^3 [s]
def qnm220(j):  # Berti, Cardoso & Will (2006) fits: M*omega_R and Q for (l,m,n)=(2,2,0)
    w = 1.5251 - 1.1568 * (1 - j) ** 0.1292
    Q = 0.7000 + 1.4187 * (1 - j) ** -0.4990
    return w, Q
w067, Q067 = qnm220(0.67)
Mdet = 62 * 1.09
f150914 = w067 / (2 * np.pi * Mdet * tsun); tau150914 = Q067 / (np.pi * f150914)
print(f"GW150914-like: f={f150914:.0f} Hz tau={tau150914*1e3:.2f} ms Q={Q067:.2f}")
print(f"Schwarzschild: f={0.3737/(2*np.pi*tsun):.0f} Hz*(Msun/M), tau={1/(0.0890)*tsun*1e6:.1f} us*(M/Msun), Q={0.3737/(2*0.089):.2f}")
fig, axs = plt.subplots(1, 2, figsize=(11.5, 3.9), gridspec_kw=dict(width_ratios=[1.25, 1]))
ax = axs[0]
t = np.linspace(-2, 25, 3000) * 1e-3
tt = np.clip(t, 0, None)
h = np.where(t >= 0, np.exp(-tt / tau150914) * np.cos(2 * np.pi * f150914 * tt), np.nan)
hQ = np.where(t >= 0, np.exp(-tt / (30 / (np.pi * f150914))) * np.cos(2 * np.pi * f150914 * tt), np.nan)
ax.plot(t * 1e3, hQ, color=GRAY, lw=0.8, alpha=0.7, label="$Q=30$（对比：较好的“铃”）")
ax.plot(t * 1e3, h, color=BLUE, lw=2, label=f"黑洞：$Q\\approx{Q067:.0f}$")
ax.plot(tt * 1e3, np.exp(-tt / tau150914), color=RED, ls="--", lw=1)
ax.plot(tt * 1e3, -np.exp(-tt / tau150914), color=RED, ls="--", lw=1)
ax.text(5.2, 0.42, "包络 $e^{-t/\\tau}$", color=RED, fontsize=10)
ax.annotate("", xy=(0, -1.22), xytext=(1e3 / f150914, -1.22), arrowprops=dict(arrowstyle="<->", color=GREEN))
ax.text(0.5e3 / f150914, -1.32, f"$1/f\\approx{1e3/f150914:.0f}$ ms", color=GREEN, ha="center", va="top", fontsize=9.5)
ax.set_xlim(-1, 25); ax.set_ylim(-1.55, 1.35)
ax.set_xlabel("并合后时间 $t$ (ms)"); ax.set_ylabel("$h(t)$（归一化）"); ax.set_yticks([])
ax.legend(loc="upper right", fontsize=9, frameon=False); clean(ax)
ax.set_title(f"(a) GW150914 式铃宕：$f\\approx{f150914:.0f}$ Hz，$\\tau\\approx{tau150914*1e3:.0f}$ ms", fontsize=11)
ax = axs[1]
M = np.logspace(0, 9, 200)
for j, ls, lab in [(0.0, "-", "不转动（$\\chi=0$）"), (0.7, "--", "$\\chi=0.7$")]:
    w, _ = qnm220(j)
    ax.loglog(M, w / (2 * np.pi * M * tsun), color=BLUE, ls=ls, lw=1.6, label=lab)
ax.axhspan(10, 2000, color=ORANGE, alpha=0.15, lw=0); ax.text(2e5, 140, "地面探测器 (LIGO/Virgo/KAGRA)", color=ORANGE, fontsize=9, ha="center")
ax.axhspan(1e-4, 0.1, color=GREEN, alpha=0.15, lw=0); ax.text(3e1, 1.5e-3, "LISA", color=GREEN, fontsize=10, ha="center")
ax.plot(62, w067 / (2 * np.pi * 62 * tsun), "o", color=RED, ms=6)
ax.text(90, 900, "GW150914", color=RED, fontsize=9)
w0, _ = qnm220(0.7)
ax.plot(1e6, w0 / (2 * np.pi * 1e6 * tsun), "s", color=RED, ms=6)
ax.text(1.5e6, 3e-2, "$10^6\\,M_\\odot$", color=RED, fontsize=9)
ax.set_xlabel("黑洞质量 $M/M_\\odot$"); ax.set_ylabel("铃宕频率 $f$ (Hz)")
ax.set_ylim(1e-5, 3e4); ax.legend(loc="lower left", fontsize=9, frameon=False); clean(ax)
ax.set_title("(b) $f\\propto1/M$：质量决定“音高”", fontsize=11)
fig.tight_layout(w_pad=2.5)
fig.savefig(OUT + "bh_ringdown.png", bbox_inches="tight", facecolor="white"); plt.close(fig)

# ---------------- Fig 3: Hubble friction ----------------
x = np.logspace(-2, 2.2, 4000)  # x = m t ; radiation era H = 1/(2t)
phi = Gamma(1.25) * (x / 2) ** -0.25 * jv(0.25, x)  # regular solution, phi(0)=1, dphi(0)=0
dphi = np.gradient(phi, x)
rho = 0.5 * dphi**2 + 0.5 * phi**2  # in units m^2 phi_i^2
fig, axs = plt.subplots(1, 2, figsize=(11.5, 3.9))
ax = axs[0]
xc = 0.75  # lambda = 3H/2 = m  ->  m t = 3/4
ax.axvspan(1e-2, xc, color=ORANGE, alpha=0.12, lw=0)
ax.axvline(xc, color=GRAY, ls=":", lw=1)
ax.semilogx(x, phi, color=BLUE, lw=1.6)
env = Gamma(1.25) * 2 ** 0.25 * np.sqrt(2 / np.pi) * x ** -0.75
ax.semilogx(x[x > 2], env[x > 2], color=RED, ls="--", lw=1)
ax.semilogx(x[x > 2], -env[x > 2], color=RED, ls="--", lw=1)
ax.text(0.03, 0.55, "过阻尼\n$\\frac{3}{2}H>m$\n场被“冻结”", color=ORANGE, fontsize=10)
ax.text(6, 0.55, "欠阻尼 $\\frac{3}{2}H<m$\n振荡，振幅 $\\propto a^{-3/2}$", color=BLUE, fontsize=10)
ax.text(xc * 1.08, -0.85, "$\\frac{3}{2}H=m$", color=GRAY, fontsize=9.5)
ax.set_xlim(1e-2, 160); ax.set_ylim(-1.0, 1.15)
ax.set_xlabel("$mt$"); ax.set_ylabel("$\\phi/\\phi_i$"); clean(ax)
ax.set_title("(a) $\\ddot\\phi+3H\\dot\\phi+m^2\\phi=0$，$H=1/2t$", fontsize=11)
ax = axs[1]
a3 = x ** 1.5
ax.loglog(x, rho * a3 / (rho * a3)[-1], color=BLUE, lw=1.6)
ax.axvspan(1e-2, xc, color=ORANGE, alpha=0.12, lw=0)
ax.loglog(x[x < 0.3], (0.5 * x[x < 0.3] ** 1.5) / (rho * a3)[-1], color=ORANGE, ls="--", lw=1)
ax.text(0.012, 0.25, "$\\rho_\\phi\\approx$ 常数\n（像真空能）\n$\\Rightarrow\\rho_\\phi a^3\\propto a^3$", color=ORANGE, fontsize=9.5)
ax.text(5, 0.25, "$\\rho_\\phi\\propto a^{-3}$\n（像物质：暗物质！）", color=BLUE, fontsize=10)
ax.set_xlim(1e-2, 160); ax.set_ylim(1e-4, 3)
ax.set_xlabel("$mt$"); ax.set_ylabel("$\\rho_\\phi\\,a^3$（归一化）"); clean(ax)
ax.set_title("(b) 能量密度：从“冻结”到“像物质”", fontsize=11)
fig.tight_layout(w_pad=2.5)
fig.savefig(OUT + "hubble_friction.png", bbox_inches="tight", facecolor="white"); plt.close(fig)

# ---------------- Fig 4: Io forced eccentricity ----------------
fig = plt.figure(figsize=(12, 4.0))
ax = fig.add_axes([0.0, 0.02, 0.30, 0.92])
R = {"木卫一 Io": 1.0, "木卫二 Europa": 2 ** (2 / 3), "木卫三 Ganymede": 4 ** (2 / 3)}
P = {"木卫一 Io": 1.769, "木卫二 Europa": 3.551, "木卫三 Ganymede": 7.155}
cols = [RED, BLUE, GREEN]
lam = {"木卫一 Io": 0.0, "木卫二 Europa": 0.0, "木卫三 Ganymede": np.deg2rad(90)}
th = np.linspace(0, 2 * np.pi, 300)
ax.add_patch(Circle((0, 0), 0.22, color=ORANGE, zorder=5)); ax.text(0, -0.42, "木星", ha="center", fontsize=9)
for (k, r), c in zip(R.items(), cols):
    ax.plot(r * np.cos(th), r * np.sin(th), color=c, lw=1)
    ax.add_patch(Circle((r * np.cos(lam[k]), r * np.sin(lam[k])), 0.09, color=c, zorder=6))
ax.text(0.62, -0.12, "Io\n1.77 d", color=RED, ha="center", va="top", fontsize=8.5)
ax.text(2.07, -0.12, "Europa\n3.55 d", color=BLUE, ha="center", va="top", fontsize=8.5)
ax.text(0.2, R["木卫三 Ganymede"] + 0.12, "Ganymede  7.16 d", color=GREEN, ha="left", va="bottom", fontsize=8.5)
ax.plot([0, 2.7], [0, 0], color=GRAY, ls=":", lw=1)
ax.text(2.0, 0.42, "会合总在木卫一的\n近木点附近发生", color=RED, fontsize=8.5, ha="left")
ax.set_xlim(-2.8, 2.9); ax.set_ylim(-2.8, 2.9); ax.set_aspect("equal"); ax.axis("off")
ax.set_title("(a) 拉普拉斯共振 1:2:4", fontsize=11)
# model: w = z e^{-i gamma t} = z_f + (z0 - z_f) exp[(i(g-gamma) - lam) t]
zf = 1.0; z0 = 2.4 * np.exp(1j * 2.3); dg = 1.0; lamd = 0.09
t = np.linspace(0, 45, 3000)
w = zf + (z0 - zf) * np.exp((1j * dg - lamd) * t)
ax = fig.add_axes([0.36, 0.13, 0.27, 0.78])
ax.plot(w.real, w.imag, color=BLUE, lw=1.1)
ax.plot(z0.real, z0.imag, "o", color=GRAY, ms=5); ax.text(z0.real, z0.imag + 0.25, "初始状态", color=GRAY, ha="center", fontsize=9)
ax.plot(zf, 0, "*", color=RED, ms=13, zorder=5)
ax.annotate("受迫偏心率（稳态解）", xy=(zf, -0.08), xytext=(0.6, -2.35), color=RED, fontsize=9, ha="center", arrowprops=dict(arrowstyle="->", color=RED, lw=1))
ax.plot(0, 0, "k+", ms=8)
ax.set_aspect("equal"); ax.set_xlim(-2.6, 3.3); ax.set_ylim(-2.6, 2.6)
ax.set_xlabel("$e\\cos(\\varpi-\\gamma t)$"); ax.set_ylabel("$e\\sin(\\varpi-\\gamma t)$")
ax.set_xticks([]); ax.set_yticks([]); clean(ax)
ax.set_title("(b) 偏心率矢量（随外力转动的参照系）", fontsize=11)
ax = fig.add_axes([0.70, 0.13, 0.29, 0.78])
ax.plot(t, np.abs(w), color=BLUE, lw=1.4, label="$e(t)$")
ax.axhline(zf, color=RED, ls="--", lw=1.1); ax.text(44, zf - 0.12, "受迫偏心率 $e_{\\rm f}$", color=RED, ha="right", va="top", fontsize=10)
ax.plot(t, zf + np.abs(z0 - zf) * np.exp(-lamd * t), color=GRAY, ls=":", lw=1)
ax.plot(t, np.maximum(zf - np.abs(z0 - zf) * np.exp(-lamd * t), 0), color=GRAY, ls=":", lw=1)
ax.text(12, 2.55, "自由部分 $\\propto e^{-\\lambda t}$ 衰减（潮汐阻尼）", color=GRAY, fontsize=9)
ax.set_xlabel("时间（任意单位）"); ax.set_ylabel("偏心率 $e/e_{\\rm f}$")
ax.set_ylim(0, 3.6); ax.set_xlim(0, 45); clean(ax)
ax.set_title("(c) 暂态衰减，只剩稳态解", fontsize=11)
fig.savefig(OUT + "io_forced_ecc.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
print("done")
