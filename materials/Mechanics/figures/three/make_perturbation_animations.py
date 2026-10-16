# GIF animations for 微扰和摄动理论.md (teaching enhancements, 2026-10)
# 每个 GIF 的第 0 帧是“总览帧”（停留较久），PDF 中只显示这一帧。
#   beats_to_resonance.gif   失谐减小：拍 → 共振时的线性增长
#   pendulum_amplitudes.gif  不同振幅的单摆逐渐失去同步（非谐振动）
#   hilda_rotating.gif       木星共转系中的 3:2 共振（希尔达型）与非共振轨道
#   coupled_beats.gif        弱耦合振子之间的能量转移
#   normal_modes.gif         两个简正模（同相 / 反相）
#   swing_parametric.gif     变摆长单摆（荡秋千）的参数共振
#   mercury_rosette.gif      近日点进动（GR 修正已放大）
#   osculating_ellipse.gif   受第三体摄动的轨道与密切椭圆
#   io_spiral.gif            复振幅螺旋收缩到受迫解（木卫一偏心率矢量）
# 用法：python3 make_perturbation_animations.py [名字 ...]   （不带参数则全部生成）
import os, sys
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle, Circle
from scipy.integrate import solve_ivp, cumulative_trapezoid
from PIL import Image

for f in font_manager.findSystemFonts():
    if "NotoSansCJK-Regular" in f:
        font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": ["Noto Sans CJK SC"], "mathtext.fontset": "cm",
                     "axes.unicode_minus": False, "font.size": 11})
OUT = os.path.dirname(os.path.abspath(__file__)) + "/"
BLUE = "#1f4e9c"; RED = "#c8102e"; ORANGE = "#e08a00"; GREEN = "#2e7d32"; GRAY = "#777777"
DPI = 90


def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def grab(fig):
    fig.canvas.draw()
    return Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[..., :3].copy())


def save_gif(frames, name, ms=60, hold=3000):
    pal = [im.convert("P", palette=Image.ADAPTIVE, colors=128) for im in frames]
    dur = [hold] + [ms] * (len(pal) - 1)
    pal[0].save(OUT + name, save_all=True, append_images=pal[1:], duration=dur, loop=0, optimize=True, disposal=1)
    print(name, len(frames), "frames", round(os.path.getsize(OUT + name) / 1e6, 2), "MB")


def make(fig, draw, idx, name, ms=60, overview=None):
    """draw(i) redraws everything for frame i; overview = index used for frame 0."""
    frames = []
    ov = idx[-1] if overview is None else overview
    draw(ov, True); frames.append(grab(fig))
    for i in idx:
        draw(i, False); frames.append(grab(fig))
    plt.close(fig)
    save_gif(frames, name, ms)


def ode(f, t, y0, **kw):
    return solve_ivp(f, (t[0], t[-1]), y0, t_eval=t, rtol=1e-10, atol=1e-12, method="DOP853", **kw).y


def spring(ax, x0, x1, y, color, n=10, amp=0.13, lw=1.4):
    xs = np.linspace(x0, x1, 2 * n + 3)
    ys = np.full_like(xs, y)
    ys[2:-2:2] += amp; ys[3:-2:2] -= amp
    ax.plot(xs, ys, color=color, lw=lw, solid_joinstyle="round")


def wall(ax, x, y, side):
    ax.plot([x, x], [y - 0.55, y + 0.55], color="k", lw=2.5)
    for d in np.linspace(-0.5, 0.4, 6):
        ax.plot([x, x + side * 0.25], [y + d, y + d - 0.15], color="k", lw=0.8)


