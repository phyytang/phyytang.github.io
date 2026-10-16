"""Figures for the 动力学系统与混沌 lecture note.

Run:  python3 make_figures.py [1 2 3 ...]   (needs numpy, scipy, matplotlib, Noto Sans CJK)
Outputs PNGs next to this script.
"""
import os, sys, time
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
cmap = plt.get_cmap("viridis")
rng = np.random.default_rng(2)


# ------------------------------------------------ Fig 1: phase portraits
def fig1():
    fig, axs = plt.subplots(2, 2, figsize=(8.6, 8.0))
    # (a) saddle
    ax = axs[0, 0]
    X, Y = np.meshgrid(np.linspace(-2, 2, 30), np.linspace(-2, 2, 30))
    ax.streamplot(X, Y, X, -Y, color=GRAY, density=1.0, linewidth=0.7, arrowsize=0.8)
    ax.plot([-2, 2], [0, 0], color=RED, lw=1.8); ax.plot([0, 0], [-2, 2], color=BLUE, lw=1.8)
    ax.plot(0, 0, "ko", ms=5)
    ax.text(1.25, 0.12, "不稳定流形", color=RED, fontsize=9)
    ax.text(0.08, 1.6, "稳定流形", color=BLUE, fontsize=9)
    ax.set_title(r"(a) 鞍点：$\lambda_1>0>\lambda_2$", fontsize=10.5)
    # (b) stable focus: damped oscillator
    ax = axs[0, 1]
    ax.streamplot(X, Y, Y, -X - 0.4*Y, color=GRAY, density=1.0, linewidth=0.7, arrowsize=0.8)
    sol = solve_ivp(lambda t, s: [s[1], -s[0] - 0.4*s[1]], (0, 30), [1.8, 0], max_step=0.02)
    ax.plot(sol.y[0], sol.y[1], color=RED, lw=1.4); ax.plot(0, 0, "ko", ms=5)
    ax.set_title(r"(b) 稳定焦点：阻尼振子，$\mathrm{Re}\,\lambda<0$", fontsize=10.5)
    # (c) pendulum: centers and saddles
    ax = axs[1, 0]
    P, Q = np.meshgrid(np.linspace(-3*np.pi/2, 3*np.pi/2, 600), np.linspace(-3, 3, 400))
    E = 0.5*Q**2 - np.cos(P)
    ax.contour(P, Q, E, levels=np.linspace(-0.9, 0.9, 6), colors=GREEN, linewidths=0.9,
               negative_linestyles="solid")
    ax.contour(P, Q, E, levels=np.linspace(1.4, 3.4, 5), colors=BLUE, linewidths=0.9)
    ax.contour(P, Q, E, levels=[1.0], colors=RED, linewidths=1.6)
    ax.plot([0], [0], "ko", ms=5); ax.plot([-np.pi, np.pi], [0, 0], "kx", ms=7, mew=1.5)
    ax.set_xticks([-np.pi, 0, np.pi]); ax.set_xticklabels([r"$-\pi$", "0", r"$\pi$"])
    ax.set_title("(c) 单摆：中心（●）与鞍点（×）", fontsize=10.5)
    ax.set_xlabel(r"$q$"); ax.set_ylabel(r"$p$")
    # (d) van der Pol limit cycle
    ax = axs[1, 1]
    mu = 1.0
    f = lambda t, s: [s[1], mu*(1 - s[0]**2)*s[1] - s[0]]
    X2, Y2 = np.meshgrid(np.linspace(-3.5, 3.5, 30), np.linspace(-3.5, 3.5, 30))
    ax.streamplot(X2, Y2, Y2, mu*(1 - X2**2)*Y2 - X2, color="#bbbbbb", density=0.9,
                  linewidth=0.6, arrowsize=0.7)
    for s0, c in [([0.1, 0.0], ORANGE), ([3.0, 3.0], BLUE)]:
        sol = solve_ivp(f, (0, 25), s0, max_step=0.01)
        ax.plot(sol.y[0], sol.y[1], color=c, lw=1.2)
    sol = solve_ivp(f, (0, 60), [2, 0], max_step=0.01)
    m = sol.t > 40
    ax.plot(sol.y[0][m], sol.y[1][m], color=RED, lw=2.0)
    ax.set_xlim(-3.5, 3.5); ax.set_ylim(-3.5, 3.5)
    ax.set_title(r"(d) 范德波尔振子的极限环（$\mu=1$）", fontsize=10.5)
    for ax in axs.flat[:2]:
        ax.set_xlim(-2, 2); ax.set_ylim(-2, 2)
    for ax in [axs[0, 0], axs[0, 1], axs[1, 1]]:
        ax.set_xlabel(r"$x$"); ax.set_ylabel(r"$\dot x$" if ax is not axs[0, 0] else r"$y$")
    for ax in axs.flat:
        ax.set_aspect("equal" if ax is not axs[1, 0] else "auto")
    fig.tight_layout()
    fig.savefig(OUT + "phase_portraits.png", bbox_inches="tight", facecolor="white"); plt.close(fig)


