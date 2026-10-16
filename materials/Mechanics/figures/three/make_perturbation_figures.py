# Static figures for 微扰和摄动理论.md (teaching enhancements, 2026-10)
#   duffing_secular.png        引言：朴素展开的久期项 vs Lindstedt 频移
#   pendulum_phase.png         单摆相图与周期-振幅关系（等时性的破坏）
#   duhamel_impulses.png       Duhamel 积分：冲击响应的叠加
#   damping_roots_phase.png    阻尼振子特征根在复平面上的轨迹 + 相空间轨迹
#   damped_forced_response.png 有阻尼强迫振动的振幅与相位曲线
#   duffing_response.png       非线性（Duffing）受迫振动：弯曲的共振峰与跳跃
#   ince_strutt.png            Mathieu 方程的稳定图（不稳定“舌头”）
#   mercury_u_phi.png          水星：u(φ) 的久期项与重新求和
import os
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from scipy.integrate import solve_ivp
from scipy.special import ellipk

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


def save(fig, name):
    fig.savefig(OUT + name, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def ode(f, t, y0):
    return solve_ivp(f, (t[0], t[-1]), y0, t_eval=t, rtol=1e-10, atol=1e-12, method="DOP853").y


# ---------------- 1. Duffing: secular term vs Lindstedt ----------------
eps, a = 0.1, 1.0
t = np.linspace(0, 70, 4000)
x_ex = ode(lambda t, y: [y[1], -y[0] - eps * y[0] ** 3], t, [a, 0])[0]
x_naive = np.cos(t) + eps * (-3 / 8 * t * np.sin(t) + (np.cos(3 * t) - np.cos(t)) / 32)
w = 1 + 3 * eps / 8
x_lind = np.cos(w * t) + eps * (np.cos(3 * w * t) - np.cos(w * t)) / 32
fig, axs = plt.subplots(2, 1, figsize=(9.5, 5.6), sharex=True)
ax = axs[0]
ax.plot(t, x_naive, color=RED, lw=1.2, label="朴素展开 $x^{(0)}+\\varepsilon x^{(1)}$")
ax.plot(t, x_ex, color=BLUE, lw=1.6, label="数值精确解")
env = np.sqrt(1 + (3 * eps * t / 8) ** 2)
ax.plot(t, env, color=RED, ls=":", lw=1); ax.plot(t, -env, color=RED, ls=":", lw=1)
ax.text(52, 2.45, "久期项 $-\\frac{3\\varepsilon}{8}\\,t\\sin t$\n使振幅“虚假”增长", color=RED, fontsize=10, ha="center")
ax.set_ylim(-3.2, 3.2); ax.set_ylabel("$x$")
ax.set_title("(a) 朴素展开：短时间内准确，长时间后完全失效", fontsize=11, loc="left")
ax.legend(loc="lower left", fontsize=9, frameon=False, ncol=2)
clean(ax)
ax = axs[1]
ax.plot(t, np.cos(t), color=GRAY, lw=0.9, ls="--", label="零阶解 $\\cos t$（频率不对）")
ax.plot(t, x_ex, color=BLUE, lw=1.6, label="数值精确解")
ax.plot(t, x_lind, color=ORANGE, lw=1.2, ls=(0, (5, 3)), label="Lindstedt：$\\omega=1+\\frac{3}{8}\\varepsilon a^2$")
ax.set_ylim(-1.6, 1.6); ax.set_xlabel("$t$"); ax.set_ylabel("$x$")
ax.set_title("(b) 把久期项重新求和为频率修正：在长时间内保持准确", fontsize=11, loc="left")
ax.legend(loc="lower left", fontsize=9, frameon=False, ncol=3)
clean(ax)
fig.text(0.99, 0.005, "$\\ddot x+x+\\varepsilon x^3=0$，$\\varepsilon=0.1$，$x(0)=1$，$\\dot x(0)=0$",
         ha="right", fontsize=9, color=GRAY)
fig.tight_layout()
save(fig, "duffing_secular.png")

# ---------------- 2. Pendulum phase portrait + period ----------------
fig, axs = plt.subplots(1, 2, figsize=(11, 4.3), gridspec_kw={"width_ratios": [1.45, 1]})
ax = axs[0]
th = np.linspace(-1.35 * np.pi, 1.35 * np.pi, 600); om = np.linspace(-3.1, 3.1, 500)
TH, OM = np.meshgrid(th, om)
E = 0.5 * OM ** 2 - np.cos(TH)
ax.contour(TH, OM, E, levels=[-0.9, -0.6, -0.2, 0.3, 0.75], colors=BLUE, linewidths=1.0, linestyles="solid")
ax.contour(TH, OM, E, levels=[1.4, 2.4], colors=GREEN, linewidths=1.0)
ax.contour(TH, OM, E, levels=[1.0], colors=RED, linewidths=1.6)
for E0 in (-0.6, -0.2):
    A = np.sqrt(2 * (E0 + 1)); p = np.linspace(0, 2 * np.pi, 200)
    ax.plot(A * np.cos(p), A * np.sin(p), color=ORANGE, ls="--", lw=1.1)
ax.plot([0], [0], "o", color=BLUE, ms=4)
for xx in (-np.pi, np.pi):
    ax.plot([xx], [0], "x", color=RED, ms=7, mew=1.8)
ax.annotate("平衡点附近：近似为椭圆\n（虚线为谐振近似）", xy=(-0.95, -0.75), xytext=(-3.95, -2.95),
            fontsize=9, color=ORANGE, arrowprops=dict(arrowstyle="->", color=ORANGE, lw=0.9))
ax.text(0, 2.62, "分界线（$E=mgl$）", color=RED, ha="center", fontsize=9.5,
        bbox=dict(fc="white", ec="none", pad=0.4))
ax.text(-3.9, 2.8, "转动", color=GREEN, fontsize=9.5)
ax.text(2.05, -0.15, "大振幅：\n曲线变形", color=BLUE, fontsize=9)
ax.set_xticks([-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi]); ax.set_xticklabels(["$-\\pi$", "$-\\pi/2$", "0", "$\\pi/2$", "$\\pi$"])
ax.set_xlabel("$\\theta$"); ax.set_ylabel("$\\dot\\theta/\\omega_0$")
ax.set_xlim(th[0], th[-1]); ax.set_ylim(-3.1, 3.1)
ax.set_title("(a) 单摆相图", fontsize=11, loc="left"); clean(ax)
ax = axs[1]
th0 = np.linspace(0.001, np.radians(175), 400)
T_ex = 2 / np.pi * ellipk(np.sin(th0 / 2) ** 2)
ax.plot(np.degrees(th0), T_ex, color=BLUE, lw=1.8, label="精确：$\\frac{2}{\\pi}K(\\sin^2\\frac{\\theta_0}{2})$")
ax.plot(np.degrees(th0), 1 + th0 ** 2 / 16, color=ORANGE, ls="--", lw=1.4, label="一阶微扰：$1+\\theta_0^2/16$")
ax.axhline(1, color=GRAY, ls=":", lw=1, label="谐振近似（等时）")
for d, c in ((10, GREEN), (120, RED)):
    v = 2 / np.pi * ellipk(np.sin(np.radians(d) / 2) ** 2)
    ax.plot([d], [v], "o", color=c, ms=5)
    ax.text(d + 3 if d > 50 else d + 4, v - 0.17 if d > 50 else v + 0.06, f"{d}°：$T/T_0={v:.3f}$", color=c, fontsize=9)
ax.set_xlim(0, 180); ax.set_ylim(0.9, 3.2)
ax.set_xlabel("振幅 $\\theta_0$ (°)"); ax.set_ylabel("$T/T_0$")
ax.legend(loc="upper left", fontsize=9, frameon=False)
ax.set_title("(b) 周期随振幅增大（等时性被破坏）", fontsize=11, loc="left"); clean(ax)
fig.tight_layout()
save(fig, "pendulum_phase.png")

# ---------------- 3. Duhamel: superposition of impulse responses ----------------
w0, tau = 1.0, 8.0
Fm = lambda t: np.where((t >= 0) & (t <= tau), np.sin(np.pi * t / tau) ** 2, 0.0)
t = np.linspace(0, 26, 2000)
N = 16; dt = tau / N; tk = (np.arange(N) + 0.5) * dt
fig, axs = plt.subplots(2, 1, figsize=(9.5, 5.4), sharex=True, gridspec_kw={"height_ratios": [1, 2]})
ax = axs[0]
cmap = plt.get_cmap("viridis")
ax.bar(tk, Fm(tk), width=dt * 0.85, color=[cmap(0.15 + 0.7 * k / N) for k in range(N)], alpha=0.85)
ax.plot(t, Fm(t), color="k", lw=1.2)
ax.set_ylabel("$F(t)/F_{\\max}$"); ax.set_ylim(0, 1.25)
ax.text(tau + 0.6, 0.55, "把外力切成一串冲击\n第 $k$ 个冲量 $F(t_k)\\,\\Delta t$", fontsize=10)
ax.set_title("(a) 外力 = 一串短冲击", fontsize=11, loc="left"); clean(ax)
ax = axs[1]
tot = np.zeros_like(t)
for k in range(N):
    r = np.where(t >= tk[k], Fm(tk[k]) * dt / w0 * np.sin(w0 * (t - tk[k])), 0.0)
    tot += r
    ax.plot(t, r, color=cmap(0.15 + 0.7 * k / N), lw=0.8, alpha=0.9)
ex = ode(lambda t, y: [y[1], -w0 ** 2 * y[0] + Fm(t)], t, [0, 0])[0]
ax.plot(t, tot, color=BLUE, lw=2.0, label="各冲击响应之和")
ax.plot(t, ex, color=RED, lw=1.2, ls="--", label="直接数值求解 $\\ddot x+\\omega^2x=F/m$")
ax.text(7.6, 1.48, "细线：每个冲击激发的自由振动 $\\frac{F(t_k)\\Delta t}{m\\omega}\\sin\\omega(t-t_k)$",
        fontsize=9.5, color="#333333")
ax.set_xlabel("$\\omega t$"); ax.set_ylabel("$x$")
ax.legend(loc="upper right", fontsize=9, frameon=False)
ax.set_title("(b) 响应 = 冲击响应的线性叠加（Duhamel 积分）", fontsize=11, loc="left"); clean(ax)
fig.tight_layout()
save(fig, "duhamel_impulses.png")

# ---------------- 4. Damping: root locus + phase space ----------------
fig, axs = plt.subplots(1, 2, figsize=(11, 4.6))
ax = axs[0]
lam = np.linspace(0, 1, 200)
ax.plot(-lam, np.sqrt(1 - lam ** 2), color=BLUE, lw=1.8)
ax.plot(-lam, -np.sqrt(1 - lam ** 2), color=BLUE, lw=1.8)
lam2 = np.linspace(1, 2.6, 200)
ax.plot(-lam2 + np.sqrt(lam2 ** 2 - 1), 0 * lam2, color=GREEN, lw=2.2, solid_capstyle="butt")
ax.plot(-lam2 - np.sqrt(lam2 ** 2 - 1), 0 * lam2 + 0.0, color=GREEN, lw=2.2, solid_capstyle="butt")
for L, c, lab in ((0.22, BLUE, "$\\lambda=0.22\\,\\omega_0$"), (1.0, RED, "$\\lambda=\\omega_0$"), (1.6, GREEN, "$\\lambda=1.6\\,\\omega_0$")):
    if L < 1:
        pts = [(-L, np.sqrt(1 - L * L)), (-L, -np.sqrt(1 - L * L))]
    else:
        s = np.sqrt(L * L - 1); pts = [(-L + s, 0), (-L - s, 0)]
    for p in pts:
        ax.plot(*p, "o", color=c, ms=7, zorder=5, mec="white")
ax.plot([0, 0], [1, -1], "o", color=BLUE, ms=5, mfc="white")
ax.text(0.06, 1.06, "$\\lambda=0$：$r=\\pm i\\omega_0$", fontsize=9.5, color=BLUE)
ax.text(-0.12, 0.80, "$\\lambda=0.22\\,\\omega_0$", fontsize=9.5, color=BLUE)
ax.text(-0.95, 0.5, "欠阻尼：两根沿\n半径 $\\omega_0$ 的圆移动", fontsize=9.5, color=BLUE, ha="left")
ax.annotate("临界阻尼：两根重合于 $-\\omega_0$", xy=(-1, 0), xytext=(-2.75, 0.62), fontsize=9.5, color=RED,
            arrowprops=dict(arrowstyle="->", color=RED, lw=0.9))
ax.annotate("过阻尼：$r_+\\to0^-$\n摩擦越大，回得越慢", xy=(-0.3, -0.02), xytext=(-2.8, -0.62), fontsize=9.5, color=GREEN,
            arrowprops=dict(arrowstyle="->", color=GREEN, lw=0.9))
for sg in (1, -1):
    ax.annotate("", xy=(-0.62, sg * np.sqrt(1 - 0.62 ** 2)), xytext=(-0.45, sg * np.sqrt(1 - 0.45 ** 2)),
                arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=1.4, shrinkA=0, shrinkB=0))