def two_masses(ax, y, x1, x2, ccoup=RED, label=None):
    p1, p2 = 3 + x1, 7 + x2
    wall(ax, 0, y, -1); wall(ax, 10, y, 1)
    spring(ax, 0, p1 - 0.45, y, BLUE)
    spring(ax, p1 + 0.45, p2 - 0.45, y, ccoup, n=12)
    spring(ax, p2 + 0.45, 10, y, BLUE)
    for p in (p1, p2):
        ax.add_patch(Rectangle((p - 0.45, y - 0.4), 0.9, 0.8, fc="#dbe4f3", ec=BLUE, lw=1.4))
        ax.text(p, y, "$m$", ha="center", va="center", fontsize=12)
    for p0 in (3, 7):
        ax.plot([p0, p0], [y - 0.62, y - 0.48], color=GRAY, lw=1)


# ---------------------------------------------------------------- 1
def beats():
    t = np.linspace(0, 120, 3000)
    Ds = 0.1 * np.linspace(1, 0, 70) ** 1.6
    Ds[0] = 0.1
    Ds = np.concatenate([Ds, np.zeros(12)])
    fig, ax = plt.subplots(figsize=(9, 3.9), dpi=DPI)

    def xsol(D):
        if D < 1e-9:
            return t * np.sin(t) / 2, t / 2
        g = 1 - D
        return (np.cos(g * t) - np.cos(t)) / (1 - g * g), 2 * np.abs(np.sin(D * t / 2)) / (1 - g * g)

    def draw(i, ov):
        ax.clear(); D = Ds[i]
        ax.plot(t, t / 2, color=GRAY, ls=":", lw=1); ax.plot(t, -t / 2, color=GRAY, ls=":", lw=1)
        if ov:
            for Dg, c in ((0.08, GREEN), (0.04, ORANGE)):
                _, e = xsol(Dg); ax.plot(t, e, color=c, lw=1.4, ls="--")
                ax.text(t[np.argmax(e)], e.max() + 1.5, f"$\\gamma/\\omega={1 - Dg:.2f}$", color=c, ha="center", fontsize=10,
                        bbox=dict(fc="white", ec="none", pad=0.3))
        x, e = xsol(D)
        ax.plot(t, x, color=RED, lw=1.0)
        ax.plot(t, e, color=BLUE, lw=1.3, ls="--"); ax.plot(t, -e, color=BLUE, lw=1.3, ls="--")
        lab = "$\\gamma=\\omega$：共振，振幅 $\\propto t$" if D < 1e-9 else \
            f"$\\gamma/\\omega={1 - D:.3f}$，拍周期 $2\\pi/|\\omega-\\gamma|={2 * np.pi / D:.0f}$"
        ax.text(2, 55, lab, fontsize=12, color=BLUE)
        ax.text(2, 47, "灰色点线：共振包络 $\\pm\\frac{f}{2m\\omega}t$", fontsize=9.5, color=GRAY)
        if ov:
            ax.text(2, 39, "总览：失谐越小，拍的包络越高、越慢；$\\gamma\\to\\omega$ 时变为线性增长", fontsize=10)
        ax.set_xlim(0, 120); ax.set_ylim(-62, 62)
        ax.set_xlabel("$\\omega t$"); ax.set_ylabel("$x$（单位 $f/m\\omega^2$）"); clean(ax)
        fig.tight_layout()
    make(fig, draw, range(len(Ds)), "beats_to_resonance.gif", ms=90)


