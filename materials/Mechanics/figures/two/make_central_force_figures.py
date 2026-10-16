"""Teaching figures and animations for 中心力场.md (2026-10).

Static
  conic_sections.png        同一近心点、不同偏心率的圆锥曲线
  tidal_field.png           潮汐加速度场与两个潮汐隆起
  lab_cm_scattering.png     质心系与实验室系：速度合成圆图
Animations (frame 0 = overview frame; a PDF shows only frame 0)
  two_body_cm.gif           两体问题：质心系中的两个质点与约化质量的相对轨道
  kepler_second_law.gif     开普勒第二定律：相等时间扫过相等面积
  veff_orbit.gif            有效势中的径向运动与平面轨道：封闭 vs 进动
  lrl_vector.gif            LRL 矢量：两部分都在变，和保持不变
  lagrange_orbits.gif       共转参照系中的蝌蚪形与马蹄形轨道
  zero_velocity_sweep.gif   雅可比积分增大时零速度曲线的拓扑变化
  l4_vs_l1.gif              L4 附近稳定、L1 附近不稳定
  rutherford_beam.gif       平行粒子束的卢瑟福散射
  dynamical_friction_wake.gif 动力学摩擦：大质量天体身后的密度尾迹
  slingshot.gif             引力弹弓：行星参照系 vs 太阳参照系

Run: python3 figures/two/make_central_force_figures.py [name ...]   (numpy, scipy, matplotlib, pillow)
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Wedge
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
from PIL import Image

for f in font_manager.findSystemFonts():
    if "NotoSansCJK-Regular" in f:
        font_manager.fontManager.addfont(f)
for cand in ("/System/Library/Fonts/STHeiti Light.ttc", "/System/Library/Fonts/Supplemental/Songti.ttc"):
    if os.path.exists(cand):
        font_manager.fontManager.addfont(cand)
plt.rcParams.update({"font.family": ["Noto Sans CJK SC", "Heiti TC", "Songti SC", "DejaVu Sans"],
                     "mathtext.fontset": "cm", "axes.unicode_minus": False, "font.size": 11})
OUT = os.path.dirname(os.path.abspath(__file__)) + "/"
BLUE = "#1f4e9c"; RED = "#c8102e"; ORANGE = "#e08a00"; GREEN = "#2e7d32"; GRAY = "#777777"; PURPLE = "#6a3d9a"
DPI = 90


def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def savefig(fig, name):
    fig.savefig(OUT + name, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", name)


def grab(fig):
    fig.canvas.draw()
    im = Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[..., :3].copy())
    return im


def save_gif(frames, name, ms=70, hold=3000):
    pal = [f.convert("P", palette=Image.Palette.ADAPTIVE, colors=128) for f in frames]
    dur = [hold] + [ms] * (len(pal) - 1)
    pal[0].save(OUT + name, save_all=True, append_images=pal[1:], duration=dur, loop=0, optimize=True, disposal=1)
    print(f"wrote {name} ({os.path.getsize(OUT + name) / 1e6:.2f} MB, {len(pal)} frames)")


def animate(fig, draw, idx, name, ms=70, overview=None):
    frames = []
    draw(idx[-1] if overview is None else overview, True); frames.append(grab(fig))
    for i in idx:
        draw(i, False); frames.append(grab(fig))
    plt.close(fig)
    save_gif(frames, name, ms)


def ode(f, t, y0, **kw):
    return solve_ivp(f, (t[0], t[-1]), y0, t_eval=t, rtol=1e-10, atol=1e-12, method="DOP853", **kw).y


def kepler_E(M, e):
    E = np.array(M, dtype=float).copy()
    for _ in range(60):
        E = E - (E - e * np.sin(E) - M) / (1 - e * np.cos(E))
    return E


def kepler_xy(a, e, t, n=1.0, M0=0.0):
    E = kepler_E(n * t + M0, e)
    x = a * (np.cos(E) - e); y = a * np.sqrt(1 - e * e) * np.sin(E)
    return x, y


# ===================================================================== static
def conic_sections():
    q = 1.0
    fig, ax = plt.subplots(figsize=(8.6, 5.6))
    phis = np.linspace(-np.pi, np.pi, 4000)
    for e, c, lab in ((0.0, GREEN, "$e=0$ 圆"), (0.5, BLUE, "$e=0.5$ 椭圆"), (1.0, ORANGE, "$e=1$ 抛物线"), (1.6, RED, "$e=1.6$ 双曲线")):
        p = q * (1 + e)
        den = 1 + e * np.cos(phis)
        ok = den > 0.02
        r = np.where(ok, p / np.where(ok, den, 1), np.nan)
        x, y = r * np.cos(phis), r * np.sin(phis)
        ax.plot(x, y, color=c, lw=1.8, label=lab)
    ax.plot([0], [0], "o", color="k", ms=6)
    ax.annotate("力心（焦点）", xy=(0, 0), xytext=(-1.9, -0.75), fontsize=10, arrowprops=dict(arrowstyle="->", lw=0.8))
    ax.plot([q], [0], "o", color=PURPLE, ms=6)
    ax.annotate("共同的近心点", xy=(q, 0), xytext=(1.35, -0.55), fontsize=10, color=PURPLE,
                arrowprops=dict(arrowstyle="->", color=PURPLE, lw=0.8))
    ax.text(-5.3, 2.75, "$r=\\dfrac{p}{1+e\\cos\\varphi}$，近心距 $r_{\\min}=\\dfrac{p}{1+e}$ 相同\n"
            "$E<0$：椭圆　$E=0$：抛物线　$E>0$：双曲线", fontsize=10.5, va="top")
    ax.set_xlim(-5.5, 2.3); ax.set_ylim(-3.2, 3.2); ax.set_aspect("equal"); ax.axis("off")
    ax.legend(loc="lower left", fontsize=10, frameon=False)
    savefig(fig, "conic_sections.png")


def tidal_field():
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.8))
    ax = axs[0]
    R = 1.0
    ax.add_patch(Circle((0, 0), R, fc="#dbe7f5", ec=BLUE, lw=1.5))
    th = np.linspace(0, 2 * np.pi, 24, endpoint=False)
    for rr in (1.0, 0.6):
        for t in th[:: (1 if rr == 1.0 else 2)]:
            x = rr * np.array([np.cos(t), np.sin(t)])
            a = 3 * x[0] * np.array([1, 0]) - x
            ax.add_patch(FancyArrowPatch(x, x + 0.32 * a, arrowstyle="-|>", mutation_scale=10, color=RED, lw=1.2))
    ax.annotate("", xy=(2.5, 0), xytext=(1.85, 0), arrowprops=dict(arrowstyle="-|>", color=GRAY, lw=1.5))
    ax.text(2.55, 0.12, "朝向月球", fontsize=10, color=GRAY)
    ax.text(0, -1.55, "潮汐加速度 $\\delta\\boldsymbol{a}=\\dfrac{Gm_2}{R^3}\\left[3(\\hat{\\boldsymbol{X}}\\cdot\\boldsymbol{x})\\hat{\\boldsymbol{X}}-\\boldsymbol{x}\\right]$\n"
            "沿连线向外拉伸（$2\\times$），垂直方向向内压缩（$1\\times$）", ha="center", fontsize=10, va="top")
    ax.set_xlim(-2.1, 3.3); ax.set_ylim(-2.25, 1.6); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("(a) 潮汐加速度场", fontsize=11, loc="left")
    ax = axs[1]
    t = np.linspace(0, 2 * np.pi, 400)
    eps = 0.22
    r = 1 + eps * (1.5 * np.cos(t) ** 2 - 0.5)
    ax.fill(r * np.cos(t), r * np.sin(t), color="#cfe0f2", ec=BLUE, lw=1.5)
    ax.add_patch(Circle((0, 0), 0.82, fc="#c7b299", ec="#8a6d4b", lw=1))
    ax.plot(np.cos(t), np.sin(t), color=GRAY, lw=0.8, ls=":")
    ax.text(0, 0, "地球", ha="center", va="center", fontsize=10)
    ax.add_patch(Circle((3.2, 0), 0.27, color="#bbbbbb"))
    ax.text(3.2, -0.48, "月球", ha="center", fontsize=10)
    ax.text(1.32, 0.22, "高潮", color=BLUE, fontsize=10)
    ax.text(-1.62, 0.22, "高潮", color=BLUE, fontsize=10)
    ax.text(-0.18, 1.0, "低潮", color=BLUE, fontsize=10)
    ax.text(0, -1.55, "等势面沿地月连线拉长：一天内经过两次高潮\n（形变极度夸大；忽略了地球自转造成的潮汐滞后）", ha="center", fontsize=10, va="top")
    ax.set_xlim(-2.1, 3.6); ax.set_ylim(-2.25, 1.6); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("(b) 平衡潮的形状", fontsize=11, loc="left")
    savefig(fig, "tidal_field.png")


def lab_cm_scattering():
    fig, axs = plt.subplots(1, 3, figsize=(12, 4.2))
    for ax, g in zip(axs, (0.5, 1.0, 2.0)):
        V, u = g / (1 + g), 1 / (1 + g)   # v0 = 1: V = m1 v0/(m1+m2), u = m2 v0/(m1+m2)
        a = np.linspace(0, 2 * np.pi, 300)
        ax.plot(V + u * np.cos(a), u * np.sin(a), color=GRAY, lw=1, ls="--")
        ax.add_patch(FancyArrowPatch((0, 0), (V, 0), arrowstyle="-|>", mutation_scale=12, color=GREEN, lw=1.6))
        ax.text(V / 2, -0.09, "$V$", color=GREEN, ha="center", fontsize=11)
        th = np.deg2rad(115)
        P = np.array([V + u * np.cos(th), u * np.sin(th)])
        ax.add_patch(FancyArrowPatch((V, 0), P, arrowstyle="-|>", mutation_scale=12, color=BLUE, lw=1.6))
        ax.add_patch(FancyArrowPatch((0, 0), P, arrowstyle="-|>", mutation_scale=12, color=RED, lw=1.8))
        ax.text(*(P * 0.5 + np.array([-0.12, 0.04])), "$\\boldsymbol{v}_1'$", color=RED, fontsize=11)
        ax.text(V + 0.5 * (P[0] - V) + 0.05, 0.5 * P[1], "$u$", color=BLUE, fontsize=11)
        aa2 = np.linspace(0, th, 40)
        ax.plot(V + 0.08 * np.cos(aa2), 0.08 * np.sin(aa2), color=BLUE, lw=1)
        ax.text(V + 0.11 * np.cos(th / 2), 0.11 * np.sin(th / 2), "$\\theta$", color=BLUE, fontsize=11)
        tl = np.arctan2(P[1], P[0])
        aa = np.linspace(0, tl, 40)
        ax.plot(0.13 * np.cos(aa), 0.13 * np.sin(aa), color=RED, lw=1)
        ax.text(0.16 * np.cos(tl / 2) + 0.02, 0.16 * np.sin(tl / 2), "$\\theta_{\\rm lab}$", color=RED, fontsize=10)
        if g > 1:
            tmax = np.arcsin(u / V)
            ax.plot([0, 1.2 * V * np.cos(tmax)], [0, 1.2 * V * np.sin(tmax)], color=PURPLE, lw=1, ls=":")
            ax.text(0.25 * V, 0.25 * V * np.tan(tmax) + 0.09, "最大散射角", color=PURPLE, fontsize=9.5, rotation=np.degrees(tmax))
        ax.plot([0], [0], "o", color="k", ms=4)
        ax.set_aspect("equal"); ax.axis("off")
        ax.set_xlim(-0.12, V + u + 0.08); ax.set_ylim(-u - 0.08, u + 0.12)
        title = {0.5: "$m_1<m_2$：可以向后散射", 1.0: "$m_1=m_2$：$\\theta_{\\rm lab}=\\theta/2\\leq90^\\circ$",
                 2.0: "$m_1>m_2$：$\\sin\\theta_{\\rm lab,max}=m_2/m_1$"}[g]
        ax.set_title(title, fontsize=10.5)
    fig.text(0.5, 0.02, "实验室系速度 $\\boldsymbol{v}_1'$ = 质心速度 $\\boldsymbol{V}$ + 质心系速度（大小 $u$ 不变，方向转过 $\\theta$）；端点落在虚线圆上",
             ha="center", fontsize=10, color="#333333")
    savefig(fig, "lab_cm_scattering.png")


# ===================================================================== GIF 1
def two_body_cm():
    m1, m2 = 1.0, 0.45
    M = m1 + m2
    a, e = 1.0, 0.55
    t = np.linspace(0, 2 * np.pi, 96, endpoint=False)
    tf = np.linspace(0, 2 * np.pi, 600)
    x, y = kepler_xy(a, e, t); X, Y = kepler_xy(a, e, tf)
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.6), dpi=DPI)

    def draw(i, ov):
        for ax in axs:
            ax.clear()
        ax = axs[0]
        ax.plot(m2 / M * X, m2 / M * Y, color=BLUE, lw=0.9, ls="--")
        ax.plot(-m1 / M * X, -m1 / M * Y, color=RED, lw=0.9, ls="--")
        p1 = m2 / M * np.array([x[i], y[i]]); p2 = -m1 / M * np.array([x[i], y[i]])
        ax.plot(*zip(p1, p2), color=GRAY, lw=0.8)
        ax.plot(*p1, "o", color=BLUE, ms=14); ax.plot(*p2, "o", color=RED, ms=9)
        ax.plot([0], [0], "+", color="k", ms=10, mew=1.5)
        ax.text(0.04, -0.12, "质心", fontsize=9.5)
        ax.text(*(p1 + [0.06, 0.06]), "$m_1$", color=BLUE, fontsize=11)
        ax.text(*(p2 + [0.06, 0.08]), "$m_2$", color=RED, fontsize=11)
        ax.set_title("质心系：两个质点绕质心画出相似的椭圆\n（$m_1=2.2\,m_2$，较重的 $m_1$ 轨道较小）", fontsize=10.5)
        ax.text(0.55, -0.62, "$\\boldsymbol{r}_1=\\dfrac{m_2}{m_1+m_2}\\boldsymbol{r}$，$\\boldsymbol{r}_2=-\\dfrac{m_1}{m_1+m_2}\\boldsymbol{r}$",
                ha="center", fontsize=10)
        ax.set_xlim(-0.62, 1.2); ax.set_ylim(-0.72, 0.6); ax.set_aspect("equal"); ax.axis("off")
        ax = axs[1]
        ax.plot(X, Y, color=PURPLE, lw=0.9, ls="--")
        ax.plot([0], [0], "o", color="k", ms=6)
        ax.plot([0, x[i]], [0, y[i]], color=GRAY, lw=0.8)
        ax.plot(x[i], y[i], "o", color=PURPLE, ms=10)
        ax.text(x[i] + 0.06, y[i] + 0.06, "$\\mu$", color=PURPLE, fontsize=12)
        ax.text(0.05, -0.16, "固定力心", fontsize=9.5)
        ax.set_title("等效单体问题：质量为 $\\mu$ 的粒子绕固定力心运动", fontsize=11)
        ax.text(-0.55, -1.3, "$\\boldsymbol{r}=\\boldsymbol{r}_1-\\boldsymbol{r}_2$，$\\mu=\\dfrac{m_1m_2}{m_1+m_2}$", ha="center", fontsize=10)
        ax.set_xlim(-1.8, 0.7); ax.set_ylim(-1.38, 1.0); ax.set_aspect("equal"); ax.axis("off")
        fig.tight_layout()
    animate(fig, draw, range(len(t)), "two_body_cm.gif", ms=70, overview=0)


# ===================================================================== GIF 2
def kepler_second_law():
    a, e = 1.0, 0.65
    N = 12
    tk = np.linspace(0, 2 * np.pi, N + 1)
    sub = 40
    frames_t = np.linspace(0, 2 * np.pi, N * 8 + 1)
    fig, ax = plt.subplots(figsize=(7.2, 4.8), dpi=DPI)
    TF = np.linspace(0, 2 * np.pi, 800); XF, YF = kepler_xy(a, e, TF)
    cols = ["#9ec5e8", "#f5c08a"]

    def sector(t0, t1):
        ts = np.linspace(t0, t1, sub)
        xs, ys = kepler_xy(a, e, ts)
        return np.r_[[[0, 0]], np.c_[xs, ys]]

    def draw(i, ov):
        ax.clear()
        t = frames_t[i]
        ax.plot(XF, YF, color=GRAY, lw=1)
        for k in range(N):
            if tk[k + 1] <= t + 1e-9:
                ax.add_patch(Polygon(sector(tk[k], tk[k + 1]), closed=True, fc=cols[k % 2], ec="white", lw=0.8))
            elif tk[k] < t:
                ax.add_patch(Polygon(sector(tk[k], t), closed=True, fc=cols[k % 2], ec="white", lw=0.8, alpha=0.8))
        x, y = kepler_xy(a, e, np.array([t]))
        ax.plot([0, x[0]], [0, y[0]], color=BLUE, lw=1.2)
        ax.plot(x, y, "o", color=BLUE, ms=8)
        ax.plot([0], [0], "o", color=ORANGE, ms=14)
        ax.text(-0.02, -0.17, "太阳", ha="center", fontsize=9.5)
        ax.text(-1.98, -0.78, f"每块扇形对应相同的时间 $T/{N}$\n面积都等于 $\\pi ab/{N}$", fontsize=10.5, va="top")
        ax.text(0.12, 0.62, "近日点附近：\n扇形短而宽，走得快", fontsize=9.5, color=BLUE)
        ax.text(-1.98, 0.8, "远日点附近：\n扇形长而窄，走得慢", fontsize=9.5, color=BLUE)
        ax.set_xlim(-2.0, 0.6); ax.set_ylim(-0.85, 0.85); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title("开普勒第二定律：相等时间内扫过相等的面积（$e=0.65$）", fontsize=11)
        fig.tight_layout()
    animate(fig, draw, range(len(frames_t)), "kepler_second_law.gif", ms=90)


# ===================================================================== GIF 3
def veff_orbit():
    cases = [dict(beta=0.0, r0=0.7, title="开普勒势 $V=-\\alpha/r$：轨道封闭", col=BLUE),
             dict(beta=0.12, r0=0.55, title="$V=-\\alpha/r-\\beta/r^2$：近心点进动", col=RED)]
    J, alpha = 1.0, 1.0
    T = 60.0
    t = np.linspace(0, T, 6000)
    for c in cases:
        b = c["beta"]
        def rhs(_t, y, b=b):
            r, pr, ph = y
            return [pr, J ** 2 / r ** 3 - alpha / r ** 2 - 2 * b / r ** 3, J / r ** 2]
        r0 = c["r0"]
        sol = ode(rhs, t, [r0, 0.0, 0.0])
        c["r"], c["ph"] = sol[0], sol[2]
        c["E"] = J ** 2 / (2 * r0 ** 2) - alpha / r0 - b / r0 ** 2
    idx = np.linspace(0, len(t) - 1, 170).astype(int)
    fig = plt.figure(figsize=(10.4, 6.2), dpi=DPI)
    axes = [(fig.add_axes([0.06, 0.56 - 0.5 * k, 0.42, 0.36]), fig.add_axes([0.55, 0.53 - 0.5 * k, 0.42, 0.42])) for k in range(2)]
    rr = np.linspace(0.3, 4.0, 400)

    def draw(i, ov):
        for c, (a1, a2) in zip(cases, axes):
            a1.clear(); a2.clear()
            V = J ** 2 / (2 * rr ** 2) - alpha / rr - c["beta"] / rr ** 2
            a1.plot(rr, V, color=c["col"], lw=1.6)
            a1.axhline(c["E"], color=GRAY, ls="--", lw=1)
            a1.text(3.95, c["E"] + 0.04, "$E$", color=GRAY, ha="right")
            ri = c["r"][i]
            a1.plot([ri], [c["E"]], "o", color="k", ms=7)
            a1.plot([ri, ri], [J ** 2 / (2 * ri ** 2) - alpha / ri - c["beta"] / ri ** 2, c["E"]], color="k", lw=0.8, ls=":")
            a1.set_xlim(0.3, 4.0); a1.set_ylim(-1.15, 0.6)
            a1.set_xlabel("$r$", labelpad=0); a1.set_ylabel("$V_{\\rm eff}(r)$")
            a1.set_title(c["title"], fontsize=10.5, loc="left")
            clean(a1)
            x, y = c["r"] * np.cos(c["ph"]), c["r"] * np.sin(c["ph"])
            a2.plot(x[: i + 1], y[: i + 1], color=c["col"], lw=0.9)
            a2.plot([x[i]], [y[i]], "o", color="k", ms=6)
            a2.plot([0], [0], "o", color=ORANGE, ms=8)
            a2.set_xlim(-2.4, 1.4); a2.set_ylim(-1.6, 1.6); a2.set_aspect("equal"); a2.axis("off")
        fig.text(0.5, 0.005, "左：径向坐标在有效势中两个转折点之间往复（一维运动）　右：同一运动的平面轨道",
                 ha="center", fontsize=10, color="#333333")
        for txt in fig.texts[:-1]:
            txt.remove()
    animate(fig, draw, idx, "veff_orbit.gif", ms=60)


# ===================================================================== GIF 4
def lrl_vector():
    a, e = 1.0, 0.6
    alpha = 1.0                        # GM = alpha/mu = 1, mu = 1
    p = a * (1 - e * e); J = np.sqrt(alpha * p)
    t = np.linspace(0, 2 * np.pi, 100, endpoint=False)
    TF = np.linspace(0, 2 * np.pi, 600); XF, YF = kepler_xy(a, e, TF)
    fig, ax = plt.subplots(figsize=(7.6, 5.4), dpi=DPI)
    s = 0.55

    def state(tt):
        E = kepler_E(np.array([tt]), e)[0]
        x, y = a * (np.cos(E) - e), a * np.sqrt(1 - e * e) * np.sin(E)
        Edot = 1 / (1 - e * np.cos(E))
        vx, vy = -a * np.sin(E) * Edot, a * np.sqrt(1 - e * e) * np.cos(E) * Edot
        return np.array([x, y]), np.array([vx, vy])

    def draw(i, ov):
        ax.clear()
        r, v = state(t[i])
        rn = r / np.linalg.norm(r)
        vxL = J * np.array([v[1], -v[0]])          # v × L with L = J z
        A = vxL - alpha * rn
        ax.plot(XF, YF, color=GRAY, lw=1)
        cc = np.linspace(0, 2 * np.pi, 200)
        ax.plot(s * (A[0] + alpha * np.cos(cc)), s * (A[1] + alpha * np.sin(cc)), color=BLUE, lw=0.7, ls=":")
        ax.plot([0], [0], "o", color=ORANGE, ms=10)
        ax.plot(*r, "o", color="k", ms=7)
        ax.add_patch(FancyArrowPatch(r, r + 0.35 * v, arrowstyle="-|>", mutation_scale=10, color="k", lw=1))
        ax.text(*(r + 0.38 * v), "$\\boldsymbol{v}$", fontsize=10)
        ax.add_patch(FancyArrowPatch((0, 0), s * vxL, arrowstyle="-|>", mutation_scale=13, color=BLUE, lw=2))
        ax.add_patch(FancyArrowPatch(s * vxL, s * A, arrowstyle="-|>", mutation_scale=13, color=RED, lw=2))
        ax.add_patch(FancyArrowPatch((0, 0), s * A, arrowstyle="-|>", mutation_scale=15, color=GREEN, lw=2.6))
        ax.text(*(s * vxL * 0.5 + np.array([0.03, 0.05])), "$\\boldsymbol{v}\\times\\boldsymbol{L}$", color=BLUE, fontsize=11)
        ax.text(*(s * (vxL + A) / 2 + np.array([0.04, -0.1])), "$-\\alpha\\hat{\\boldsymbol{r}}$", color=RED, fontsize=11)
        ax.text(s * A[0] + 0.03, 0.06, "$\\boldsymbol{A}$（指向近日点，长度 $\\alpha e$）", color=GREEN, fontsize=11)
        ax.text(-1.7, -1.05, "蓝色虚线：$\\boldsymbol{v}\\times\\boldsymbol{L}$ 的端点在一个圆上运动（半径 $\\alpha$，圆心在 $\\boldsymbol{A}$ 端点）", fontsize=9.5, color=BLUE)
        ax.set_xlim(-1.75, 1.2); ax.set_ylim(-1.15, 1.15); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title("LRL 矢量 $\\boldsymbol{A}=\\boldsymbol{v}\\times\\boldsymbol{L}-\\alpha\\hat{\\boldsymbol{r}}$：两部分都在变，和保持不变", fontsize=11)
        fig.tight_layout()
    animate(fig, draw, range(len(t)), "lrl_vector.gif", ms=70, overview=33)


# ===================================================================== CR3BP helpers
def cr3bp_rhs(mu):
    # doc convention: m1 at (mu, 0), m2 at (-(1-mu), 0); units G(m1+m2)=1, R=1, Omega=1
    x1, x2 = mu, -(1 - mu)

    def rhs(_t, s):
        x, y, vx, vy = s
        r1 = np.hypot(x - x1, y); r2 = np.hypot(x - x2, y)
        ax_ = x - (1 - mu) * (x - x1) / r1 ** 3 - mu * (x - x2) / r2 ** 3 + 2 * vy
        ay_ = y - (1 - mu) * y / r1 ** 3 - mu * y / r2 ** 3 - 2 * vx
        return [vx, vy, ax_, ay_]
    return rhs


def veff(mu, x, y):
    x1, x2 = mu, -(1 - mu)
    return -0.5 * (x * x + y * y) - (1 - mu) / np.hypot(x - x1, y) - mu / np.hypot(x - x2, y)


def lagrange_points(mu):
    x1, x2 = mu, -(1 - mu)
    f = lambda x: x - (1 - mu) * (x - x1) / abs(x - x1) ** 3 - mu * (x - x2) / abs(x - x2) ** 3
    L1 = brentq(f, x2 + 1e-6, x1 - 1e-6)
    L2 = brentq(f, x2 - 2, x2 - 1e-6)
    L3 = brentq(f, x1 + 1e-6, x1 + 2)
    xL4 = (x1 + x2) / 2
    return {"L1": (L1, 0), "L2": (L2, 0), "L3": (L3, 0), "L4": (xL4, np.sqrt(3) / 2), "L5": (xL4, -np.sqrt(3) / 2)}


def cr3bp_circular_ic(mu, r, ang):
    """Start on a circle of radius r about the barycentre with the Keplerian circular speed (rotating frame)."""
    vphi = r * (r ** -1.5 - 1.0)
    x, y = r * np.cos(ang), r * np.sin(ang)
    return [x, y, -vphi * np.sin(ang), vphi * np.cos(ang)]


def lagrange_orbits():
    mu = 0.001
    Lp = lagrange_points(mu)
    rhs = cr3bp_rhs(mu)
    # tadpole: start at L4 displaced along the orbit
    ang4 = np.arctan2(Lp["L4"][1], Lp["L4"][0])
    ic_t = cr3bp_circular_ic(mu, 1.0, ang4 - np.deg2rad(22))
    ic_h = cr3bp_circular_ic(mu, 1.0 - 0.0085, 0.0)   # near L3 side, slightly inside: horseshoe
    Tt, Th = 160.0, 560.0
    tt = np.linspace(0, Tt, 8000); th = np.linspace(0, Th, 20000)
    st = ode(rhs, tt, ic_t); sh = ode(rhs, th, ic_h)
    ang_h = np.unwrap(np.arctan2(sh[1], sh[0]) - np.pi)
    print("horseshoe angle range (deg, relative to m2):", np.degrees(ang_h.min()), np.degrees(ang_h.max()))
    nfr = 150
    it = np.linspace(0, len(tt) - 1, nfr).astype(int); ih = np.linspace(0, len(th) - 1, nfr).astype(int)
    fig, axs = plt.subplots(1, 2, figsize=(10.4, 5.2), dpi=DPI)
    a = np.linspace(0, 2 * np.pi, 300)

    def base(ax, title):
        ax.plot(np.cos(a), np.sin(a), color="#dddddd", lw=0.8)
        ax.plot([mu], [0], "o", color=ORANGE, ms=12); ax.plot([-(1 - mu)], [0], "o", color=BLUE, ms=6)
        ax.text(mu + 0.06, -0.14, "$m_1$", fontsize=10); ax.text(-(1 - mu) - 0.05, -0.17, "$m_2$", fontsize=10, color=BLUE)
        for k, (x, y) in Lp.items():
            ax.plot([x], [y], "x", color=GRAY, ms=6, mew=1.3)
            ax.text(x + 0.05, y + 0.05, k, fontsize=9, color=GRAY)
        ax.set_xlim(-1.35, 1.35); ax.set_ylim(-1.3, 1.3); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(title, fontsize=11)

    def draw(i, ov):
        for ax in axs:
            ax.clear()
        base(axs[0], "蝌蚪形轨道：绕 $L_4$ 来回摆动")
        j = it[i]
        axs[0].plot(st[0, : j + 1], st[1, : j + 1], color=RED, lw=0.8)
        axs[0].plot([st[0, j]], [st[1, j]], "o", color="k", ms=5)
        base(axs[1], "马蹄形轨道：绕过 $L_4$、$L_3$、$L_5$")
        j = ih[i]
        axs[1].plot(sh[0, : j + 1], sh[1, : j + 1], color=GREEN, lw=0.6)
        axs[1].plot([sh[0, j]], [sh[1, j]], "o", color="k", ms=5)
        fig.text(0.5, 0.02, f"共转参照系，$m_2/(m_1+m_2)=0.001$（与日–木系统相近）；轨道均由运动方程数值积分得到", ha="center",
                 fontsize=9.5, color="#333333")
        for txt in fig.texts[:-1]:
            txt.remove()
        fig.subplots_adjust(left=0.01, right=0.99, top=0.92, bottom=0.07, wspace=0.03)
    animate(fig, draw, range(nfr), "lagrange_orbits.gif", ms=70)


def zero_velocity_sweep():
    mu = 0.1
    Lp = lagrange_points(mu)
    xs = np.linspace(-1.7, 1.7, 500); ys = np.linspace(-1.5, 1.5, 440)
    X, Y = np.meshgrid(xs, ys)
    V = veff(mu, X, Y)
    VL = {k: veff(mu, *v) for k, v in Lp.items()}
    lo, hi = VL["L1"] - 0.08, VL["L4"] + 0.02
    EJs = np.linspace(lo, hi, 90)
    stages = [(VL["L1"], "① 三块许可区互不连通：$m_2$ 附近的质点无法离开"),
              (VL["L2"], "② $L_1$ 颈口打开：$m_1$ 与 $m_2$ 附近连通"),
              (VL["L3"], "③ $L_2$ 也打开：可以从 $m_2$ 附近逃到外区"),
              (VL["L4"], "④ 禁区只剩 $L_4$、$L_5$ 周围两块"),
              (np.inf, "⑤ 没有禁区")]

    def stage_text(E):
        for v, s in stages:
            if E < v:
                return s

    def panel(ax, E, big=True):
        ax.contourf(X, Y, (V > E).astype(float), levels=[0.5, 1.5], colors=["#c9ced6"])
        ax.contour(X, Y, V, levels=[E], colors=[BLUE], linewidths=1.2 if big else 0.8)
        ax.plot([mu], [0], "o", color=ORANGE, ms=9 if big else 5); ax.plot([-(1 - mu)], [0], "o", color=BLUE, ms=6 if big else 3)
        for k, (x, y) in Lp.items():
            ax.plot([x], [y], "x", color=RED, ms=6 if big else 4, mew=1.2)
            if big:
                ax.text(x + 0.05, y + 0.06, k, fontsize=9, color=RED)
        ax.set_xlim(xs[0], xs[-1]); ax.set_ylim(ys[0], ys[-1]); ax.set_aspect("equal"); ax.axis("off")

    fig = plt.figure(figsize=(8.0, 6.0), dpi=DPI)

    def draw(i, ov):
        fig.clf()
        if ov:
            reps = [VL["L1"] - 0.05, (VL["L1"] + VL["L2"]) / 2, (VL["L2"] + VL["L3"]) / 2, (VL["L3"] + VL["L4"]) / 2, VL["L4"] + 0.02]
            for k, E in enumerate(reps):
                ax = fig.add_axes([0.01 + (k % 3) * 0.33, 0.5 - (k // 3) * 0.46, 0.32, 0.42])
                panel(ax, E, big=False)
                ax.set_title(stage_text(E)[:1] + "  " + ["三块分离", "$L_1$ 打开", "$L_2$ 打开", "只剩 $L_4,L_5$ 附近", "无禁区"][k], fontsize=10)
            fig.text(0.83, 0.25, "灰色：禁区 $V_{\\rm eff}>E_J$\n蓝线：零速度曲线\n\n随 $E_J$ 增大\n许可区依次连通", fontsize=10, ha="center", va="center")
            return
        E = EJs[i]
        ax = fig.add_axes([0.02, 0.1, 0.96, 0.8])
        panel(ax, E)
        fig.text(0.5, 0.93, stage_text(E), ha="center", fontsize=11.5)
        fig.text(0.5, 0.04, f"$E_J={E:.3f}$　（$V_{{\\rm eff}}(L_1)={VL['L1']:.3f}$，$V_{{\\rm eff}}(L_4)={VL['L4']:.3f}$；$\\mu=0.1$）",
                 ha="center", fontsize=10, color="#333333")
    animate(fig, draw, range(len(EJs)), "zero_velocity_sweep.gif", ms=90, overview=0)


def l4_vs_l1():
    mu = 0.0121  # Earth-Moon
    Lp = lagrange_points(mu)
    rhs = cr3bp_rhs(mu)
    T = 45.0
    t = np.linspace(0, T, 6000)
    d = 0.01
    s4 = ode(rhs, t, [Lp["L4"][0] + d, Lp["L4"][1], 0, 0])
    s1 = ode(rhs, t, [Lp["L1"][0] + 0.002, 0, 0, 0], )
    idx = np.linspace(0, len(t) - 1, 130).astype(int)
    fig, axs = plt.subplots(1, 2, figsize=(10.4, 5.0), dpi=DPI)
    a = np.linspace(0, 2 * np.pi, 300)

    def draw(i, ov):
        j = idx[i] if not ov else len(t) - 1
        for ax, s, title, col, key in ((axs[0], s4, "$L_4$：被科里奥利力“拉住”，绕点小幅摆动", GREEN, "L4"),
                                       (axs[1], s1, "$L_1$：同样的小扰动指数增长，很快离开", RED, "L1")):
            ax.clear()
            ax.plot(np.cos(a), np.sin(a), color="#e2e2e2", lw=0.8)
            ax.plot([mu], [0], "o", color=ORANGE, ms=11); ax.plot([-(1 - mu)], [0], "o", color=BLUE, ms=6)
            for k, (x, y) in Lp.items():
                ax.plot([x], [y], "x", color=GRAY, ms=6, mew=1.2)
                ax.text(x + 0.04, y + 0.05, k, fontsize=9, color=GRAY)
            ax.plot(s[0, : j + 1], s[1, : j + 1], color=col, lw=0.9)
            ax.plot([s[0, j]], [s[1, j]], "o", color="k", ms=5)
            ax.set_xlim(-1.45, 1.35); ax.set_ylim(-1.3, 1.3); ax.set_aspect("equal"); ax.axis("off")
            ax.set_title(title, fontsize=10.5)
        fig.text(0.5, 0.02, f"共转参照系，$\\mu=0.0121$（地–月），初始扰动约为地月距离的 1%，初速度为零；$t={t[j] / (2 * np.pi):.1f}$ 个公转周期",
                 ha="center", fontsize=9.5, color="#333333")
        for txt in fig.texts[:-1]:
            txt.remove()
        fig.subplots_adjust(left=0.01, right=0.99, top=0.92, bottom=0.07, wspace=0.03)
    animate(fig, draw, range(len(idx)), "l4_vs_l1.gif", ms=70)


# ===================================================================== GIF 8
def rutherford_beam():
    k = 1.0  # k = alpha/(m v^2); v = 1
    bs = np.linspace(-3.0, 3.0, 41)
    T = 16.0
    t = np.linspace(0, T, 1600)
    trajs = []
    for b in bs:
        def rhs(_t, s):
            x, y, vx, vy = s
            r3 = (x * x + y * y) ** 1.5
            return [vx, vy, k * x / r3, k * y / r3]
        trajs.append(ode(rhs, t, [-8.0, b, 1.0, 0.0]))
    idx = np.linspace(0, len(t) - 1, 120).astype(int)
    fig, ax = plt.subplots(figsize=(8.6, 5.4), dpi=DPI)
    cmap = plt.get_cmap("coolwarm")

    def draw(i, ov):
        ax.clear()
        j = idx[i]
        for n, s in enumerate(trajs):
            c = cmap(0.5 + 0.5 * np.sign(bs[n]) * min(abs(bs[n]) / 3, 1)) if bs[n] != 0 else "k"
            ax.plot(s[0, : j + 1], s[1, : j + 1], color=c, lw=0.8, alpha=0.9)
            if not ov:
                ax.plot([s[0, j]], [s[1, j]], "o", color=c, ms=2.5)
        ax.plot([0], [0], "o", color="k", ms=7)
        ax.text(0.15, -0.45, "核（排斥力心）", fontsize=10, bbox=dict(fc="white", ec="none", pad=0.5))
        ax.text(-7.8, 3.6, "平行粒子束从左方入射，碰撞参数 $b$ 均匀分布\n"
                "$b$ 越小偏转越大：$\\tan\\dfrac{\\theta}{2}=\\dfrac{k}{b}$，$k=\\dfrac{\\alpha}{mv_0^2}$", fontsize=10.5, va="top", bbox=dict(fc="white", ec="none", alpha=0.85, pad=1))
        ax.text(2.3, 0.15, "力心后方的“阴影”区：\n没有粒子能到达", fontsize=9.5, color="#444444", bbox=dict(fc="white", ec="none", pad=0.5))
        ax.set_xlim(-8, 6); ax.set_ylim(-4, 4); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title("卢瑟福散射：粒子束在排斥库仑势中的轨迹", fontsize=11)
        fig.tight_layout()
    animate(fig, draw, range(len(idx)), "rutherford_beam.gif", ms=70)


# ===================================================================== GIF 9
def dynamical_friction_wake():
    GM, v, eps = 1.0, 1.0, 0.08
    rng = np.random.default_rng(3)
    N = 42000
    x0 = rng.uniform(-27, 10, N); y0 = rng.uniform(-7, 7, N)
    T = 20.0
    nsteps = 2000
    dt = T / nsteps
    x, y = x0.copy(), y0.copy(); vx, vy = np.full(N, v), np.zeros(N)
    snaps = []
    keep = np.linspace(0, nsteps, 61).astype(int)

    def acc(x, y):
        r2 = x * x + y * y + eps * eps
        f = -GM / r2 ** 1.5
        return f * x, f * y
    ax_, ay_ = acc(x, y)
    for n in range(nsteps + 1):
        if n in keep:
            snaps.append((x.copy(), y.copy()))
        vx += 0.5 * dt * ax_; vy += 0.5 * dt * ay_
        x += dt * vx; y += dt * vy
        ax_, ay_ = acc(x, y)
        vx += 0.5 * dt * ax_; vy += 0.5 * dt * ay_
    fig, axs = plt.subplots(1, 2, figsize=(10.6, 4.6), dpi=72, gridspec_kw={"width_ratios": [1.3, 1]})
    from scipy.ndimage import gaussian_filter
    xe, ye = np.linspace(-6, 10, 81), np.linspace(-5, 5, 51)
    nbar = N / (37 * 14) * (16 / 80) * (10 / 50)

    def draw(i, ov):
        for ax in axs:
            ax.clear()
        xs, ys = snaps[i]
        ax = axs[0]
        ax.scatter(xs[:7000], ys[:7000], s=1.2, color=BLUE, alpha=0.55, lw=0)
        ax.plot([0], [0], "o", color=RED, ms=10)
        ax.annotate("", xy=(-4.8, 4.2), xytext=(-3.2, 4.2), arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.5))
        ax.text(-3.0, 4.05, "$M$ 相对背景向左运动", color=RED, fontsize=10)
        ax.annotate("", xy=(8.5, -4.3), xytext=(6.9, -4.3), arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=1.2))
        ax.text(1.8, -4.45, "在 $M$ 的参照系中背景向右流", color=BLUE, fontsize=9.5)
        ax.set_xlim(-6, 10); ax.set_ylim(-5, 5); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title("背景星（试验粒子）流过大质量天体 $M$", fontsize=11)
        ax = axs[1]
        H, _, _ = np.histogram2d(xs, ys, bins=[xe, ye])
        H = gaussian_filter(H, 1.6)
        ax.imshow((H / nbar).T, origin="lower", extent=[xe[0], xe[-1], ye[0], ye[-1]], cmap="magma", vmin=0, vmax=2.5, aspect="equal")
        ax.plot([0], [0], "o", color="cyan", ms=6)
        ax.text(1.0, 3.6, "身后的高密度尾迹\n把 $M$ 往后拉", color="white", fontsize=10)
        ax.set_xlim(-6, 10); ax.set_ylim(-5, 5); ax.axis("off")
        ax.set_title("数密度 / 平均密度", fontsize=11)
        fig.text(0.5, 0.02, f"$t={i * T / 60 * v:.1f}\\,b_{{90}}/v$；二维示意（试验粒子只受 $M$ 的引力，彼此无相互作用）",
                 ha="center", fontsize=9.5, color="#333333")
        for txt in fig.texts[:-1]:
            txt.remove()
        fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.08, wspace=0.04)
    animate(fig, draw, range(len(snaps)), "dynamical_friction_wake.gif", ms=70)


# ===================================================================== GIF 10
def slingshot():
    GM, vinf = 1.0, 1.0
    e = 1.28
    rp = (e - 1) * GM / vinf ** 2
    delta = 2 * np.arcsin(1 / e)
    b = rp * np.sqrt(1 + 2 * GM / (rp * vinf ** 2))
    Vp = 1.3
    th_in = -np.pi / 2 - delta / 2
    vp = np.sqrt(vinf ** 2 + 2 * GM / rp)
    def rhs(_t, s):
        x, y, vx, vy = s
        r3 = (x * x + y * y) ** 1.5
        return [vx, vy, -GM * x / r3, -GM * y / r3]
    Th = 9.0
    tf = np.linspace(0, Th, 1500)
    fwd = ode(rhs, tf, [-rp, 0.0, 0.0, -vp])            # periapsis at (-rp, 0), moving -y: counter-clockwise turn
    bwd = ode(rhs, tf, [-rp, 0.0, 0.0, vp])
    bwd[2:] *= -1                                      # time-reversed copy of the incoming branch
    s = np.c_[bwd[:, ::-1][:, :-1], fwd]
    t = np.r_[-tf[::-1][:-1], tf]
    t0 = 0.0
    vin, vout = s[2:, 0], s[2:, -1]
    vin = vinf * vin / np.linalg.norm(vin); vout = vinf * vout / np.linalg.norm(vout)
    print("slingshot: deflection (deg)", np.degrees(np.arccos(vin @ vout / vinf ** 2)), "expected", np.degrees(delta))
    idx = np.linspace(0, len(t) - 1, 130).astype(int)
    fig, axs = plt.subplots(1, 3, figsize=(12.0, 4.6), dpi=DPI, gridspec_kw={"width_ratios": [1, 1.25, 0.8]})

    def draw(i, ov):
        j = idx[i]
        for ax in axs:
            ax.clear()
        ax = axs[0]
        ax.plot(s[0, : j + 1], s[1, : j + 1], color=BLUE, lw=1.2)
        ax.plot([s[0, j]], [s[1, j]], "o", color="k", ms=5)
        ax.add_patch(Circle((0, 0), 0.12, color=ORANGE))
        ax.set_xlim(-6, 6); ax.set_ylim(-7, 3.5); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title("行星参照系：对称的双曲线\n进出速率都是 $v_\\infty$，只是方向转过 $\\delta$", fontsize=10)
        ax = axs[1]
        tt = t[: j + 1] - t0
        X = s[0, : j + 1] + Vp * tt; Y = s[1, : j + 1]
        ax.plot(X, Y, color=RED, lw=1.2)
        ax.plot([X[-1]], [Y[-1]], "o", color="k", ms=5)
        px = Vp * (t[j] - t0)
        ax.add_patch(Circle((px, 0), 0.12, color=ORANGE))
        ax.plot(Vp * (t - t0), 0 * t, color=ORANGE, lw=0.8, ls=":")
        ax.set_xlim(-12, 12); ax.set_ylim(-7, 3.5); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title("太阳参照系：行星以 $V_p$ 向右运动\n航天器从行星后方绕过，被“甩”得更快", fontsize=10)
        ax = axs[2]
        Vv = np.array([Vp, 0])
        for vec, col, lab in ((vin, GRAY, "前"), (vout, GREEN, "后")):
            ax.add_patch(FancyArrowPatch((0, 0), Vv, arrowstyle="-|>", mutation_scale=11, color=ORANGE, lw=1.4))
            ax.add_patch(FancyArrowPatch(Vv, Vv + vec, arrowstyle="-|>", mutation_scale=11, color=col, lw=1.4))
            ax.add_patch(FancyArrowPatch((0, 0), Vv + vec, arrowstyle="-|>", mutation_scale=12, color=col, lw=2.0, ls="--"))
            ax.text((Vv + vec)[0], (Vv + vec)[1] - 0.22, f"飞掠{lab}\n$|\\boldsymbol{{v}}|={np.linalg.norm(Vv + vec):.2f}$", color=col, fontsize=9.5, ha="center", va="top")
        ax.text(Vp / 2, 0.06, "$\\boldsymbol{V}_p$", color=ORANGE, ha="center", fontsize=10)
        ax.set_xlim(-0.2, 2.6); ax.set_ylim(-1.55, 0.35); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title("速度合成 $\\boldsymbol{v}=\\boldsymbol{V}_p+\\boldsymbol{v}_\\infty$\n（$v_\\infty=1$，$V_p=1.3$，$\\delta\\approx103^\\circ$）", fontsize=10)
        fig.subplots_adjust(left=0.01, right=0.99, top=0.84, bottom=0.03, wspace=0.05)
    animate(fig, draw, range(len(idx)), "slingshot.gif", ms=70)


ALL = {f.__name__: f for f in (conic_sections, tidal_field, lab_cm_scattering, two_body_cm, kepler_second_law, veff_orbit,
                               lrl_vector, lagrange_orbits, zero_velocity_sweep, l4_vs_l1, rutherford_beam,
                               dynamical_friction_wake, slingshot)}
if __name__ == "__main__":
    for name in sys.argv[1:] or ALL:
        ALL[name]()