ax.annotate("", xy=(-1.75, 0.0), xytext=(-1.35, 0.0), arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=1.2))
ax.annotate("", xy=(-0.62, 0.0), xytext=(-0.85, 0.0), arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=1.2))
p = np.linspace(0, 2 * np.pi, 300)
ax.plot(np.cos(p), np.sin(p), color=GRAY, ls=":", lw=0.8)
ax.axhline(0, color="k", lw=0.6); ax.axvline(0, color="k", lw=0.6)
ax.set_xlim(-2.9, 1.0); ax.set_ylim(-1.25, 1.25); ax.set_aspect("equal")
ax.set_xlabel("$\\mathrm{Re}\\,r/\\omega_0$（衰减率 $-\\lambda$）"); ax.set_ylabel("$\\mathrm{Im}\\,r/\\omega_0$（振荡频率 $\\pm\\omega_d$）")
ax.set_title("(a) 特征根随 $\\lambda$ 增大的轨迹", fontsize=11, loc="left")
ax = axs[1]
t = np.linspace(0, 40, 4000)
for L, c, lab in ((0.22, BLUE, "欠阻尼 $\\lambda=0.22\\,\\omega_0$"), (1.0, RED, "临界阻尼"), (1.6, GREEN, "过阻尼 $\\lambda=1.6\\,\\omega_0$")):
    y = ode(lambda t, y, L=L: [y[1], -2 * L * y[1] - y[0]], t, [1, 0])
    ax.plot(y[0], y[1], color=c, lw=1.5, label=lab)