# ---------------------------------------------------------------- 2
def pendulums():
    amps = [(10, GREEN), (90, BLUE), (150, RED)]
    t = np.linspace(0, 4 * 2 * np.pi, 600)
    sols = [ode(lambda t, y: [y[1], -np.sin(y[0])], t, [np.radians(a), 0])[0] for a, _ in amps]
    fig = plt.figure(figsize=(9, 5.4), dpi=DPI)
    ax1 = fig.add_axes([0.02, 0.42, 0.96, 0.56]); ax2 = fig.add_axes([0.09, 0.09, 0.88, 0.3])
    idx = np.arange(0, 600, 5)

    def draw(i, ov):
        ax1.clear(); ax2.clear()
        for k, ((a, c), th) in enumerate(zip(amps, sols)):
            px = -3.2 + 3.2 * k; py = 0
            ax1.plot([px - 0.5, px + 0.5], [py, py], color="k", lw=2)
            bx, by = px + np.sin(th[i]), py - np.cos(th[i])
            ax1.plot([px, bx], [py, by], color="k", lw=1.2)
            ax1.add_patch(Circle((bx, by), 0.12, color=c, zorder=5))
            arc = np.linspace(-np.radians(a), np.radians(a), 60)
            ax1.plot(px + np.sin(arc), py - np.cos(arc), color=c, lw=0.8, ls=":")
            ax1.text(px, py - 1.32, f"$\\theta_0={a}^\\circ$", ha="center", color=c, fontsize=12)
            ax2.plot(t[:i + 1] / (2 * np.pi), th[:i + 1] / np.radians(a), color=c, lw=1.5)
        ax1.text(0, 1.05, f"$t={t[i] / (2 * np.pi):.2f}\\,T_0$（$T_0=2\\pi\\sqrt{{l/g}}$，同时释放）", ha="center", fontsize=11)
        ax1.set_xlim(-4.6, 4.6); ax1.set_ylim(-1.5, 1.2); ax1.set_aspect("equal"); ax1.axis("off")
        ax2.set_xlim(0, 4); ax2.set_ylim(-1.1, 1.1)
        ax2.set_xlabel("$t/T_0$"); ax2.set_ylabel("$\\theta/\\theta_0$"); clean(ax2)
        ax2.text(4, 1.12, "振幅越大，周期越长：10° 几乎等时，150° 的周期约为 $1.76\\,T_0$", ha="right", va="bottom", fontsize=9.5)
    make(fig, draw, idx, "pendulum_amplitudes.gif", ms=55)


# ---------------------------------------------------------------- 3
def kepler_xy(a, e, n, t, pomega=0.0, M0=0.0):
    M = n * t + M0
    E = M.copy()
    for _ in range(50):
        E = E - (E - e * np.sin(E) - M) / (1 - e * np.cos(E))
    r = a * (1 - e * np.cos(E))
    f = 2 * np.arctan2(np.sqrt(1 + e) * np.sin(E / 2), np.sqrt(1 - e) * np.cos(E / 2))
    return r, f + pomega


def hilda():
    aJ, nJ = 5.2, 2 * np.pi
    t = np.linspace(0, 12, 2400)
    cases = []
    for ratio, e, c in ((1.5, 0.2, BLUE), (1.57, 0.2, GREEN)):
        n = ratio * nJ; a = aJ * ratio ** (-2 / 3)
        r, lam = kepler_xy(a, e, n, t)
        th = lam - nJ * t
        x, y = r * np.cos(th), r * np.sin(th)
        rel = np.unwrap(lam) - nJ * t  # conjunction when rel = 2πk
        k = np.floor(rel / (2 * np.pi))
        conj = np.where(np.diff(k) != 0)[0]
        cases.append((ratio, a, e, x, y, conj, c))
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 5.0), dpi=DPI)
    idx = np.arange(0, 2400, 16)

    def draw(i, ov):
        for ax, (ratio, a, e, x, y, conj, c) in zip(axs, cases):
            ax.clear()
            ph = np.linspace(0, 2 * np.pi, 200)
            ax.plot(aJ * np.cos(ph), aJ * np.sin(ph), color=ORANGE, ls=":", lw=0.9)
            ax.plot([0], [0], "o", color=ORANGE, ms=10)
            ax.plot([aJ], [0], "o", color=ORANGE, ms=9, mec="k", mew=0.6)
            ax.text(aJ, -0.65, "木星\n（在此系中静止）", ha="center", va="top", fontsize=9, color="#8a5a00")
            ax.plot(x[:i + 1], y[:i + 1], color=c, lw=0.7, alpha=0.75)
            ax.plot([x[i]], [y[i]], "o", color=c, ms=6)
            cc = conj[conj <= i]
            ax.plot(x[cc], y[cc], "*", color=RED, ms=10, zorder=6)
            ax.set_xlim(-6.2, 6.2); ax.set_ylim(-6.2, 6.2); ax.set_aspect("equal"); ax.axis("off")
            if ratio == 1.5:
                ax.set_title("3:2 共振（希尔达型）\n会合（★）总在近日点，离木星最远", fontsize=11)
            else:
                ax.set_title(f"非共振 $n/n_{{\\rm J}}={ratio}$\n每次会合时离木星时远时近，迟早被近距离摄动", fontsize=11)
        fig.text(0.5, 0.03, f"木星共转参照系，$t={t[i]:.1f}\\,P_{{\\rm J}}$（开普勒轨道示意，未计入木星引力）",
                 ha="center", fontsize=10, color=GRAY)
        fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.07, wspace=0.04)
        for txt in fig.texts[:-1]:
            txt.remove()
    make(fig, draw, idx, "hilda_rotating.gif", ms=60)