# ------------------------------------------------ Fig 2: cobwebs
def fig2():
    fig, axs = plt.subplots(1, 3, figsize=(10.0, 3.6))
    for ax, r, title in zip(axs, [2.8, 3.3, 3.9],
                            ["稳定不动点", "稳定 2-周期", "混沌"]):
        x = np.linspace(0, 1, 400)
        ax.plot(x, r*x*(1 - x), color=BLUE, lw=1.4)
        ax.plot([0, 1], [0, 1], color=GRAY, lw=0.8)
        xn = 0.1; xs = [xn]
        for _ in range(120 if r > 3.5 else 60):
            xn = r*xn*(1 - xn); xs.append(xn)
        X = []; Y = []
        for a, b in zip(xs[:-1], xs[1:]):
            X += [a, a]; Y += [a, b]
            X += [a, b]; Y += [b, b]
        ax.plot(X[1:], Y[1:], color=RED, lw=0.6, alpha=0.8)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("equal")
        ax.set_xlabel(r"$x_n$"); ax.set_ylabel(r"$x_{n+1}$")
        ax.set_title(rf"$r={r}$：{title}", fontsize=10.5)
    fig.tight_layout()
    fig.savefig(OUT + "logistic_cobweb.png", bbox_inches="tight", facecolor="white"); plt.close(fig)


# ------------------------------------------------ Fig 3: bifurcation + Lyapunov
def fig3():
    rs = np.linspace(2.5, 4.0, 3000)
    x = 0.5*np.ones_like(rs)
    for _ in range(1000):
        x = rs*x*(1 - x)
    R = []; Xs = []
    lyap = np.zeros_like(rs)
    n_keep = 400
    for _ in range(n_keep):
        x = rs*x*(1 - x)
        lyap += np.log(np.abs(rs*(1 - 2*x)) + 1e-300)
        R.append(rs.copy()); Xs.append(x.copy())
    lyap /= n_keep
    rs2 = np.linspace(2.5, 4.0, 6000); x2 = 0.5*np.ones_like(rs2); ly2 = np.zeros_like(rs2)
    for _ in range(1000):
        x2 = rs2*x2*(1 - x2)
    for _ in range(4000):
        x2 = rs2*x2*(1 - x2); ly2 += np.log(np.abs(rs2*(1 - 2*x2)) + 1e-300)
    ly2 /= 4000
    fig, axs = plt.subplots(2, 1, figsize=(8.6, 6.6), sharex=True,
                            gridspec_kw={"height_ratios": [2.2, 1]})
    ax = axs[0]
    ax.plot(np.concatenate(R), np.concatenate(Xs), ",", color=BLUE, alpha=0.35, rasterized=True)
    ax.set_ylabel(r"长期行为 $x_n$")
    ax.set_title(r"逻辑斯谛映射 $x_{n+1}=rx_n(1-x_n)$ 的分岔图与李雅普诺夫指数", fontsize=11)
    for rv, lab in [(3.0, r"$r_1=3$"), (1 + np.sqrt(6), r"$r_2\approx3.449$"),
                    (3.5699456, r"$r_\infty\approx3.570$"), (1 + np.sqrt(8), "3-周期窗口")]:
        ax.axvline(rv, color=GRAY, lw=0.6, ls="--")
        ax.text(rv + 0.01, 0.03, lab, fontsize=8.5, color="k")
    ax.set_ylim(0, 1)
    ax = axs[1]
    ax.plot(rs2, ly2, color=RED, lw=0.6)
    ax.axhline(0, color="k", lw=0.7)
    ax.axhline(np.log(2), color=GRAY, lw=0.6, ls=":")
    ax.text(2.52, np.log(2) + 0.05, r"$\ln 2$", fontsize=9, color=GRAY)
    ax.set_ylim(-1.5, 0.9)
    ax.set_xlabel(r"$r$"); ax.set_ylabel(r"$\lambda$")
    ax.set_xlim(2.5, 4.0)
    fig.tight_layout()
    fig.savefig(OUT + "logistic_bifurcation.png", bbox_inches="tight", facecolor="white"); plt.close(fig)