ax.plot([1], [0], "o", color="k", ms=5); ax.text(1.03, 0.05, "起点", fontsize=9)
ax.plot([0], [0], "*", color=ORANGE, ms=11, zorder=6)
ax.set_xlabel("$x/x_0$"); ax.set_ylabel("$\\dot x/(\\omega_0x_0)$")
ax.set_aspect("equal"); ax.set_xlim(-0.75, 1.15); ax.set_ylim(-0.85, 0.5)
ax.legend(loc="lower left", fontsize=9, frameon=False)
ax.set_title("(b) 相空间：螺线（欠阻尼）与直接回落（过阻尼）", fontsize=11, loc="left"); clean(ax)
fig.tight_layout()
save(fig, "damping_roots_phase.png")

# ---------------- 5. Damped forced response: amplitude & phase ----------------
g = np.linspace(0.001, 2.0, 2000)
fig, axs = plt.subplots(1, 2, figsize=(11, 4.3))
Qs = [(1, GRAY), (2, GREEN), (5, BLUE), (10, RED)]
for Q, c in Qs:
    amp = 1 / np.sqrt((1 - g ** 2) ** 2 + (g / Q) ** 2)
    axs[0].plot(g, amp, color=c, lw=1.6, label=f"$Q={Q}$")
    dl = np.arctan2(g / Q, 1 - g ** 2)
    axs[1].plot(g, dl / np.pi, color=c, lw=1.6, label=f"$Q={Q}$")