# ---------------------------------------------------------------- 4
def coupled():
    k, kap = 1.0, 0.08
    w1, w2 = 1.0, np.sqrt(1 + 2 * kap)
    Tex = 2 * np.pi / (w2 - w1)
    t = np.linspace(0, Tex, 1600)
    x1 = 0.5 * (np.cos(w1 * t) + np.cos(w2 * t)); x2 = 0.5 * (np.cos(w1 * t) - np.cos(w2 * t))
    v1 = -0.5 * (w1 * np.sin(w1 * t) + w2 * np.sin(w2 * t)); v2 = -0.5 * (w1 * np.sin(w1 * t) - w2 * np.sin(w2 * t))
    E1 = 0.5 * v1 ** 2 + 0.5 * k * x1 ** 2; E2 = 0.5 * v2 ** 2 + 0.5 * k * x2 ** 2
    Et = E1 + E2
    fig = plt.figure(figsize=(9, 6.0), dpi=DPI)
    a0 = fig.add_axes([0.03, 0.72, 0.94, 0.26]); a1 = fig.add_axes([0.09, 0.40, 0.88, 0.27]); a2 = fig.add_axes([0.09, 0.08, 0.88, 0.25])
    idx = np.arange(0, 1600, 10)

    def draw(i, ov):
        for ax in (a0, a1, a2):
            ax.clear()
        two_masses(a0, 0, 1.1 * x1[i], 1.1 * x2[i])
        a0.text(5, 0.75, f"弱耦合 $\\kappa=0.08\\,k$；只拨动左边的质点。$t={t[i]:.0f}$", ha="center", fontsize=11)
        a0.set_xlim(-0.5, 10.5); a0.set_ylim(-0.75, 1.05); a0.axis("off")
        j = slice(0, i + 1)
        a1.plot(t[j], x1[j], color=BLUE, lw=1, label="$x_1$"); a1.plot(t[j], x2[j], color=RED, lw=1, label="$x_2$")
        a1.set_xlim(0, Tex); a1.set_ylim(-1.1, 1.1); a1.set_ylabel("位移"); a1.legend(loc="upper right", fontsize=9, frameon=False, ncol=2)
        a2.plot(t[j], E1[j] / Et[j], color=BLUE, lw=1.6, label="质点 1 的能量")
        a2.plot(t[j], E2[j] / Et[j], color=RED, lw=1.6, label="质点 2 的能量")
        a2.set_xlim(0, Tex); a2.set_ylim(-0.03, 1.05); a2.set_xlabel("$\\omega_1t$"); a2.set_ylabel("$E_i/E$")
        a2.legend(loc="center right", fontsize=9, frameon=False)
        a2.text(Tex * 0.02, -0.02, f"能量来回交换一次的周期 $2\\pi/(\\omega_2-\\omega_1)\\approx{Tex:.0f}$", ha="left", va="bottom", fontsize=9.5, color=GRAY)
        clean(a1); clean(a2)
    make(fig, draw, idx, "coupled_beats.gif", ms=60)