# ------------------------------------------------ Fig 4: Lorenz
def lorenz(t, s, sig=10.0, rho=28.0, beta=8/3):
    x, y, z = s
    return [sig*(y - x), x*(rho - z) - y, x*y - beta*z]

def fig4():
    T = 40.0
    tt = np.linspace(0, T, 20001)
    s0 = np.array([1.0, 1.0, 20.0])
    a = solve_ivp(lorenz, (0, T), s0, t_eval=tt, rtol=1e-12, atol=1e-12, method="DOP853")
    b = solve_ivp(lorenz, (0, T), s0 + [1e-8, 0, 0], t_eval=tt, rtol=1e-12, atol=1e-12, method="DOP853")
    long = solve_ivp(lorenz, (0, 120), s0, max_step=0.005, rtol=1e-10, atol=1e-10, method="DOP853")
    fig = plt.figure(figsize=(10.0, 4.6))
    ax = fig.add_axes([0.04, 0.1, 0.40, 0.82])
    m = long.t > 2
    ax.plot(long.y[0][m], long.y[2][m], color=BLUE, lw=0.25, alpha=0.8)
    ax.plot(np.sqrt(8/3*27)*np.array([1, -1]), [27, 27], "o", color=RED, ms=4)
    ax.set_xlabel(r"$x$"); ax.set_ylabel(r"$z$")
    ax.set_title(r"洛伦兹吸引子（$\sigma=10,\ \rho=28,\ \beta=8/3$）", fontsize=10.5)
    ax2 = fig.add_axes([0.53, 0.58, 0.45, 0.34])
    ax2.plot(tt, a.y[0], color=BLUE, lw=0.8, label=r"$x_0=1$")
    ax2.plot(tt, b.y[0], color=ORANGE, lw=0.8, ls="--", label=r"$x_0=1+10^{-8}$")
    ax2.set_ylabel(r"$x(t)$"); ax2.set_xlim(0, T); ax2.set_xticklabels([])
    ax2.legend(fontsize=8, loc="lower left", ncol=2, frameon=False)
    ax2.set_title("两条初值相差 $10^{-8}$ 的轨道", fontsize=10.5)
    ax3 = fig.add_axes([0.53, 0.1, 0.45, 0.40])
    d = np.sqrt(((a.y - b.y)**2).sum(axis=0))
    ax3.semilogy(tt, d, color=RED, lw=0.8)
    lam = 0.906
    t_fit = np.linspace(0, 26, 50)
    ax3.semilogy(t_fit, 1e-8*np.exp(lam*t_fit), color="k", lw=1.0, ls="--")
    ax3.text(0.8, 3e0, r"$\propto e^{\lambda_1 t},\ \lambda_1\approx0.906$", fontsize=9.5)
    ax3.set_xlim(0, T); ax3.set_ylim(1e-9, 1e3)
    ax3.set_xlabel(r"$t$"); ax3.set_ylabel(r"$|\delta\boldsymbol{x}(t)|$")
    fig.savefig(OUT + "lorenz.png", bbox_inches="tight", facecolor="white"); plt.close(fig)