axs[1].plot(g, np.where(g < 1, 0, 1), color="k", lw=0.9, ls=":", label="无阻尼")
ax = axs[0]
Q = 5; pk = Q / np.sqrt(1 - 1 / (4 * Q * Q)) * 1.0
lamq = 1 / (2 * Q)
ax.annotate("", xy=(1 - lamq, pk / np.sqrt(2)), xytext=(1 + lamq, pk / np.sqrt(2)),
            arrowprops=dict(arrowstyle="<->", color=BLUE, lw=1.1))
ax.text(1.13, pk / np.sqrt(2) - 0.15, "$\\Delta\\gamma\\approx2\\lambda=\\omega_0/Q$\n（$b^2$ 降为一半处）", color=BLUE, fontsize=9.5)
ax.text(0.33, 9.7, "峰高 $\\approx Q\\times$静态位移\n$b_{\\max}\\approx\\dfrac{f}{2m\\lambda\\omega_0}$", color=RED, fontsize=9.5)
ax.set_ylim(0, 11); ax.set_xlim(0, 2)
ax.set_xlabel("$\\gamma/\\omega_0$"); ax.set_ylabel("$b\\,/\\,(f/m\\omega_0^2)$")
ax.legend(loc="upper right", fontsize=9, frameon=False)
ax.set_title("(a) 振幅：阻尼使共振峰有限", fontsize=11, loc="left"); clean(ax)
ax = axs[1]
ax.axhline(0.5, color=GRAY, ls="--", lw=0.8); ax.axvline(1, color=GRAY, ls="--", lw=0.8)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1]); ax.set_yticklabels(["0", "$\\pi/4$", "$\\pi/2$", "$3\\pi/4$", "$\\pi$"])
ax.text(0.05, 0.08, "同相：跟随外力", fontsize=9.5)
ax.text(1.32, 0.88, "反相", fontsize=9.5)
ax.text(1.04, 0.42, "共振时滞后 $\\pi/2$：\n速度与外力同相，\n外力做功最多", fontsize=9.5)
ax.set_xlim(0, 2); ax.set_ylim(-0.03, 1.05)
ax.set_xlabel("$\\gamma/\\omega_0$"); ax.set_ylabel("相位滞后 $\\delta$")
ax.legend(loc="upper left", fontsize=9, frameon=False, bbox_to_anchor=(0.0, 0.93))
ax.set_title("(b) 相位：$\\tan\\delta=2\\lambda\\gamma/(\\omega_0^2-\\gamma^2)$", fontsize=11, loc="left"); clean(ax)
fig.tight_layout()
save(fig, "damped_forced_response.png")