# ---------------------------------------------------------------- 5
def normal_modes():
    w1, w2 = 1.0, 1.5
    t = np.linspace(0, 4 * np.pi, 96, endpoint=False)
    fig, ax = plt.subplots(figsize=(8.4, 4.0), dpi=DPI)

    def draw(i, ov):
        ax.clear()
        A = 0.9
        c1 = A * np.cos(w1 * t[i]); c2 = A * np.cos(w2 * t[i])
        two_masses(ax, 2.4, c1, c1)
        two_masses(ax, 0, c2, -c2)
        ax.text(-0.4, 3.25, "简正模 1（同相）：$\\omega_1=\\sqrt{k/m}$，中间弹簧不伸缩", fontsize=11, color=BLUE)
        ax.text(-0.4, 0.85, "简正模 2（反相）：$\\omega_2=\\sqrt{(k+2\\kappa)/m}$", fontsize=11, color=RED)
        ax.text(10.4, -1.05, "此处取 $\\kappa=\\frac{5}{8}k$，使 $\\omega_2=1.5\\,\\omega_1$：模 1 振 2 次，模 2 振 3 次",
                fontsize=9.5, color=GRAY, ha="right")
        ax.set_xlim(-0.5, 10.5); ax.set_ylim(-1.2, 3.5); ax.axis("off")
        fig.tight_layout()
    make(fig, draw, range(len(t)), "normal_modes.gif", ms=70, overview=0)


# ---------------------------------------------------------------- 6
def swing():
    eta = 0.05
    L = lambda t: 1 + eta * np.cos(2 * t)
    Ld = lambda t: -2 * eta * np.sin(2 * t)
    T = 12 * 2 * np.pi
    t = np.linspace(0, T, 2400)
    th = ode(lambda t, y: [y[1], -np.sin(y[0]) / L(t) - 2 * Ld(t) / L(t) * y[1]], t, [np.radians(3), 0])[0]
    fig = plt.figure(figsize=(9.6, 4.6), dpi=DPI)
    ax0 = fig.add_axes([0.0, 0.05, 0.36, 0.9]); a1 = fig.add_axes([0.45, 0.42, 0.53, 0.5]); a2 = fig.add_axes([0.45, 0.12, 0.53, 0.2])
    idx = np.arange(0, 2400, 12)
    print("swing max deg", np.degrees(np.abs(th).max()))

    def draw(i, ov):
        for ax in (ax0, a1, a2):
            ax.clear()
        l = L(t[i]); bx, by = l * np.sin(th[i]), -l * np.cos(th[i])
        j0 = max(0, i - 120)
        ax0.plot(L(t[j0:i + 1]) * np.sin(th[j0:i + 1]), -L(t[j0:i + 1]) * np.cos(th[j0:i + 1]), color=BLUE, lw=0.8, alpha=0.5)
        ax0.plot([-0.4, 0.4], [0, 0], color="k", lw=2.5)
        ax0.plot([0, bx], [0, by], color="k", lw=1.3)
        ax0.add_patch(Circle((bx, by), 0.07, color=RED, zorder=5))
        ax0.text(0, -1.4, "最低点：重心上移（摆长变短）\n最高点：重心下移（摆长变长）", ha="center", fontsize=9.5)
        ax0.set_xlim(-0.95, 0.95); ax0.set_ylim(-1.55, 0.1); ax0.set_aspect("equal"); ax0.axis("off")
        j = slice(0, i + 1); X = t / (2 * np.pi)
        a1.plot(X[j], np.degrees(th[j]), color=RED, lw=1.1)
        a1.set_xlim(0, 12); a1.set_ylim(-45, 45); a1.set_ylabel("$\\theta$ (°)")
        a1.set_title("摆长以 $2\\omega_0$ 调制：$l=l_0(1+0.05\\cos2\\omega_0t)$，摆幅指数增长", fontsize=10.5, loc="left")
        a2.plot(X[j], L(t[j]), color=GREEN, lw=1.1)
        a2.set_xlim(0, 12); a2.set_ylim(0.93, 1.07); a2.set_ylabel("$l/l_0$"); a2.set_xlabel("$t/T_0$")
        clean(a1); clean(a2)
    make(fig, draw, idx, "swing_parametric.gif", ms=55)


