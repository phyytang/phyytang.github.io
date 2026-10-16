"""Teaching figures and animations for 最小作用量原理.md (2026-10).

Animations (frame 0 = overview frame; a PDF shows only frame 0)
  brachistochrone_race.gif  几条曲线上的小球同时出发，摆线最先到达
  tautochrone.gif           摆线的等时性：不同高度释放，同时到达最低点
  action_landscape.gif      试探路径族与作用量 S(ε)：真实路径是平稳点（短时间为极小，长时间不是）
Static
  virial_kepler.png         开普勒轨道上的动能、势能及其时间平均（位力定理）
  similar_orbits.png        力学相似性：几何相似的开普勒轨道与 T ∝ a^{3/2}

Run: python3 figures/one/make_action_figures.py [name ...]   (numpy, scipy, matplotlib, pillow)
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from scipy.integrate import solve_ivp, cumulative_trapezoid
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
    return Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[..., :3].copy())


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


# ---------------------------------------------------------------- brachistochrone race
def curve_time(x, y, g=1.0):
    """Travel time along the polyline (x, y), y measured downward, starting from rest at (x[0], y[0]=0)."""
    ds = np.hypot(np.diff(x), np.diff(y))
    ym = 0.5 * (y[1:] + y[:-1])
    dt = ds / np.sqrt(2 * g * np.maximum(ym, 1e-15))
    return np.r_[0, np.cumsum(dt)]


def brachistochrone_race():
    a = 1.0
    xB, yB = np.pi * a, 2 * a
    w = np.linspace(0, 1, 6001) ** 2           # points clustered near the start
    curves = []
    th = np.pi * w
    curves.append(("摆线（最速降线）", a * (th - np.sin(th)), a * (1 - np.cos(th)), RED))
    curves.append(("直线（最短）", xB * w, yB * w, BLUE))
    curves.append(("下凹更深的曲线", xB * w, yB * w + 1.6 * np.sin(np.pi * w), GREEN))
    xs = xB * w
    curves.append(("$y\\propto x^{2/3}$", xs, yB * (xs / xB) ** (2 / 3), ORANGE))
    data = []
    for name, x, y, c in curves:
        t = curve_time(x, y)
        data.append((name, x, y, c, t))
        print(f"{name}: T = {t[-1]:.4f}  (cycloid exact {np.pi * np.sqrt(a):.4f})")
    Tmax = max(d[4][-1] for d in data) * 1.03
    taus = np.linspace(0, Tmax, 110)
    fig, ax = plt.subplots(figsize=(8.6, 5.0), dpi=DPI)

    def draw(i, ov):
        ax.clear()
        tau = taus[i]
        for k, (name, x, y, c, t) in enumerate(data):
            ax.plot(x, -y, color=c, lw=1.6)
            j = np.searchsorted(t, tau)
            j = min(j, len(t) - 1)
            ax.plot([x[j]], [-y[j]], "o", color=c, ms=10, mec="k", mew=0.6, zorder=5)
            done = t[-1] <= tau
            ax.text(xB + 0.12, 0.05 - 0.32 * k, f"{name}：{t[-1]:.2f}" + ("　✓" if done else ""), color=c, fontsize=10.5,
                    fontweight="bold" if (done and k == 0) else "normal")
        ax.plot([0], [0], "s", color="k", ms=6); ax.text(-0.12, 0.12, "$A$", fontsize=12)
        ax.plot([xB], [-yB], "s", color="k", ms=6); ax.text(xB - 0.05, -yB - 0.3, "$B$", fontsize=12)
        ax.text(xB + 0.12, 0.4, "到达时间（单位 $\\sqrt{a/g}$）", fontsize=10.5)
        ax.text(0.05, -3.45, f"$t={tau:.2f}\\sqrt{{a/g}}$；摆线的理论值为 $\\pi\\sqrt{{a/g}}\\approx3.14\\sqrt{{a/g}}$", fontsize=10)
        ax.set_xlim(-0.3, 6.6); ax.set_ylim(-3.6, 0.6); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title("最速降线：四颗小球同时从 $A$ 静止释放，沿不同轨道无摩擦滑到 $B$", fontsize=11)
        fig.tight_layout()
    animate(fig, draw, range(len(taus)), "brachistochrone_race.gif", ms=70)


# ---------------------------------------------------------------- tautochrone
def tautochrone():
    a, g = 1.0, 1.0
    om = np.sqrt(g / (4 * a))
    th = np.linspace(0, 2 * np.pi, 600)
    cx, cy = a * (th - np.sin(th)), a * (1 + np.cos(th))
    s0s = [3.8, 2.6, 1.3]
    cols = [RED, BLUE, GREEN]
    Tq = np.pi / (2 * om)                     # quarter period = pi*sqrt(a/g)
    taus = np.linspace(0, 4 * Tq, 120)

    def pos(s):
        theta = 2 * np.arccos(np.clip(s / (4 * a), -1, 1))
        return a * (theta - np.sin(theta)), a * (1 + np.cos(theta))

    fig, axs = plt.subplots(1, 2, figsize=(10.4, 4.2), dpi=DPI, gridspec_kw={"width_ratios": [1.5, 1]})
    tt = np.linspace(0, 4 * Tq, 400)

    def draw(i, ov):
        for ax in axs:
            ax.clear()
        tau = taus[i] if not ov else Tq
        ax = axs[0]
        ax.plot(cx, cy, color=GRAY, lw=1.5)
        for s0, c in zip(s0s, cols):
            x0, y0 = pos(s0)
            ax.plot([x0], [y0], "o", color=c, ms=6, alpha=0.35)
            x, y = pos(s0 * np.cos(om * tau))
            ax.plot([x], [y], "o", color=c, ms=11, mec="k", mew=0.6, zorder=5)
        ax.plot([np.pi * a], [0], "x", color="k", ms=9)
        ax.text(np.pi * a, -0.28, "最低点", ha="center", fontsize=10)
        msg = "总览：三颗小球在 $t=\\pi\\sqrt{a/g}$ 同时到达最低点" if ov else f"$t={tau / Tq:.2f}\\times\\pi\\sqrt{{a/g}}$"
        ax.set_title(msg, fontsize=11)
        ax.set_xlim(-0.2, 2 * np.pi + 0.2); ax.set_ylim(-0.45, 2.2); ax.set_aspect("equal"); ax.axis("off")
        ax = axs[1]
        for s0, c in zip(s0s, cols):
            ax.plot(tt / Tq, s0 * np.cos(om * tt), color=c, lw=1.4)
            ax.plot([tau / Tq], [s0 * np.cos(om * tau)], "o", color=c, ms=6)
        ax.axhline(0, color=GRAY, lw=0.6)
        for k in (1, 3):
            ax.axvline(k, color=GRAY, lw=0.6, ls=":")
        ax.set_xlabel("$t\\,/\\,\\pi\\sqrt{a/g}$"); ax.set_ylabel("沿曲线到最低点的弧长 $s$")
        ax.set_title("$s(t)=s_0\\cos\\left(\\sqrt{g/4a}\\,t\\right)$：周期与 $s_0$ 无关", fontsize=10.5)
        clean(ax)
        fig.tight_layout()
    animate(fig, draw, range(len(taus)), "tautochrone.gif", ms=70)


# ---------------------------------------------------------------- action landscape
def action_landscape():
    cases = [dict(T=2.0, title="$t_2-t_1=2<\\pi$：真实路径使 $S$ 取极小", col=BLUE),
             dict(T=4.0, title="$t_2-t_1=4>\\pi$：真实路径不再是极小，只是平稳", col=RED)]
    for c in cases:
        T = c["T"]
        t = np.linspace(0, T, 600)
        q0 = np.sin(t) / np.sin(T)
        eta = np.sin(np.pi * t / T)
        def S(eps, t=t, q0=q0, eta=eta):
            q = q0 + eps * eta
            qd = np.gradient(q, t)
            return np.trapezoid(0.5 * qd ** 2 - 0.5 * q ** 2, t)
        c.update(t=t, q0=q0, eta=eta, S=S, S0=S(0.0))
        c["S2"] = 0.5 * ((np.pi / T) ** 2 - 1) * T / 2
        print(T, "S(0.5)-S(0)", S(0.5) - S(0), "predicted", 0.25 * c["S2"])
    epss = 0.8 * np.sin(np.linspace(0, 2 * np.pi, 90, endpoint=False))
    fig = plt.figure(figsize=(10.4, 6.4), dpi=DPI)
    axes = [(fig.add_axes([0.07, 0.56 - 0.48 * k, 0.5, 0.34]), fig.add_axes([0.66, 0.56 - 0.48 * k, 0.31, 0.34])) for k in range(2)]
    eg = np.linspace(-0.85, 0.85, 200)

    def draw(i, ov):
        for c, (a1, a2) in zip(cases, axes):
            a1.clear(); a2.clear()
            t = c["t"]
            for e in np.linspace(-0.8, 0.8, 9):
                a1.plot(t, c["q0"] + e * c["eta"], color=GRAY, lw=0.6, alpha=0.5)
            a1.plot(t, c["q0"], color="k", lw=2.0, label="真实路径")
            if not ov:
                a1.plot(t, c["q0"] + epss[i] * c["eta"], color=c["col"], lw=1.8, label="试探路径")
            a1.plot([0, c["T"]], [0, 1], "o", color="k", ms=5)
            a1.set_xlabel("$t$", labelpad=0); a1.set_ylabel("$q$")
            a1.set_title(c["title"], fontsize=10.5, loc="left")
            a1.legend(loc="lower left" if c["T"] < 3 else "upper left", fontsize=9, frameon=False)
            clean(a1)
            Sg = np.array([c["S"](e) for e in eg])
            a2.plot(eg, Sg - c["S0"], color=c["col"], lw=1.6)
            a2.axvline(0, color="k", lw=0.8, ls=":")
            if not ov:
                a2.plot([epss[i]], [c["S"](epss[i]) - c["S0"]], "o", color=c["col"], ms=7)
            a2.set_xlabel("$\\varepsilon$", labelpad=0); a2.set_ylabel("$S(\\varepsilon)-S(0)$")
            clean(a2)
        fig.text(0.5, 0.01, "谐振子 $L=\\frac{1}{2}\\dot q^2-\\frac{1}{2}q^2$，端点固定 $q(0)=0$、$q(t_2)=1$；试探路径 $q_0(t)+\\varepsilon\\sin(\\pi t/t_2)$，$q_0$ 为真实路径",
                 ha="center", fontsize=10, color="#333333")
        for txt in fig.texts[:-1]:
            txt.remove()
    animate(fig, draw, range(len(epss)), "action_landscape.gif", ms=80, overview=0)


# ---------------------------------------------------------------- static: virial
def kepler_E(M, e):
    E = np.array(M, dtype=float).copy()
    for _ in range(60):
        E = E - (E - e * np.sin(E) - M) / (1 - e * np.cos(E))
    return E


def virial_kepler():
    a, e = 1.0, 0.7
    t = np.linspace(1e-4, 4 * 2 * np.pi, 8000)
    E = kepler_E(t, e)
    r = a * (1 - e * np.cos(E))
    v2 = 2 / r - 1 / a
    T, U = 0.5 * v2, -1 / r
    Tbar = cumulative_trapezoid(T, t, initial=0) / np.maximum(t - t[0], 1e-9)
    Ubar = cumulative_trapezoid(U, t, initial=0) / np.maximum(t - t[0], 1e-9)
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1, 2]})
    ax = axs[0]
    EE = np.linspace(0, 2 * np.pi, 400)
    ax.plot(a * (np.cos(EE) - e), a * np.sqrt(1 - e * e) * np.sin(EE), color=GRAY, lw=1.4)
    ax.plot([0], [0], "o", color=ORANGE, ms=10)
    ax.text(-1.7, -0.85, "开普勒轨道 $e=0.7$\n近日点快，动能大\n远日点慢，动能小", fontsize=10, va="top")
    ax.set_ylim(-1.5, 0.8)
    ax.set_aspect("equal"); ax.axis("off")
    ax = axs[1]
    P = t / (2 * np.pi)
    ax.plot(P, T, color=RED, lw=0.9, alpha=0.6, label="动能 $T(t)$")
    ax.plot(P, U, color=BLUE, lw=0.9, alpha=0.6, label="势能 $U(t)$")
    ax.plot(P, Tbar, color=RED, lw=2, label="$T$ 的累积时间平均")
    ax.plot(P, Ubar, color=BLUE, lw=2, label="$U$ 的累积时间平均")
    ax.axhline(-0.5, color="k", lw=1, ls="--"); ax.text(4.02, -0.5, "$E=-1/2a$", va="center", fontsize=10)
    ax.axhline(0.5, color=RED, lw=0.8, ls=":"); ax.text(4.02, 0.5, "$\\overline{T}=-E$", va="center", fontsize=10, color=RED)
    ax.axhline(-1.0, color=BLUE, lw=0.8, ls=":"); ax.text(4.02, -1.0, "$\\overline{U}=2E$", va="center", fontsize=10, color=BLUE)
    ax.set_ylim(-3.2, 3.2); ax.set_xlim(0, 4)
    ax.set_xlabel("时间（以轨道周期为单位）"); ax.set_ylabel("单位质量的能量（$GM=a=1$）")
    ax.legend(loc="upper right", fontsize=9, frameon=False, ncol=2)
    ax.set_title("$T$、$U$ 剧烈变化，但时间平均满足 $2\\overline{T}=-\\overline{U}$", fontsize=11, loc="left")
    clean(ax)
    fig.tight_layout()
    savefig(fig, "virial_kepler.png")


def similar_orbits():
    e = 0.5
    fig, ax = plt.subplots(figsize=(8.4, 5.2))
    for a, c in ((1.0, BLUE), (2.0, RED)):
        EE = np.linspace(0, 2 * np.pi, 400)
        ax.plot(a * (np.cos(EE) - e), a * np.sqrt(1 - e * e) * np.sin(EE), color=c, lw=1.6)
        Tper = 2 * np.pi * a ** 1.5
        for k in range(8):
            Ek = kepler_E(np.array([2 * np.pi * k / 8]), e)[0]
            x, y = a * (np.cos(Ek) - e), a * np.sqrt(1 - e * e) * np.sin(Ek)
            ax.plot([x], [y], "o", color=c, ms=5)
            if a == 2.0 and k in (0, 2, 4, 6):
                lab = {0: "$t=0$", 2: "$T_2/4$", 4: "$T_2/2$", 6: "$3T_2/4$"}[k]
                off = {0: (0.12, 0.0), 2: (0.0, 0.18), 4: (-0.15, 0.22), 6: (0.0, -0.3)}[k]
                ax.text(x + off[0], y + off[1], lab, color=c, fontsize=10, ha="left" if k == 0 else "center", va="center")
        ax.text(-a * (1 + e) + (0.15 if a == 1 else -0.12), -0.45 if a == 2 else 0.0, f"$a={a:g}$\n$T={Tper / (2 * np.pi):.2f}\\times2\\pi$", color=c, fontsize=10,
                ha="left" if a == 1 else "right", va="center")
    ax.plot([0], [0], "o", color=ORANGE, ms=10)
    ax.text(-5.6, 2.75, "两条轨道几何相似（线度相差 2 倍），点是每隔 1/8 周期的位置\n"
            "$U\\propto r^{-1}$（$k=-1$）$\\Rightarrow$ $t'/t=(l'/l)^{3/2}$：$T_2/T_1=2^{3/2}\\approx2.83$", fontsize=10.5, va="top")
    ax.set_xlim(-5.6, 1.9); ax.set_ylim(-2.1, 2.8); ax.set_aspect("equal"); ax.axis("off")
    savefig(fig, "similar_orbits.png")


ALL = {f.__name__: f for f in (brachistochrone_race, tautochrone, action_landscape, virial_kepler, similar_orbits)}
if __name__ == "__main__":
    for name in sys.argv[1:] or ALL:
        ALL[name]()
