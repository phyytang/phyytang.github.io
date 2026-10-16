"""Additional teaching media for 哈密顿力学.md (second round).

Outputs (in this folder):
  pendulum_separatrix.gif   单摆相图、分离曲线与周期发散
  magnetic_mirror.gif       磁镜中的回旋粒子与磁矩的绝热不变性
  invariant_torus.gif       不变环面上的周期轨道与准周期轨道
  hj_wavefront_gravity.gif  均匀重力场中等作用量面（波前）与轨道（法线）

Frame 0 of every GIF is an overview frame (it is what the PDF shows).
Helpers and colours are shared with make_hamiltonian_teaching_media.py.
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from scipy.special import ellipk

from make_hamiltonian_teaching_media import (BLUE, RED, GREEN, ORANGE, GRAY, LIGHT,
                                             clean, frame, save_gif)

PURPLE = "#6f4c9b"


# ----------------------------------------------------------------------------
# 1. pendulum: libration, near-separatrix, rotation
# ----------------------------------------------------------------------------
def rk4(f, y, dt, n):
    out = np.empty((n + 1, len(y)))
    out[0] = y
    for k in range(n):
        k1 = f(y); k2 = f(y + 0.5 * dt * k1); k3 = f(y + 0.5 * dt * k2); k4 = f(y + dt * k3)
        y = y + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        out[k + 1] = y
    return out


def pendulum_period(E):
    E = np.asarray(E, dtype=float)
    T = np.full_like(E, np.nan)
    lib = (E > -1) & (E < 1)
    m = (1 + E[lib]) / 2
    T[lib] = 4 * ellipk(m)
    rot = E > 1
    m = (1 + E[rot]) / 2
    T[rot] = 2 / np.sqrt(m) * ellipk(1 / m)
    return T


def wrap(q):
    return (q + np.pi) % (2 * np.pi) - np.pi


def pendulum_separatrix():
    f = lambda y: np.array([y[1], -np.sin(y[0])])
    cases = [(-0.5, "天平动 $E=-0.5$", BLUE), (0.97, "接近分离曲线 $E=0.97$", RED), (1.6, "整圈转动 $E=1.6$", GREEN)]
    dt, tmax = 0.01, 16.0
    n = int(tmax / dt)
    orbits = []
    for E, lab, c in cases:
        p0 = np.sqrt(2 * (E + 1))           # start at q = 0 with p > 0
        orbits.append(rk4(f, np.array([0.0, p0]), dt, n))
    qg, pg = np.meshgrid(np.linspace(-np.pi, np.pi, 400), np.linspace(-2.6, 2.6, 300))
    Hg = 0.5 * pg**2 - np.cos(qg)
    Es = np.linspace(-0.995, 2.6, 900)
    Ts = pendulum_period(Es)
    idx = np.r_[n, np.linspace(0, n, 80).astype(int)]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.3), dpi=105, gridspec_kw={"width_ratios": [1.25, 1]})
    frames = []
    for j, k in enumerate(idx):
        ax1.clear(); ax2.clear()
        ax1.contour(qg, pg, Hg, levels=np.linspace(-0.9, 2.4, 12), colors="#c4ccd8", linewidths=0.7)
        ax1.contour(qg, pg, Hg, levels=[1.0], colors=[ORANGE], linewidths=1.8)
        for (E, lab, c), orb in zip(cases, orbits):
            q, p = wrap(orb[:, 0]), orb[:, 1]
            if j == 0:
                jumps = np.r_[0, np.nonzero(np.abs(np.diff(q)) > np.pi)[0] + 1, len(q)]
                for a, b in zip(jumps[:-1], jumps[1:]):
                    ax1.plot(q[a:b], p[a:b], color=c, lw=1.6)
                ax1.plot([q[0]], [p[0]], "o", color=c, ms=7)
            else:
                lo = max(0, k - 120)
                seg_q, seg_p = q[lo:k + 1], p[lo:k + 1]
                jumps = np.r_[0, np.nonzero(np.abs(np.diff(seg_q)) > np.pi)[0] + 1, len(seg_q)]
                for a, b in zip(jumps[:-1], jumps[1:]):
                    ax1.plot(seg_q[a:b], seg_p[a:b], color=c, lw=1.8, alpha=0.8)
                ax1.plot([q[k]], [p[k]], "o", color=c, ms=8)
        ax1.text(-3.05, -2.48, "橙色：分离曲线 $E=1$（两个双曲点 $q=\\pm\\pi$）", color=ORANGE, fontsize=9.5)
        ax1.set(xlim=(-np.pi, np.pi), ylim=(-2.6, 2.6), xlabel="$q$（摆角）", ylabel="$p$")
        ax1.set_xticks([-np.pi, 0, np.pi], ["$-\\pi$", "0", "$\\pi$"])
        ax1.set_title("单摆 $H=\\frac{1}{2}p^2-\\cos q$ 的相图" + ("" if j == 0 else f"（$t={k * dt:.1f}$）"))
        clean(ax1)

        ax2.plot(Es, Ts / (2 * np.pi), color=GRAY, lw=1.8)
        ax2.axvline(1.0, color=ORANGE, ls="--", lw=1.2)
        for E, lab, c in cases:
            ax2.plot([E], [pendulum_period(np.array([E]))[0] / (2 * np.pi)], "o", color=c, ms=8)
        for (E, lab, c), (dx, y) in zip(cases, ((-0.95, 1.38), (1.08, 2.45), (1.45, 0.92))):
            ax2.text(dx, y, lab, color=c, fontsize=9.5)
        ax2.text(1.04, 3.55, "$T\\to\\infty$", color=ORANGE)
        ax2.set(xlim=(-1, 2.6), ylim=(0.5, 3.8), xlabel="能量 $E$", ylabel="周期 $T/2\\pi$")
        ax2.set_title("周期在分离曲线处对数发散")
        clean(ax2)
        fig.suptitle("天平动与转动由分离曲线隔开；靠近分离曲线时，“相对一个周期很慢”的条件失效", fontsize=11.5)
        fig.subplots_adjust(left=0.07, right=0.98, bottom=0.13, top=0.84, wspace=0.25)
        frames.append(frame(fig))
    plt.close(fig)
    save_gif(frames, "pendulum_separatrix.gif", duration=80)


# ----------------------------------------------------------------------------
# 2. magnetic mirror (Boris pusher, paraxial field)
# ----------------------------------------------------------------------------
def mirror_field(x, B0=8.0, L=1.0):
    X, Y, Z = x
    Bz = B0 * (1 + (Z / L) ** 2)
    dBz = 2 * B0 * Z / L**2
    return np.array([-0.5 * X * dBz, -0.5 * Y * dBz, Bz])


def boris(x, v, dt, n):
    xs = np.empty((n + 1, 3)); vs = np.empty((n + 1, 3))
    xs[0], vs[0] = x, v
    for k in range(n):
        B = mirror_field(x)
        t = 0.5 * dt * B
        s = 2 * t / (1 + t @ t)
        vp = v + np.cross(v, t)
        v = v + np.cross(vp, s)
        x = x + dt * v
        xs[k + 1], vs[k + 1] = x, v
    return xs, vs


def magnetic_mirror():
    B0, L, zmax = 8.0, 1.0, 2.0
    dt, tmax = 0.004, 14.0
    n = int(tmax / dt)
    runs = []
    for alpha, c, lab in ((50, BLUE, "投掷角 $50^\\circ$：被反射"), (20, RED, "投掷角 $20^\\circ$：在损失锥内，逃逸")):
        a = np.radians(alpha)
        vperp, vpar = np.sin(a), np.cos(a)
        x0 = np.array([0.18 + vperp / B0, 0.0, 0.0])      # guiding centre at x = 0.18
        v0 = np.array([0.0, -vperp, vpar])
        xs, vs = boris(x0, v0, dt, n)
        B = np.array([np.linalg.norm(mirror_field(xx)) for xx in xs])
        bhat = np.array([mirror_field(xx) for xx in xs]) / B[:, None]
        vpar_t = np.sum(vs * bhat, axis=1)
        vperp2 = np.sum(vs**2, axis=1) - vpar_t**2
        mu = vperp2 / (2 * B)
        inside = np.abs(xs[:, 2]) <= zmax
        last = np.argmax(~inside) if (~inside).any() else n
        runs.append(dict(xs=xs, vpar=vpar_t, mu=mu, last=last, c=c, lab=lab, alpha=alpha))
    t = np.arange(n + 1) * dt
    zz = np.linspace(-zmax, zmax, 300)
    idx = np.r_[n, np.linspace(0, n, 90).astype(int)]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.8, 4.3), dpi=105, gridspec_kw={"width_ratios": [1.35, 1]})
    frames = []
    for j, k in enumerate(idx):
        ax1.clear(); ax2.clear()
        for r0 in (0.08, 0.18, 0.3, 0.42):
            r = r0 / np.sqrt(1 + zz**2)
            ax1.plot(zz, r, color="#c4ccd8", lw=0.8); ax1.plot(zz, -r, color="#c4ccd8", lw=0.8)
        ax1.fill_between([-zmax, -1.6], -0.5, 0.5, color=LIGHT, alpha=0.8)
        ax1.fill_between([1.6, zmax], -0.5, 0.5, color=LIGHT, alpha=0.8)
        ax1.text(-1.98, 0.45, "强场区", fontsize=9, color=GRAY); ax1.text(1.62, 0.45, "强场区", fontsize=9, color=GRAY)
        for r in runs:
            kk = min(k, r["last"])
            ax1.plot(r["xs"][:kk + 1, 2], r["xs"][:kk + 1, 0], color=r["c"], lw=0.7, alpha=0.85)
            if j > 0 and k <= r["last"]:
                ax1.plot([r["xs"][k, 2]], [r["xs"][k, 0]], "o", color=r["c"], ms=6)
        ax1.set(xlim=(-zmax, zmax), ylim=(-0.5, 0.52), xlabel="沿磁场方向 $z$", ylabel="$x$")
        ax1.set_title("侧视图：磁力线（灰）在两端收拢")
        clean(ax1)
        for r in runs:
            kk = min(k, r["last"])
            ax2.plot(t[:kk + 1], r["vpar"][:kk + 1], color=r["c"], lw=1.3, label=r["lab"])
            if r["last"] == n:
                ax2.plot(t[:kk + 1], r["mu"][:kk + 1] / r["mu"][0] - 1.5, color=r["c"], lw=1.0, ls="--")
        ax2.axhline(0, color=GRAY, lw=0.6)
        ax2.text(3.0, -0.36, "虚线：被俘获粒子的 $\\mu/\\mu_0$（下移 1.5）", color=GRAY, fontsize=9)
        ax2.text(3.0, 1.08, "实线：沿磁场的速度 $v_\\parallel$", color=GRAY, fontsize=9)
        ax2.set(xlim=(0, tmax), ylim=(-1.05, 1.22), xlabel="$t$")
        ax2.legend(frameon=False, loc="lower right", fontsize=8.5)
        ax2.set_title("$v_\\parallel$ 减到零即被反射")
        clean(ax2)
        fig.suptitle("磁镜：回旋运动的作用量 $\\propto\\mu=mv_\\perp^2/2B$ 是绝热不变量", fontsize=12)
        fig.subplots_adjust(left=0.07, right=0.98, bottom=0.13, top=0.84, wspace=0.22)
        frames.append(frame(fig))
    plt.close(fig)
    for r in runs:
        print("mirror", r["alpha"], "mu drift", float(np.ptp(r["mu"][:r["last"]]) / r["mu"][0]),
              "escaped" if r["last"] < n else "trapped")
    save_gif(frames, "magnetic_mirror.gif", duration=70)


# ----------------------------------------------------------------------------
# 3. invariant tori
# ----------------------------------------------------------------------------
def torus_xyz(t1, t2, R=2.0, r=0.8):
    return ((R + r * np.cos(t2)) * np.cos(t1), (R + r * np.cos(t2)) * np.sin(t1), r * np.sin(t2))


def invariant_torus():
    cases = [(2 / 3, "$\\omega_2/\\omega_1=2/3$（有理数）：轨道闭合", RED),
             ((np.sqrt(5) - 1) / 2, "$\\omega_2/\\omega_1=(\\sqrt{5}-1)/2$（无理数）：轨道铺满环面", BLUE)]
    tmax = 2 * np.pi * 30
    tt = np.linspace(0, tmax, 9000)
    u, w = np.meshgrid(np.linspace(0, 2 * np.pi, 60), np.linspace(0, 2 * np.pi, 30))
    idx = np.r_[len(tt) - 1, np.linspace(30, len(tt) - 1, 64).astype(int)]
    fig = plt.figure(figsize=(9.8, 4.6), dpi=100)
    axs = [fig.add_subplot(1, 2, i + 1, projection="3d") for i in range(2)]
    frames = []
    for j, k in enumerate(idx):
        for ax, (ratio, lab, c) in zip(axs, cases):
            ax.clear()
            X, Y, Z = torus_xyz(u, w)
            ax.plot_surface(X, Y, Z, color="#e4e9f1", alpha=0.25, linewidth=0, shade=False)
            x, y, z = torus_xyz(tt[:k + 1], ratio * tt[:k + 1])
            ax.plot(x, y, z, color=c, lw=0.9)
            ax.plot([x[-1]], [y[-1]], [z[-1]], "o", color=c, ms=5)
            ax.set(xlim=(-2.8, 2.8), ylim=(-2.8, 2.8), zlim=(-1.4, 1.4))
            ax.set_box_aspect((1, 1, 0.5)); ax.set_axis_off()
            ax.view_init(elev=32, azim=-60 + 0.8 * j)
            ax.set_title(lab, fontsize=10, color=c)
        fig.suptitle("二自由度可积系统：轨道位于由 $(I_1,I_2)$ 标记的不变环面上，两个角变量匀速增加", fontsize=11.5)
        fig.subplots_adjust(left=0.0, right=1.0, bottom=0.0, top=0.9, wspace=0.0)
        frames.append(frame(fig))
    plt.close(fig)
    save_gif(frames, "invariant_torus.gif", duration=70)


# ----------------------------------------------------------------------------
# 4. Hamilton-Jacobi wavefronts in uniform gravity
# ----------------------------------------------------------------------------
def hj_wavefront_gravity():
    v0 = 1.0
    thetas = np.radians(np.linspace(-80, 80, 17))
    tcap = 2.4

    def tmax(th):
        return min(1 / np.sin(th), tcap) if th > 0 else tcap

    def W(th, t):           # characteristic function along a ray, m = g = 1
        return v0**2 * t - v0 * np.sin(th) * t**2 + t**3 / 3

    def pos(th, t):
        return v0 * np.cos(th) * t, v0 * np.sin(th) * t - 0.5 * t**2

    Wlev = np.linspace(0.15, 1.5, 10)
    xs = np.linspace(-0.05, 2.6, 200)
    env = v0**2 / 2 - xs**2 / (2 * v0**2)

    def front(Wstar):
        pts = []
        for th in np.radians(np.linspace(-85, 85, 241)):
            tt = np.linspace(0, tmax(th), 800)
            ww = W(th, tt)
            if ww[-1] < Wstar:
                pts.append((np.nan, np.nan)); continue
            t_ = np.interp(Wstar, ww, tt)
            pts.append(pos(th, t_))
        return np.array(pts)

    fronts = [front(w) for w in Wlev]
    Wanim = np.r_[Wlev[-1], np.linspace(0.05, Wlev[-1], 70)]
    fig, ax = plt.subplots(figsize=(8.0, 5.0), dpi=125)
    frames = []
    for j, Wn in enumerate(Wanim):
        ax.clear()
        ax.plot(xs, env, color=GRAY, ls="--", lw=1.0)
        ax.text(1.72, -0.5, "包络（焦散线）\n$y=\\frac{1}{2}-\\frac{x^2}{2}$", color=GRAY, fontsize=9)
        for th in thetas:
            tt = np.linspace(0, tmax(th), 200)
            x, y = pos(th, tt)
            ax.plot(x, y, color=RED, lw=0.9, alpha=0.75)
        for w, fr in zip(Wlev, fronts):
            if w <= Wn + 1e-9:
                ax.plot(fr[:, 0], fr[:, 1], color=BLUE, lw=1.4 if j == 0 else 1.0, alpha=0.9 if j == 0 else 0.45)
        if j > 0:
            fr = front(Wn)
            ax.plot(fr[:, 0], fr[:, 1], color=BLUE, lw=2.4)
            ax.text(0.02, 0.62, f"$W={Wn:.2f}$", color=BLUE, fontsize=11)
        ax.plot([0], [0], "o", color=ORANGE, ms=8)
        ax.text(-0.42, 0.88, "红：同一点、同一速率抛出的轨道（射线）", color=RED, fontsize=10)
        ax.text(-0.42, 0.76, "蓝：等作用量面 $W(x,y)=$ 常数（波前），满足 $\\frac{1}{2}|\\nabla W|^2+y=E$", color=BLUE, fontsize=10)
        ax.set(xlim=(-0.45, 2.65), ylim=(-1.35, 0.98), xlabel="$x$", ylabel="$y$", aspect="equal")
        ax.set_title("均匀重力场中的哈密顿－雅可比波前：轨道处处垂直于波前（$\\boldsymbol{p}=\\nabla W$）", fontsize=11)
        clean(ax)
        fig.subplots_adjust(left=0.08, right=0.98, bottom=0.1, top=0.92)
        frames.append(frame(fig))
    plt.close(fig)
    save_gif(frames, "hj_wavefront_gravity.gif", duration=80)


if __name__ == "__main__":
    pendulum_separatrix()
    magnetic_mirror()
    invariant_torus()
    hj_wavefront_gravity()