# ---------------------------------------------------------------- 7
def rosette():
    k2, e = 0.01, 0.5
    norb = 16
    ph = np.linspace(0, norb * 2 * np.pi * 1.06, 40000)
    u = ode(lambda p, y: [y[1], -y[0] + k2 + 3 * y[0] ** 2], ph, [k2 * (1 + e), 0])[0]
    tt = cumulative_trapezoid(1 / u ** 2, ph, initial=0)  # J=1 up to scale
    r = 1 / u; x, y = r * np.cos(ph), r * np.sin(ph)
    # perihelia: local maxima of u
    pk = np.where((u[1:-1] > u[:-2]) & (u[1:-1] >= u[2:]))[0] + 1
    pk = np.concatenate([[0], pk])
    tf = tt[pk[min(norb, len(pk) - 1)]]
    ts = np.linspace(0, tf, 240)
    ii = np.searchsorted(tt, ts).clip(0, len(tt) - 1)
    fig, ax = plt.subplots(figsize=(6.4, 6.6), dpi=DPI)
    R = (1 / k2) / (1 - e) * 1.05
    dphi = 6 * np.pi * k2

    def draw(n, ov):
        ax.clear(); i = ii[n]
        ax.plot(x[:i + 1], y[:i + 1], color=BLUE, lw=0.9)
        ax.plot([0], [0], "o", color=ORANGE, ms=12)
        pp = pk[pk <= i]
        for m, q in enumerate(pp):
            ax.plot([0, x[q]], [0, y[q]], color=RED, lw=0.8, alpha=0.8)
            ax.plot([x[q]], [y[q]], "o", color=RED, ms=5)
        ax.plot([x[i]], [y[i]], "o", color="k", ms=6)
        nn = len(pp) - 1
        tot = np.degrees(np.arctan2(y[pp[-1]], x[pp[-1]])) % 360
        avg = f"，平均每圈 {tot / nn:.1f}°" if nn > 0 else ""
        ax.text(0.02, 0.98, f"已完成 {max(nn, 0)} 圈，近日点累计前移 {tot:.0f}°{avg}",
                transform=ax.transAxes, va="top", fontsize=11)
        ax.text(0.02, 0.92, f"一阶公式 $6\\pi(GM/J)^2={np.degrees(dphi):.1f}^\\circ$/圈（略小，差别来自高阶修正）",
                transform=ax.transAxes, va="top", fontsize=10, color=RED)
        ax.text(0.02, 0.86, "为便于观察取 $(GM/J)^2=0.01$（水星约 $2.7\\times10^{-8}$，修正放大约 $4\\times10^5$ 倍）",
                transform=ax.transAxes, va="top", fontsize=9, color=GRAY)
        ax.set_xlim(-R * 1.02, R * 1.02); ax.set_ylim(-R * 1.03, R * 1.0); ax.set_aspect("equal"); ax.axis("off")
        fig.tight_layout()
    make(fig, draw, range(len(ts)), "mercury_rosette.gif", ms=60)


