"""Figures for the KAM 定理 lecture note.

Run:  python3 make_figures.py   (needs numpy, scipy, matplotlib, Noto Sans CJK)
Outputs PNGs next to this script.
"""
import os, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from scipy.integrate import solve_ivp

for f in font_manager.findSystemFonts():
    if "NotoSansCJK-Regular" in f:
        font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": ["Noto Sans CJK SC", "Noto Sans CJK JP"],
                     "mathtext.fontset": "cm", "axes.unicode_minus": False,
                     "font.size": 11, "savefig.dpi": 220})
OUT = os.path.dirname(os.path.abspath(__file__)) + "/"
BLUE = "#1f4e9c"; RED = "#c8102e"; ORANGE = "#e08a00"; GREEN = "#2e7d32"; GRAY = "#777777"
rng = np.random.default_rng(1)

cmap = plt.get_cmap("viridis")

def fig1():
    # ---------------------------------------------------------------- Fig 1: tori
    def torus_xyz(t1, t2, R=2.0, r=0.8):
        return ((R + r*np.cos(t1))*np.cos(t2), (R + r*np.cos(t1))*np.sin(t2), r*np.sin(t1))

    fig = plt.figure(figsize=(9.2, 3.6))
    u, v = np.meshgrid(np.linspace(0, 2*np.pi, 60), np.linspace(0, 2*np.pi, 60))
    for k, (ratio, T, title, col) in enumerate([
            (2/3, 6*np.pi, r"共振环面：$\omega_1/\omega_2=2/3$（周期轨道）", RED),
            ((np.sqrt(5)-1)/2, 120*np.pi, r"非共振环面：$\omega_1/\omega_2=(\sqrt{5}-1)/2$（拟周期）", BLUE)]):
        ax = fig.add_subplot(1, 2, k+1, projection="3d")
        X, Y, Z = torus_xyz(u, v)
        ax.plot_surface(X, Y, Z, color="#dfe6f0", alpha=0.25, linewidth=0, shade=False)
        t = np.linspace(0, T, 6000)
        x, y, z = torus_xyz(ratio*t, t)
        ax.plot(x, y, z, color=col, lw=0.7 if k else 1.4)
        ax.set_xlim(-2.3, 2.3); ax.set_ylim(-2.3, 2.3); ax.set_zlim(-1.0, 1.0)
        ax.set_box_aspect((1, 1, 0.43), zoom=1.12); ax.set_axis_off()
        ax.view_init(elev=32, azim=-60)
        ax.set_title(title, fontsize=10.5, pad=-4)
    fig.subplots_adjust(left=0, right=1, top=0.95, bottom=0, wspace=0)
    fig.savefig(OUT + "kam_torus.png", bbox_inches="tight", facecolor="white"); plt.close(fig)



def fig2():
    # ---------------------------------------------------- Fig 2: Diophantine set
    def removed_intervals(gamma, tau, qmax=1500):
        iv = []
        for q in range(1, qmax+1):
            w = gamma / q**(tau+1)
            for p in range(0, q+1):
                if math.gcd(p, q) != 1:
                    continue
                iv.append((p/q - w, p/q + w))
        iv.sort()
        merged = []
        for a, b in iv:
            a, b = max(a, 0.0), min(b, 1.0)
            if a >= b:
                continue
            if merged and a <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        return merged

    tau = 2.0
    fig, ax = plt.subplots(figsize=(8.6, 3.0))
    gammas = [0.12, 0.05, 0.015]
    N = 8000
    xs = (np.arange(N) + 0.5)/N
    for i, g in enumerate(gammas):
        y0 = len(gammas) - 1 - i
        m = removed_intervals(g, tau)
        lost = sum(b - a for a, b in m)
        mm = np.array(m)
        lo = np.searchsorted(xs, mm[:, 0]); hi = np.searchsorted(xs, mm[:, 1])
        d = np.zeros(N + 1, int)
        np.add.at(d, lo, 1); np.add.at(d, hi, -1)
        keep = np.cumsum(d)[:N] == 0
        img = np.where(keep, 1.0, 0.0)[None, :]
        ax.imshow(img, extent=(0, 1, y0+0.2, y0+0.7), aspect="auto",
                  cmap=matplotlib.colors.ListedColormap(["white", BLUE]), vmin=0, vmax=1,
                  interpolation="nearest")
        ax.text(1.02, y0+0.45, rf"$\gamma={g}$" + "\n" + f"保留 {100*(1-lost):.0f}%",
                va="center", fontsize=9.5)
    for p, q in [(0, 1), (1, 3), (1, 2), (2, 3), (1, 1), (2, 5), (3, 5), (1, 4), (3, 4)]:
        ax.text(p/q, -0.08, f"{p}/{q}", ha="center", va="top", fontsize=8.5, color=GRAY)
    gold = (np.sqrt(5)-1)/2
    ax.annotate("黄金分割比 $(\\sqrt{5}-1)/2$", xy=(gold, 2.72), xytext=(gold+0.08, 3.05),
                fontsize=9, color=RED, arrowprops=dict(arrowstyle="->", color=RED, lw=0.9))
    ax.set_xlim(-0.01, 1.16); ax.set_ylim(-0.4, 3.3)
    ax.set_xlabel(r"频率比 $\alpha=\omega_1/\omega_2$")
    ax.set_yticks([]); [ax.spines[s].set_visible(False) for s in ("left", "right", "top")]
    ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.xaxis.set_label_coords(0.43, -0.2)
    ax.set_title(r"丢番图条件 $|\alpha-p/q|\geq\gamma/q^{\tau+1}$（$\tau=2$）：蓝色为保留的频率", fontsize=10.5, pad=12)
    fig.savefig(OUT + "diophantine_set.png", bbox_inches="tight", facecolor="white"); plt.close(fig)