# ------------------------------------------------ Fig 5: Hyperion spin-orbit section
def kepler_E(M, e):
    E = M.copy() if np.ndim(M) else M
    for _ in range(30):
        E = E - (E - e*np.sin(E) - M)/(1 - e*np.cos(E))
    return E

def fig5():
    e = 0.1; w0sq = 0.79           # Hyperion (Wisdom, Peale & Mignard 1984); n = 1, a = 1
    nper = 400; nstep = 256
    dt = 2*np.pi/nstep
    # orbit quantities on half-step grid (RK4 needs t, t+dt/2, t+dt), same for all ICs
    tg = np.arange(0, 2*nstep + 1)*dt/2
    E = kepler_E(tg.copy(), e)
    r = 1 - e*np.cos(E)
    f = 2*np.arctan2(np.sqrt(1 + e)*np.sin(E/2), np.sqrt(1 - e)*np.cos(E/2))
    A = 0.5*w0sq/r**3
    th0 = []; om0 = []
    for om in np.linspace(0.2, 2.8, 34):
        for th in [0.0, np.pi/2]:
            th0.append(th); om0.append(om)
    th = np.array(th0) + rng.uniform(0, 0.02, len(th0)); om = np.array(om0)
    TH = np.empty((nper, len(th))); OM = np.empty_like(TH)
    def acc(theta, k):
        return -A[k]*np.sin(2*(theta - f[k]))
    for p in range(nper):
        for j in range(nstep):
            k0 = 2*j; k1 = 2*j + 1; k2 = 2*j + 2
            a1 = acc(th, k0);                 v1 = om
            a2 = acc(th + 0.5*dt*v1, k1);     v2 = om + 0.5*dt*a1
            a3 = acc(th + 0.5*dt*v2, k1);     v3 = om + 0.5*dt*a2
            a4 = acc(th + dt*v3, k2);         v4 = om + dt*a3
            th = th + dt/6*(v1 + 2*v2 + 2*v3 + v4)
            om = om + dt/6*(a1 + 2*a2 + 2*a3 + a4)
        TH[p] = np.mod(th, np.pi); OM[p] = om
    fig, ax = plt.subplots(figsize=(7.4, 5.0))
    for i in range(TH.shape[1]):
        ok = (OM[:, i] > 0) & (OM[:, i] < 3.2)
        ax.plot(TH[ok, i], OM[ok, i], ".", ms=0.8, color=cmap(i/TH.shape[1]), rasterized=True)
    ax.annotate("同步共振岛", xy=(0.12, 0.55), xytext=(0.55, 0.62), fontsize=9.5, color="k",
                arrowprops=dict(arrowstyle="->", lw=0.8), bbox=dict(fc="white", ec="none", pad=1))
    ax.text(np.pi/2, 1.45, "混沌海", fontsize=12, ha="center", color="k",
            bbox=dict(fc="white", ec="none", alpha=0.8, pad=2))
    ax.text(np.pi/2, 2.82, "快速规则自转（KAM 曲线）", fontsize=9.5, ha="center",
            bbox=dict(fc="white", ec="none", alpha=0.8, pad=1))
    ax.text(np.pi/2, 0.1, "慢速规则自转", fontsize=9.5, ha="center",
            bbox=dict(fc="white", ec="none", alpha=0.8, pad=1))
    ax.set_xlim(0, np.pi); ax.set_ylim(0, 3.0)
    ax.set_xticks([0, np.pi/2, np.pi]); ax.set_xticklabels(["0", r"$\pi/2$", r"$\pi$"])
    ax.set_xlabel(r"近土点时刻的取向角 $\theta$（mod $\pi$）")
    ax.set_ylabel(r"自转角速度 $\dot\theta/n$")
    ax.set_title(r"土卫七 Hyperion 的自转－轨道耦合：庞加莱截面（$e=0.1$，$\omega_0^2=0.79$）", fontsize=10.5)
    fig.savefig(OUT + "hyperion_section.png", bbox_inches="tight", facecolor="white"); plt.close(fig)