# ---------------------------------------------------------------- 8
def osculating():
    mp, rp = 0.3, 3.0
    npl = np.sqrt((1 + mp) / rp ** 3)
    def rhs(t, s):
        x, y, vx, vy = s
        r3 = (x * x + y * y) ** 1.5
        X, Y = rp * np.cos(npl * t), rp * np.sin(npl * t)
        dx, dy = X - x, Y - y; d3 = (dx * dx + dy * dy) ** 1.5
        ax_ = -x / r3 + mp * (dx / d3 - X / rp ** 3); ay_ = -y / r3 + mp * (dy / d3 - Y / rp ** 3)
        return [vx, vy, ax_, ay_]
    T = 10 * 2 * np.pi
    t = np.linspace(0, T, 3000)
    e0 = 0.2
    s = ode(rhs, t, [1 - e0, 0, 0, np.sqrt((1 + e0) / (1 - e0))])
    x, y, vx, vy = s
    r = np.hypot(x, y); h = x * vy - y * vx
    ex = vy * h - x / r; ey = -vx * h - y / r
    ecc = np.hypot(ex, ey); pom = np.unwrap(np.arctan2(ey, ex))
    aa = 1 / (2 / r - (vx ** 2 + vy ** 2))
    print("osc e range", ecc.min(), ecc.max(), "pomega drift deg", np.degrees(pom[-1] - pom[0]))
    fig = plt.figure(figsize=(9.6, 4.8), dpi=DPI)
    a0 = fig.add_axes([0.0, 0.03, 0.46, 0.92]); a1 = fig.add_axes([0.56, 0.56, 0.42, 0.36]); a2 = fig.add_axes([0.56, 0.12, 0.42, 0.33])
    idx = np.arange(0, 3000, 20)
    X = t / (2 * np.pi)

    def draw(i, ov):
        for ax in (a0, a1, a2):
            ax.clear()
        j0 = max(0, i - 400)
        a0.plot(x[j0:i + 1], y[j0:i + 1], color=BLUE, lw=0.9, alpha=0.6)
        E = np.linspace(0, 2 * np.pi, 200); ai, ei, wi = aa[i], ecc[i], pom[i]
        xe, ye = ai * (np.cos(E) - ei), ai * np.sqrt(1 - ei ** 2) * np.sin(E)
        a0.plot(xe * np.cos(wi) - ye * np.sin(wi), xe * np.sin(wi) + ye * np.cos(wi), color=ORANGE, lw=1.6, ls="--")
        a0.plot([0], [0], "o", color=ORANGE, ms=11)
        a0.plot([x[i]], [y[i]], "o", color=BLUE, ms=6)
        Xp, Yp = rp * np.cos(npl * t[i]), rp * np.sin(npl * t[i])
        a0.plot([Xp], [Yp], "o", color=RED, ms=8)
        ph = np.linspace(0, 2 * np.pi, 200); a0.plot(rp * np.cos(ph), rp * np.sin(ph), color=RED, ls=":", lw=0.8)
        qx, qy = ai * (1 - ei) * np.cos(wi), ai * (1 - ei) * np.sin(wi)
        a0.plot([0, qx], [0, qy], color=GREEN, lw=1.2)
        a0.text(-3.25, 3.3, "蓝：真实轨道　橙虚线：此刻的密切椭圆\n绿：密切近心点方向　红：摄动天体", fontsize=9.5, va="top")
        a0.set_xlim(-3.3, 3.3); a0.set_ylim(-3.3, 3.3); a0.set_aspect("equal"); a0.axis("off")
        j = slice(0, i + 1)
        a1.plot(X[j], ecc[j], color=BLUE, lw=1.1); a1.set_xlim(0, 10); a1.set_ylim(0, 0.3)
        a1.set_ylabel("密切偏心率 $e$"); a1.set_title("密切轨道根数：短周期起伏 + 长期变化", fontsize=10.5, loc="left")
        a2.plot(X[j], np.degrees(pom[j] - pom[0]), color=GREEN, lw=1.1); a2.set_xlim(0, 10)
        a2.set_ylim(min(0, np.degrees(pom - pom[0]).min()) - 5, np.degrees(pom - pom[0]).max() + 5)
        a2.set_ylabel("近心点经度 $\\varpi$ (°)"); a2.set_xlabel("圈数")
        clean(a1); clean(a2)
        fig.text(0.56, 0.005, f"摄动体质量 $m'={mp}M$、轨道半径 $3a$（为便于观察而夸大）", fontsize=9, color=GRAY)
        for txt in fig.texts[:-1]:
            txt.remove()
    make(fig, draw, idx, "osculating_ellipse.gif", ms=60)