def fig3():
    # ---------------------------------------------------- Fig 3: standard map
    def standard_map_orbits(K, n_ic=110, n_it=900):
        th0 = rng.uniform(0, 2*np.pi, n_ic)
        I0 = np.linspace(0, 2*np.pi, n_ic, endpoint=False) + rng.uniform(0, 0.05, n_ic)
        TH = np.empty((n_ic, n_it)); II = np.empty((n_ic, n_it))
        th, I = th0.copy(), I0.copy()
        for j in range(n_it):
            I = (I + K*np.sin(th)) % (2*np.pi)
            th = (th + I) % (2*np.pi)
            TH[:, j] = th; II[:, j] = I
        return TH, II

    Ks = [(0.5, r"$K=0.5$：大部分 KAM 曲线保留"),
          (0.971635, r"$K=K_c\approx0.9716$：最后一条曲线临界"),
          (1.5, r"$K=1.5$：全局混沌 + 稳定岛"),
          (4.0, r"$K=4$：几乎完全混沌")]
    fig, axs = plt.subplots(2, 2, figsize=(8.4, 8.0))
    cmap = plt.get_cmap("viridis")
    for ax, (K, title) in zip(axs.flat, Ks):
        TH, II = standard_map_orbits(K)
        for i in range(TH.shape[0]):
            ax.plot(TH[i], II[i], ",", color=cmap(i/TH.shape[0]), alpha=0.9, rasterized=True)
        if abs(K - 0.971635) < 1e-3:
            # golden-mean orbit: rotation number (3-sqrt5)/2 * 2pi near I ~ 2.4
            pass
        ax.set_xlim(0, 2*np.pi); ax.set_ylim(0, 2*np.pi)
        ax.set_xticks([0, np.pi, 2*np.pi]); ax.set_xticklabels(["0", r"$\pi$", r"$2\pi$"])
        ax.set_yticks([0, np.pi, 2*np.pi]); ax.set_yticklabels(["0", r"$\pi$", r"$2\pi$"])
        ax.set_xlabel(r"$\theta$"); ax.set_ylabel(r"$I$")
        ax.set_title(title, fontsize=10.5)
    fig.tight_layout()
    fig.savefig(OUT + "standard_map.png", bbox_inches="tight", facecolor="white"); plt.close(fig)



def fig4():
    # ---------------------------------------------------- Fig 4: Henon-Heiles
    def hh_section(E, n_orb=40, tmax=2500.0, dt=0.01):
        """Vectorised RK4 for all orbits at once; record x=0 crossings with px>0."""
        ics = []
        while len(ics) < n_orb:
            y = rng.uniform(-0.45, 0.75); py = rng.uniform(-0.5, 0.5)
            V = 0.5*y*y - y**3/3
            K2 = 2*(E - V) - py*py
            if K2 > 0:
                ics.append([0.0, y, np.sqrt(K2), py])
        S = np.array(ics).T  # shape (4, n)
        def f(S):
            x, y, px, py = S
            return np.array([px, py, -x - 2*x*y, -y - x*x + y*y])
        pts = [([], []) for _ in range(n_orb)]
        alive = np.ones(n_orb, bool)
        for _ in range(int(tmax/dt)):
            k1 = f(S); k2 = f(S + 0.5*dt*k1); k3 = f(S + 0.5*dt*k2); k4 = f(S + dt*k3)
            Sn = S + dt/6*(k1 + 2*k2 + 2*k3 + k4)
            cross = (S[0] < 0) & (Sn[0] >= 0) & alive
            if cross.any():
                idx = np.nonzero(cross)[0]
                w = -S[0, idx]/(Sn[0, idx] - S[0, idx])
                yc = S[1, idx] + w*(Sn[1, idx] - S[1, idx])
                pc = S[3, idx] + w*(Sn[3, idx] - S[3, idx])
                for i, a, b in zip(idx, yc, pc):
                    pts[i][0].append(a); pts[i][1].append(b)
            S = Sn
            alive &= (np.abs(S[0]) < 2) & (np.abs(S[1]) < 2)
        return [(np.array(a), np.array(b)) for a, b in pts if len(a) > 20]

    fig, axs = plt.subplots(1, 2, figsize=(9.0, 4.4))
    for ax, E in zip(axs, [1/12, 1/8]):
        pts = hh_section(E)
        for i, (y, py) in enumerate(pts):
            ax.plot(y, py, ".", ms=0.9, color=cmap(i/len(pts)), rasterized=True)
        yy = np.linspace(-0.7, 1.05, 800)
        V = 0.5*yy**2 - yy**3/3
        pmax = np.sqrt(np.clip(2*(E - V), 0, None))
        ok = 2*(E - V) >= 0
        ax.plot(yy[ok], pmax[ok], color="k", lw=0.8); ax.plot(yy[ok], -pmax[ok], color="k", lw=0.8)
        ax.set_xlabel(r"$y$"); ax.set_ylabel(r"$p_y$")
        ax.set_title(rf"$E={'1/12' if E < 0.1 else '1/8'}$", fontsize=11)
        ax.set_aspect("equal")
    fig.suptitle(r"Hénon–Heiles 系统的庞加莱截面（$x=0,\ p_x>0$）", fontsize=11.5)
    fig.tight_layout()
    fig.savefig(OUT + "henon_heiles.png", bbox_inches="tight", facecolor="white"); plt.close(fig)