# ---------------- 6. Duffing forced response ----------------
lam, beta = 0.04, 0.6
fig, ax = plt.subplots(figsize=(8.6, 4.8))
aa = np.linspace(0.005, 1.7, 8000)
for F, c in ((0.025, GREEN), (0.05, BLUE), (0.1, RED)):
    A = 1 + 0.75 * beta * aa ** 2
    B = 2 * A - 4 * lam ** 2; C = A ** 2 - (F / aa) ** 2
    disc = B ** 2 - 4 * C
    ok = disc >= 0
    gp = np.full_like(aa, np.nan); gm = np.full_like(aa, np.nan)
    gp[ok] = (B[ok] + np.sqrt(disc[ok])) / 2; gm[ok] = (B[ok] - np.sqrt(disc[ok])) / 2
    gm[gm <= 0] = np.nan
    gpp, gmm = np.sqrt(gp), np.sqrt(gm)
    i_min = np.nanargmin(gpp)
    tip = np.where(ok)[0][-1]
    ax.plot(gpp[:i_min + 1], aa[:i_min + 1], color=c, lw=1.8)
    ax.plot(gpp[i_min:tip + 1], aa[i_min:tip + 1], color=c, lw=1.3, ls="--")
    ax.plot(gmm, aa, color=c, lw=1.8, label=f"$f/m={F}$")
    if F == 0.1:
        g_tip, a_tip = gpp[tip], aa[tip]
        a_low = aa[np.nanargmin(np.abs(gpp[:i_min] - g_tip))]
        ax.annotate("", xy=(g_tip, a_low + 0.03), xytext=(g_tip, a_tip - 0.03),
                    arrowprops=dict(arrowstyle="-|>", color="k", lw=1.2))
        g_jump = gpp[i_min]; a_jump = aa[i_min]
        a_up = aa[np.nanargmin(np.abs(np.where(aa > 0.8, gmm, np.nan) - g_jump))]
        ax.annotate("", xy=(g_jump, a_up - 0.03), xytext=(g_jump, a_jump + 0.03),
                    arrowprops=dict(arrowstyle="-|>", color="k", lw=1.2))
        ax.text(g_tip + 0.012, (a_tip + a_low) / 2, "升频扫描：\n振幅突然跌落", fontsize=9.5)
        ax.text(g_jump - 0.012, (a_jump + a_up) / 2 + 0.25, "降频扫描：\n振幅突然跃升", fontsize=9.5, ha="right")
        lin = F / np.sqrt((1 - aa * 0 - 0) ** 2)  # placeholder