# ---------------------------------------------------------------- 9
def io_spiral():
    Dl, lam = 0.3, 0.035
    Af = 1j * 1.0
    A0 = 2.6 + 0.6j
    t = np.linspace(0, 90, 1800)
    A = Af + (A0 - Af) * np.exp((1j * Dl - lam) * t)
    fig = plt.figure(figsize=(9.6, 4.4), dpi=DPI)
    a0 = fig.add_axes([0.04, 0.1, 0.42, 0.82]); a1 = fig.add_axes([0.57, 0.16, 0.41, 0.72])
    idx = np.arange(0, 1800, 12)

    def draw(i, ov):
        a0.clear(); a1.clear()
        a0.plot(A.real[:i + 1], A.imag[:i + 1], color=BLUE, lw=1.0)
        a0.annotate("", xy=(A.real[i], A.imag[i]), xytext=(0, 0), arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=1.4))
        a0.annotate("", xy=(Af.real, Af.imag), xytext=(0, 0), arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.2, ls="--"))
        a0.plot([Af.real], [Af.imag], "*", color=RED, ms=14, zorder=6)
        a0.text(Af.real + 0.15, Af.imag + 0.18, "受迫解 $A_{\\rm f}$", color=RED, fontsize=10)
        a0.plot([A0.real], [A0.imag], "o", color=GRAY, ms=5); a0.text(A0.real, A0.imag + 0.25, "初始", color=GRAY, ha="center", fontsize=9)
        a0.axhline(0, color="k", lw=0.5); a0.axvline(0, color="k", lw=0.5)
        a0.set_xlim(-2.2, 3.2); a0.set_ylim(-1.6, 3.6); a0.set_aspect("equal")
        a0.set_xlabel("$\\mathrm{Re}\\,A$"); a0.set_ylabel("$\\mathrm{Im}\\,A$")
        a0.set_title("复振幅 $A$（偏心率矢量 $e\\,e^{i\\varpi}$）", fontsize=10.5)
        a1.plot(t[:i + 1], np.abs(A[:i + 1]), color=BLUE, lw=1.3)
        a1.axhline(abs(Af), color=RED, ls="--", lw=1)
        env = np.abs(A0 - Af) * np.exp(-lam * t)
        a1.plot(t, abs(Af) + env, color=GRAY, ls=":", lw=0.9); a1.plot(t, np.maximum(abs(Af) - env, 0), color=GRAY, ls=":", lw=0.9)
        a1.text(88, abs(Af) + 0.07, "$|A_{\\rm f}|$：由外力维持，不衰减", color=RED, ha="right", fontsize=9.5)
        a1.text(25, 3.15, "自由部分 $\\propto e^{-\\lambda t}$ 绕 $A_{\\rm f}$ 旋转并衰减", fontsize=9.5, color=GRAY)
        a1.set_xlim(0, 90); a1.set_ylim(0, 3.5); a1.set_xlabel("$t$（任意单位）"); a1.set_ylabel("$|A|$（偏心率）")
        clean(a1)
    make(fig, draw, idx, "io_spiral.gif", ms=55)


ALL = {"beats": beats, "pendulums": pendulums, "hilda": hilda, "coupled": coupled, "normal_modes": normal_modes,
       "swing": swing, "rosette": rosette, "osculating": osculating, "io_spiral": io_spiral}
if __name__ == "__main__":
    for name in (sys.argv[1:] or ALL):
        ALL[name]()