def fig5():
    # ------------------------------------------- Fig 5: resonance -> pendulum
    fig, axs = plt.subplots(1, 2, figsize=(9.0, 3.6))
    ax = axs[0]
    P, J = np.meshgrid(np.linspace(-np.pi, 3*np.pi, 800), np.linspace(-3, 3, 600))
    Hp = 0.5*J**2 - np.cos(P)
    ax.contour(P, J, Hp, levels=np.linspace(-0.9, 0.9, 7), colors=GREEN, linewidths=0.9, negative_linestyles="solid")
    ax.contour(P, J, Hp, levels=np.linspace(1.3, 3.5, 7), colors=BLUE, linewidths=0.9)
    ax.contour(P, J, Hp, levels=[1.0], colors=RED, linewidths=1.6)
    ax.annotate("", xy=(0, 2.0), xytext=(0, -2.0), arrowprops=dict(arrowstyle="<->", color="k", lw=1))
    ax.text(0.15, 0.15, r"宽度 $\propto\sqrt{\varepsilon}$", fontsize=9.5)
    ax.set_xlim(-np.pi, 3*np.pi); ax.set_ylim(-3.0, 3.0)
    ax.set_xticks([-np.pi, 0, np.pi, 2*np.pi, 3*np.pi])
    ax.set_xticklabels([r"$-\pi$", "0", r"$\pi$", r"$2\pi$", r"$3\pi$"])
    ax.set_xlabel(r"共振角 $\phi=\boldsymbol{k}\cdot\boldsymbol{\theta}$")
    ax.set_ylabel(r"$J-J_{\rm res}$（任意单位）")
    ax.set_title("共振附近：摆模型的相图", fontsize=10.5)
    ax.text(np.pi, -2.72, "环流（KAM 型）", color=BLUE, ha="center", fontsize=9,
            bbox=dict(fc="white", ec="none", pad=1))
    ax.text(2*np.pi, 0.0, "天平动\n（岛）", color=GREEN, ha="center", va="center", fontsize=9,
            bbox=dict(fc="white", ec="none", pad=1))
    ax.annotate("分界线", xy=(4.0, 0.832), xytext=(3.75, -1.15), color=RED, fontsize=9,
                arrowprops=dict(arrowstyle="->", color=RED, lw=0.8),
                bbox=dict(fc="white", ec="none", pad=1))

    ax = axs[1]
    # Poincare-Birkhoff chain: standard map near the 1:2 resonance (I = pi)
    K = 0.5
    I0s = np.linspace(np.pi - 0.95, np.pi + 0.95, 34)
    for I0 in I0s:
        for th0 in [0.0, np.pi/2]:
            th, I = th0, I0
            xs, ys = np.empty(1500), np.empty(1500)
            for j in range(1500):
                I = I + K*np.sin(th)
                th = (th + I) % (2*np.pi)
                xs[j] = th; ys[j] = I
            ax.plot(xs, ys, ",", color=cmap((I0 - I0s[0])/(I0s[-1] - I0s[0])), rasterized=True)
    ax.set_xlim(0, 2*np.pi); ax.set_ylim(np.pi - 1.0, np.pi + 1.0)
    ax.set_xticks([0, np.pi, 2*np.pi]); ax.set_xticklabels(["0", r"$\pi$", r"$2\pi$"])
    ax.set_yticks([np.pi - 1, np.pi, np.pi + 1]); ax.set_yticklabels([r"$\pi-1$", r"$\pi$", r"$\pi+1$"])
    ax.set_xlabel(r"$\theta$"); ax.set_ylabel(r"$I$")
    ax.set_title(r"共振环面碎裂成岛链（标准映射 $K=0.5$，$1{:}2$ 共振）", fontsize=10.5)
    fig.tight_layout()
    fig.savefig(OUT + "resonance_islands.png", bbox_inches="tight", facecolor="white"); plt.close(fig)


import sys, time
sel = sys.argv[1:] or ["1", "2", "3", "4", "5"]
for k in sel:
    t0 = time.time(); globals()["fig" + k](); print("fig", k, f"{time.time()-t0:.1f}s", flush=True)