gg = np.linspace(0.6, 1.6, 800)
ax.plot(gg, (0.1) / np.sqrt((1 - gg ** 2) ** 2 + (2 * lam * gg) ** 2), color=GRAY, lw=1.0, ls=":",
        label="线性振子（$f/m=0.1$）")
ab = np.linspace(0, 1.7, 200)
ax.plot(np.sqrt(1 + 0.75 * beta * ab ** 2), ab, color=ORANGE, lw=1.1, ls="-.", label="骨架线 $\\omega(a)$")
ax.set_xlim(0.6, 1.6); ax.set_ylim(0, 1.7)
ax.set_xlabel("$\\gamma/\\omega_0$"); ax.set_ylabel("稳态振幅 $a$")
ax.legend(loc="upper left", fontsize=9, frameon=False)
ax.text(1.59, 1.68, "$\\ddot x+2\\lambda\\dot x+\\omega_0^2x+\\beta x^3=\\frac{f}{m}\\cos\\gamma t$\n$\\omega_0=1$，$\\lambda=0.04$，$\\beta=0.6$\n同色虚线：不稳定分支（实际观测不到）",
        fontsize=9.5, color="#444444", ha="right", va="top")
ax.set_title("非线性受迫振动：频率依赖振幅，共振峰向高频弯曲", fontsize=11, loc="left"); clean(ax)
fig.tight_layout()
save(fig, "duffing_response.png")


# ---------------- 7. Ince–Strutt diagram ----------------
def floquet_grid(G, H, lam, N=700):
    T = 2 * np.pi / G
    def rhs(tau, X, V):
        return T * V, T * (-2 * lam * V - (1 + H * np.cos(2 * np.pi * tau)) * X)
    res = []
    for X, V in ((np.ones_like(G), np.zeros_like(G)), (np.zeros_like(G), np.ones_like(G))):
        d = 1.0 / N
        for i in range(N):
            tau = i * d
            k1x, k1v = rhs(tau, X, V)
            k2x, k2v = rhs(tau + d / 2, X + d / 2 * k1x, V + d / 2 * k1v)
            k3x, k3v = rhs(tau + d / 2, X + d / 2 * k2x, V + d / 2 * k2v)
            k4x, k4v = rhs(tau + d, X + d * k3x, V + d * k3v)
            X = X + d / 6 * (k1x + 2 * k2x + 2 * k3x + k4x)
            V = V + d / 6 * (k1v + 2 * k2v + 2 * k3v + k4v)
        res.append((X, V))
    (x1, v1), (x2, v2) = res
    tr = x1 + v2; det = x1 * v2 - x2 * v1
    disc = tr ** 2 - 4 * det
    mu = np.where(disc >= 0, (np.abs(tr) + np.sqrt(np.maximum(disc, 0))) / 2, np.sqrt(np.abs(det)))
    return tr, mu


gam = np.linspace(0.56, 2.75, 900); hh = np.linspace(0, 1.0, 240)
G, H = np.meshgrid(gam, hh)
tr0, _ = floquet_grid(G, H, 0.0)
_, mud = floquet_grid(G, H, 0.05)
fig, ax = plt.subplots(figsize=(9.5, 4.6))
unst = (np.abs(tr0) > 2).astype(float)
ax.contourf(G, H, unst, levels=[0.5, 1.5], colors=["#f4c7cc"])
ax.contour(G, H, np.abs(tr0), levels=[2], colors=RED, linewidths=1.0)
ax.contour(G, H, mud, levels=[1.0], colors=BLUE, linewidths=1.5)
hl = np.linspace(0, 1, 50)
ax.plot(2 + hl / 2, hl, color="k", ls="--", lw=1.0); ax.plot(2 - hl / 2, hl, color="k", ls="--", lw=1.0)
for n in (1, 2, 3):
    gn = 2 / n
    ax.text(gn, 1.02, {1: "$n=1$\n$\\gamma=2\\omega_0$", 2: "$n=2$\n$\\gamma=\\omega_0$", 3: "$n=3$\n$\\gamma=2\\omega_0/3$"}[n],
            ha="center", va="bottom", fontsize=9.5, color=RED)