# ------------------------------------------------ Fig 6: Pythagorean three-body problem
M3 = np.array([3.0, 4.0, 5.0])

def nbody(t, s):
    x = s[:6].reshape(3, 2); v = s[6:].reshape(3, 2)
    a = np.zeros_like(x)
    for i in range(3):
        for j in range(3):
            if i != j:
                d = x[j] - x[i]
                a[i] += M3[j]*d/np.linalg.norm(d)**3
    return np.concatenate([v.ravel(), a.ravel()])

def energy(s):
    x = s[:6].reshape(3, 2); v = s[6:].reshape(3, 2)
    K = 0.5*(M3[:, None]*v**2).sum()
    U = 0.0
    for i in range(3):
        for j in range(i + 1, 3):
            U -= M3[i]*M3[j]/np.linalg.norm(x[i] - x[j])
    return K + U

def fig6():
    x0 = np.array([1.0, 3.0, -2.0, -1.0, 1.0, -1.0])
    s0 = np.concatenate([x0, np.zeros(6)])
    T = 70.0
    tt = np.linspace(0, T, 14001)
    kw = dict(t_eval=tt, rtol=1e-13, atol=1e-13, method="DOP853")
    a = solve_ivp(nbody, (0, T), s0, **kw)
    s1 = s0.copy(); s1[0] += 1e-9
    b = solve_ivp(nbody, (0, T), s1, **kw)
    E0 = energy(s0); E1 = energy(a.y[:, -1])
    print("energy drift", abs(E1 - E0)/abs(E0))
    fig = plt.figure(figsize=(10.0, 4.6))
    ax = fig.add_axes([0.04, 0.1, 0.42, 0.82])
    cols = [ORANGE, GREEN, BLUE]
    for i in range(3):
        ax.plot(a.y[2*i], a.y[2*i + 1], color=cols[i], lw=0.6, label=rf"$m={int(M3[i])}$")
        ax.plot(x0[2*i], x0[2*i + 1], "o", color=cols[i], ms=6)
    ax.set_xlim(-6, 6); ax.set_ylim(-6, 6); ax.set_aspect("equal")
    ax.legend(fontsize=9, loc="upper left", frameon=False)
    ax.set_xlabel(r"$x$"); ax.set_ylabel(r"$y$")
    ax.set_title(r"毕达哥拉斯三体问题（$0\leq t\leq70$）", fontsize=10.5)
    ax2 = fig.add_axes([0.56, 0.1, 0.42, 0.82])
    d = np.sqrt(((a.y[:6] - b.y[:6])**2).sum(axis=0))
    ax2.semilogy(tt, d, color=RED, lw=0.8)
    ax2.set_xlabel(r"$t$"); ax2.set_ylabel(r"位置差 $|\delta\boldsymbol{x}(t)|$")
    ax2.set_title(r"初始位置相差 $10^{-9}$ 的两次积分", fontsize=10.5)
    ax2.set_xlim(0, T)
    fig.savefig(OUT + "pythagorean.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
    # report final state
    xf = a.y[:6, -1].reshape(3, 2)
    print("final positions", xf, "dist 12,13,23",
          np.linalg.norm(xf[0]-xf[1]), np.linalg.norm(xf[0]-xf[2]), np.linalg.norm(xf[1]-xf[2]))


sel = sys.argv[1:] or ["1", "2", "3", "4", "5", "6"]
for k in sel:
    t0 = time.time(); globals()["fig" + k](); print("fig", k, f"{time.time()-t0:.1f}s", flush=True)
