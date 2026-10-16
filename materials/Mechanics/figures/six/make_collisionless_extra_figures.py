"""Additional teaching media for 无碰撞粒子体系.md (second round).

Outputs (in this folder):
  relaxation_random_walk.gif  大量微弱遭遇使速度随机游走，<Δv^2> 随穿越次数线性增长
  third_integral.gif          扁平轴对称势中子午面轨道与庞加莱截面：第三积分
  isothermal_sphere.png       非奇异等温球的数值解：核心、r^-2 外区与平坦旋转曲线

Frame 0 of every GIF is an overview frame (it is what the PDF shows).
Helpers and colours are shared with make_collisionless_teaching_media.py.
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

from make_collisionless_teaching_media import (BLUE, RED, GREEN, ORANGE, PURPLE, GRAY, LIGHT,
                                               OUT, clean, frame, save_gif)


# ----------------------------------------------------------------------------
# 1. two-body relaxation as a random walk in velocity space
# ----------------------------------------------------------------------------
def relaxation_random_walk():
    rng = np.random.default_rng(3)
    N = 1000                      # stars in the system; units R = v = G N m = 1
    bmin = 1.0 / N                # so that ln(Lambda) = ln N
    ncross, sub = 25, 4           # crossings, frames per crossing
    nstar = 400
    per = N // sub                # encounters per sub-step
    dv = np.zeros((nstar, 2))
    hist = [dv.copy()]
    for _ in range(ncross * sub):
        u = rng.random((nstar, per))
        b = np.sqrt(bmin**2 + u * (1 - bmin**2))         # p(b) ∝ b on [bmin, 1]
        kick = 2.0 / (N * b)                             # δv = 2Gm/(b v)
        ang = 2 * np.pi * rng.random((nstar, per))
        dv = dv + np.stack([np.sum(kick * np.cos(ang), 1), np.sum(kick * np.sin(ang), 1)], 1)
        hist.append(dv.copy())
    hist = np.array(hist)                                # (steps+1, nstar, 2)
    ncr = np.arange(hist.shape[0]) / sub
    msq = np.mean(np.sum(hist**2, 2), 1)
    mean_vec = np.linalg.norm(np.mean(hist, 1), axis=1)
    slope = 8 * np.log(N) / N
    t_relax = 1 / slope
    print("relaxation: measured slope", np.polyfit(ncr, msq, 1)[0], "theory", slope, "t_relax crossings", t_relax)
    show = [0, 1, 2, 3, 4, 5]
    cols = [BLUE, RED, GREEN, ORANGE, PURPLE, GRAY]
    idx = np.r_[len(ncr) - 1, np.arange(len(ncr))]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.4), dpi=110, gridspec_kw={"width_ratios": [1, 1.15]})
    frames = []
    ph = np.linspace(0, 2 * np.pi, 300)
    for j, k in enumerate(idx):
        ax1.clear(); ax2.clear()
        ax1.plot(np.cos(ph), np.sin(ph), color=GRAY, ls="--", lw=1)
        ax1.text(0.0, 1.06, "$|\\Delta\\vec v|=v$", color=GRAY, ha="center", fontsize=9.5)
        for s_, c in zip(show, cols):
            ax1.plot(hist[:k + 1, s_, 0], hist[:k + 1, s_, 1], color=c, lw=1.0, alpha=0.85)
            ax1.plot([hist[k, s_, 0]], [hist[k, s_, 1]], "o", color=c, ms=5)
        ax1.plot([0], [0], "k+", ms=9)
        ax1.set(xlim=(-1.55, 1.55), ylim=(-1.55, 1.55), aspect="equal",
                xlabel="$\\Delta v_x/v$", ylabel="$\\Delta v_y/v$")
        ax1.set_title(f"六颗恒星横向速度的累积改变（穿越 {ncr[k]:.0f} 次）", fontsize=10.5)
        clean(ax1)

        ax2.plot(ncr[:k + 1], msq[:k + 1], color=BLUE, lw=2, label="$\\langle|\\Delta\\vec v|^2\\rangle/v^2$（400 颗星平均）")
        ax2.plot(ncr[:k + 1], mean_vec[:k + 1], color=RED, lw=1.6, label="$|\\langle\\Delta\\vec v\\rangle|/v$：平均改变几乎为零")
        ax2.plot(ncr, slope * ncr, color=GRAY, ls="--", lw=1.1, label="理论 $8n\\ln\\Lambda/N$")
        ax2.axhline(1, color=GRAY, lw=0.6); ax2.axvline(t_relax, color=ORANGE, lw=1, ls=":")
        ax2.text(t_relax + 0.3, 0.35, f"$n_{{\\rm relax}}=N/(8\\ln N)\\approx{t_relax:.0f}$", color=ORANGE, fontsize=9.5)
        ax2.set(xlim=(0, ncross), ylim=(0, 1.55), xlabel="穿越体系的次数 $n$")
        ax2.legend(frameon=False, loc="upper left", fontsize=9)
        ax2.set_title("随机方向的小偏转：累加的是 $\\delta v^2$，不是 $\\delta v$", fontsize=10.5)
        clean(ax2)
        fig.suptitle(f"二体弛豫：$N={N}$，每次穿越约 $N$ 次远距离遭遇（$b_{{\\min}}=R/N$）", fontsize=12)
        fig.subplots_adjust(left=0.07, right=0.98, bottom=0.13, top=0.84, wspace=0.22)
        frames.append(frame(fig))
    plt.close(fig)
    save_gif(frames, "relaxation_random_walk.gif", duration=90)


# ----------------------------------------------------------------------------
# 2. third integral: meridional orbits in a flattened logarithmic potential
# ----------------------------------------------------------------------------
QF, LZ, E0 = 0.7, 0.2, -0.25


def phi_eff(R, z):
    return 0.5 * np.log(R**2 + (z / QF) ** 2) + LZ**2 / (2 * R**2)


def integrate_meridional(R0, vR0, T=320.0, dt=0.004):
    R0 = np.asarray(R0, float); vR0 = np.asarray(vR0, float)
    vz0 = np.sqrt(2 * (E0 - phi_eff(R0, 0 * R0)) - vR0**2)
    R, z, vR, vz = R0.copy(), 0 * R0, vR0.copy(), vz0.copy()

    def acc(R, z):
        D = R**2 + (z / QF) ** 2
        return -R / D + LZ**2 / R**3, -(z / QF**2) / D

    n = int(T / dt)
    traj = np.empty((n + 1, 2, len(R0)))
    traj[0] = R, z
    sos = [[] for _ in R0]
    aR, az = acc(R, z)
    for k in range(n):
        vR += 0.5 * dt * aR; vz += 0.5 * dt * az
        zold = z.copy()
        R += dt * vR; z += dt * vz
        aR, az = acc(R, z)
        vR += 0.5 * dt * aR; vz += 0.5 * dt * az
        traj[k + 1] = R, z
        cross = (zold < 0) & (z >= 0)
        for i in np.nonzero(cross)[0]:
            sos[i].append((k + 1, R[i], vR[i]))
    return traj, [np.array(s) for s in sos], n


def third_integral():
    R0 = np.array([0.3, 0.68, 0.45, 0.55, 0.38, 0.6])
    vR0 = np.array([0.0, 0.0, 0.0, 0.0, 0.25, 0.15])
    traj, sos, n = integrate_meridional(R0, vR0)
    cols = [BLUE, RED, GREEN, ORANGE, PURPLE, GRAY]
    Rg, zg = np.meshgrid(np.linspace(0.05, 1.6, 400), np.linspace(-1.1, 1.1, 400))
    pe = phi_eff(Rg, zg)
    nfr = 80
    idx = np.r_[n, np.linspace(0, n, nfr).astype(int)[1:]]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.8, 4.5), dpi=105, gridspec_kw={"width_ratios": [1.05, 1]})
    frames = []
    for j, k in enumerate(idx):
        ax1.clear(); ax2.clear()
        ax1.contourf(Rg, zg, pe, levels=[pe.min(), E0], colors=[LIGHT])
        ax1.contour(Rg, zg, pe, levels=[E0], colors=[GRAY], linewidths=1.3)
        for i, c in ((0, BLUE), (1, RED)):
            kk = k
            ax1.plot(traj[:kk + 1:4, 0, i], traj[:kk + 1:4, 1, i], color=c, lw=0.35, alpha=0.75)
        ax1.text(0.03, 0.69, "灰线：$\\Phi_{\\rm eff}(R,z)=E$ 的零速度曲线", color=GRAY, fontsize=9)
        ax1.text(0.03, 0.61, "两条轨道 $E$、$L_z$ 相同，却只占据允许区域的一部分", color="k", fontsize=9)
        ax1.set(xlim=(0, 0.95), ylim=(-0.6, 0.75), xlabel="$R$", ylabel="$z$", aspect="equal")
        ax1.set_title("子午面中的轨道" + ("" if j == 0 else f"（$t={k * 0.004:.0f}$）"), fontsize=10.5)
        clean(ax1)
        for i, c in enumerate(cols):
            if j > 0 and i > 1:
                continue
            S = sos[i]
            if len(S) == 0:
                continue
            m = S[:, 0] <= k
            ax2.plot(S[m, 1], S[m, 2], ".", color=c, ms=3.5)
        Rs = np.linspace(0.05, 1.6, 600)
        vmax2 = 2 * (E0 - phi_eff(Rs, 0 * Rs))
        ok = vmax2 >= 0
        ax2.plot(Rs[ok], np.sqrt(vmax2[ok]), color=GRAY, lw=1); ax2.plot(Rs[ok], -np.sqrt(vmax2[ok]), color=GRAY, lw=1)
        ax2.text(0.13, 0.86, "每次以 $v_z>0$ 穿过 $z=0$ 时记下 $(R,v_R)$", color="k", fontsize=9)
        ax2.text(0.13, 0.77, "点落在闭合曲线上：还有一个守恒量", color=PURPLE, fontsize=9)
        ax2.set(xlim=(0.12, 0.82), ylim=(-0.85, 0.95), xlabel="$R$", ylabel="$v_R$")
        ax2.set_title("庞加莱截面" + ("（六条轨道，相同 $E$、$L_z$）" if j == 0 else ""), fontsize=10.5)
        clean(ax2)
        fig.suptitle("第三积分：扁平轴对称势 $\\Phi=\\frac{1}{2}\\ln(R^2+z^2/q^2)$，$q=0.7$", fontsize=12)
        fig.subplots_adjust(left=0.06, right=0.98, bottom=0.12, top=0.86, wspace=0.18)
        frames.append(frame(fig))
    plt.close(fig)
    save_gif(frames, "third_integral.gif", duration=90)


# ----------------------------------------------------------------------------
# 3. non-singular isothermal sphere
# ----------------------------------------------------------------------------
def isothermal_sphere():
    def rhs(x, y):
        psi, dpsi = y
        return [dpsi, np.exp(-psi) - 2 * dpsi / x]
    x0 = 1e-4
    sol = solve_ivp(rhs, (x0, 1e4), [x0**2 / 6, x0 / 3], dense_output=True, rtol=1e-10, atol=1e-12)
    x = np.logspace(-2, 4, 800)
    psi, dpsi = sol.sol(x)
    rho = np.exp(-psi)
    vc = np.sqrt(x * dpsi)                 # v_c / sigma
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.0), dpi=170)
    ax1.loglog(x, rho, color=BLUE, lw=2, label="非奇异等温球（数值解）")
    ax1.loglog(x, 2 / x**2, color=RED, ls="--", lw=1.3, label="奇异等温球 $\\rho/\\rho_0=2/x^2$")
    ax1.axvline(3, color=GRAY, lw=0.8, ls=":")
    ax1.text(2.7, 3e-2, "核心半径 $\\sim3r_0$", color=GRAY, fontsize=9.5, ha="right")
    ax1.set(xlim=(1e-2, 1e4), ylim=(1e-8, 3), xlabel="$x=r/r_0$，$r_0=\\sigma/\\sqrt{4\\pi G\\rho_0}$", ylabel="$\\rho/\\rho_0$")
    ax1.legend(frameon=False, fontsize=9, loc="lower left")
    ax1.set_title("密度：中心有平坦核心，外区趋于 $r^{-2}$", fontsize=10.5)
    clean(ax1)
    ax2.semilogx(x, vc, color=BLUE, lw=2, label="$v_c/\\sigma$")
    ax2.axhline(np.sqrt(2), color=RED, ls="--", lw=1.3, label="$\\sqrt{2}$（奇异解）")
    ax2.set(xlim=(1e-2, 1e4), ylim=(0, 1.75), xlabel="$x=r/r_0$", ylabel="$v_c/\\sigma$")
    ax2.legend(frameon=False, fontsize=9, loc="lower right")
    ax2.set_title("旋转曲线：内区上升，外区以小幅振荡趋于平坦", fontsize=10.5)
    clean(ax2)
    fig.suptitle("等温球方程 $\\frac{1}{x^2}\\frac{d}{dx}\\left(x^2\\frac{d\\psi}{dx}\\right)=e^{-\\psi}$，$\\psi=\\Phi/\\sigma^2$，$\\rho=\\rho_0e^{-\\psi}$", fontsize=11.5)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(OUT / "isothermal_sphere.png", bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    print("isothermal_sphere.png; max vc/sigma", vc.max(), "at x", x[np.argmax(vc)])


if __name__ == "__main__":
    relaxation_random_walk()
    third_integral()
    isothermal_sphere()