ax.annotate("慢变振幅法：$|\\varepsilon|<h\\omega_0/2$", xy=(2 + 0.38, 0.76), xytext=(2.38, 0.42),
            fontsize=9.5, arrowprops=dict(arrowstyle="->", lw=0.8))
ax.annotate("有阻尼 $\\lambda=0.05\\,\\omega_0$：\n阈值 $h>4\\lambda/\\omega_0=0.2$", xy=(2.0, 0.2), xytext=(2.2, 0.08),
            fontsize=9.5, color=BLUE, arrowprops=dict(arrowstyle="->", color=BLUE, lw=0.8))
ax.text(1.08, 0.66, "红色区域：无阻尼时\n$|\\Delta|>2$ 的不稳定区\n蓝线：有阻尼时的\n不稳定区边界\n高阶舌头宽度 $\\propto h^n$，\n有阻尼时阈值更高",
        fontsize=9.5, va="top")
ax.set_xlim(gam[0], gam[-1]); ax.set_ylim(0, 1.0)
ax.set_xlabel("调制频率 $\\gamma/\\omega_0$"); ax.set_ylabel("调制幅度 $h$")
ax.set_title("$\\ddot x+\\omega_0^2(1+h\\cos\\gamma t)x=0$ 的稳定图（Floquet 判据数值计算）", fontsize=11, loc="left", pad=36)
clean(ax)
fig.tight_layout()
save(fig, "ince_strutt.png")

# ---------------- 8. Mercury-like u(phi): secular term and resummation ----------------
k2, e = 0.005, 0.3
ph = np.linspace(0, 12 * 2 * np.pi, 6000)
u = ode(lambda p, y: [y[1], -y[0] + k2 + 3 * y[0] ** 2], ph, [k2 * (1 + e), 0])[0]
y_ex = u / k2 - 1
y_naive = e * np.cos(ph) + 3 * k2 * e * ph * np.sin(ph)
y_res = e * np.cos((1 - 3 * k2) * ph)
X = ph / (2 * np.pi)
fig, axs = plt.subplots(2, 1, figsize=(9.5, 5.6), sharex=True)
ax = axs[0]
ax.plot(X, y_naive, color=RED, lw=1.2, label="一阶朴素解（含 $\\varphi\\sin\\varphi$）")
ax.plot(X, y_ex, color=BLUE, lw=1.6, label="数值精确解")
ax.plot(X, e * np.cos(ph), color=GRAY, lw=0.8, ls="--", label="牛顿：$e\\cos\\varphi$")
ax.set_ylim(-0.75, 0.6); ax.set_ylabel("$\\tilde u/(GM/J)^2-1$")
ax.legend(loc="lower left", fontsize=9, frameon=False, ncol=3)
ax.set_title("(a) 久期项 $3(GM/J)^2e\\,\\varphi\\sin\\varphi$ 随圈数增长", fontsize=11, loc="left"); clean(ax)
ax = axs[1]
ax.plot(X, y_ex, color=BLUE, lw=1.6, label="数值精确解")
ax.plot(X, y_res, color=ORANGE, lw=1.2, ls=(0, (5, 3)), label="重新求和：$e\\cos[(1-3(GM/J)^2)\\varphi]$")
ax.plot(X, e * np.cos(ph), color=GRAY, lw=0.8, ls="--", label="牛顿")
ax.set_ylim(-0.45, 0.45); ax.set_xlabel("$\\varphi/2\\pi$（圈数）"); ax.set_ylabel("$\\tilde u/(GM/J)^2-1$")
ax.legend(loc="lower left", fontsize=9, frameon=False, ncol=3)
ax.set_title("(b) 物理意义：$u(\\varphi)$ 的振荡频率略小于 1，极大值（近日点）每圈推迟 $\\Delta\\varphi=6\\pi(GM/J)^2$",
             fontsize=11, loc="left"); clean(ax)
fig.text(0.99, 0.005, "为便于观察取 $(GM/J)^2=0.005$（水星约为 $2.7\\times10^{-8}$），$e=0.3$", ha="right", fontsize=9, color=GRAY)
fig.tight_layout()
save(fig, "mercury_u_phi.png")
print("done")
