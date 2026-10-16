"""Figure for the 中间轴定理 / 贾尼别科夫效应 subsection of 刚体运动.md.

Run: python3 make_dzhanibekov.py   (needs numpy, scipy, matplotlib, Noto Sans CJK)
Output: dzhanibekov.png next to this script.
Units: I_2 = 1 (I_1 : I_2 : I_3 = 1 : 2 : 3 rescaled), Omega_0 = 1.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from scipy.integrate import solve_ivp
from scipy.special import ellipk

for f in font_manager.findSystemFonts():
    if "NotoSansCJK-Regular" in f:
        font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": ["Noto Sans CJK SC", "Noto Sans CJK JP"],
                     "mathtext.fontset": "cm", "axes.unicode_minus": False,
                     "font.size": 11, "savefig.dpi": 220})
OUT = os.path.dirname(os.path.abspath(__file__)) + "/"
BLUE = "#1f4e9c"; RED = "#c8102e"; ORANGE = "#e08a00"; GREEN = "#2e7d32"; GRAY = "#777777"

I1, I2, I3 = 1.0, 2.0, 3.0

def euler(t, w):
    w1, w2, w3 = w
    return [(I2 - I3)*w2*w3/I1, (I3 - I1)*w3*w1/I2, (I1 - I2)*w1*w2/I3]

lam = np.sqrt((I3 - I2)*(I2 - I1)/(I1*I3))          # growth rate for Omega_0 = 1

def flip_interval_exact(w):
    w1, w2, w3 = w
    E2 = I1*w1**2 + I2*w2**2 + I3*w3**2              # 2E
    M2 = (I1*w1)**2 + (I2*w2)**2 + (I3*w3)**2
    if M2 < E2*I2:                                    # swap roles of axes 1 and 3
        a, c = I3, I1
    else:
        a, c = I1, I3
    nu = np.sqrt(abs((c - I2)*(M2 - E2*a))/(I1*I2*I3))
    k2 = (I2 - a)*(E2*c - M2)/((c - I2)*(M2 - E2*a))
    return 2*ellipk(k2)/nu, np.sqrt(1 - k2), nu

fig = plt.figure(figsize=(11.2, 7.4))

# (a) time series ------------------------------------------------------------
ax = fig.add_axes([0.06, 0.58, 0.56, 0.36])
eps = 1e-2
w0 = [eps, 1.0, eps]
T = 60.0
tt = np.linspace(0, T, 6001)
sol = solve_ivp(euler, (0, T), w0, t_eval=tt, rtol=1e-11, atol=1e-13, method="DOP853")
turns = tt/(2*np.pi)
ax.plot(turns, sol.y[1], color=RED, lw=1.6, label=r"$\Omega_2$（中间轴）")
ax.plot(turns, sol.y[0], color=BLUE, lw=1.0, label=r"$\Omega_1$")
ax.plot(turns, sol.y[2], color=GREEN, lw=1.0, label=r"$\Omega_3$")
ax.axhline(0, color=GRAY, lw=0.5)
dt_flip, kp, nu = flip_interval_exact(w0)
tz = turns[np.nonzero(np.diff(np.sign(sol.y[1])))[0]]
ax.annotate("", xy=(tz[0] + dt_flip/(2*np.pi), -1.22), xytext=(tz[0], -1.22),
            arrowprops=dict(arrowstyle="<->", lw=0.9))
for z in tz[:2]:
    ax.plot([z, z], [-1.22, 0], color=GRAY, lw=0.6, ls=":")
ax.text(tz[0] + 0.5*dt_flip/(2*np.pi), -1.42, r"翻转间隔 $\Delta t$", ha="center", fontsize=9.5)
ax.set_xlim(0, T/(2*np.pi)); ax.set_ylim(-1.55, 1.25)
ax.set_xlabel(r"时间 $t$（以 $2\pi/\Omega_0$ 为单位，约等于转过的圈数）")
ax.set_ylabel(r"$\Omega_i/\Omega_0$")
ax.legend(loc="upper right", fontsize=9, ncol=3, frameon=False)
ax.set_title(r"(a) 绕中间轴抛出（$I_1:I_2:I_3=1:2:3$，初始扰动 $10^{-2}\Omega_0$）", fontsize=10.5)

# (b) polhodes on the angular-momentum sphere -------------------------------
ax3 = fig.add_axes([0.62, 0.40, 0.38, 0.58], projection="3d")
u, v = np.meshgrid(np.linspace(0, 2*np.pi, 60), np.linspace(0, np.pi, 30))
ax3.plot_surface(np.cos(u)*np.sin(v), np.sin(u)*np.sin(v), np.cos(v), color="#dfe6f0",
                 alpha=0.25, linewidth=0, shade=False)
def polhode(w, color, lw=1.0):
    s = solve_ivp(euler, (0, 40), w, max_step=0.02, rtol=1e-10, atol=1e-12)
    M = np.array([I1*s.y[0], I2*s.y[1], I3*s.y[2]])
    M /= np.linalg.norm(M, axis=0)
    for sgn in (1, -1):
        Mx, My, Mz = sgn*M
        ax3.plot(Mx, My, Mz, color=color, lw=lw)
for a in [0.08, 0.18, 0.3]:                      # around x1 (largest energy)
    polhode([1.0, a, 0.0], BLUE)
for a in [0.35, 0.7, 1.05]:                      # around x3 (smallest energy)
    polhode([0.0, a, 1.0], GREEN)
# separatrix: start next to the +x2 pole on the unstable direction
polhode([1e-4*np.sqrt(I2*(I3 - I2)/(I1*(I3 - I1))), 1.0, 1e-4*np.sqrt(I2*(I2 - I1)/(I3*(I3 - I1)))], RED, 1.6)
polhode([-1e-4*np.sqrt(I2*(I3 - I2)/(I1*(I3 - I1))), 1.0, 1e-4*np.sqrt(I2*(I2 - I1)/(I3*(I3 - I1)))], RED, 1.6)
for vec, lab in [((1.35, 0, 0), r"$x_1$"), ((0, 1.35, 0), r"$x_2$"), ((0, 0, 1.35), r"$x_3$")]:
    ax3.plot([0, vec[0]], [0, vec[1]], [0, vec[2]], color="k", lw=0.8)
    ax3.text(*[1.08*c for c in vec], lab, fontsize=11)
ax3.set_box_aspect((1, 1, 1)); ax3.set_axis_off()
ax3.view_init(elev=22, azim=35)
ax3.set_title("(b) $\\boldsymbol{M}$ 在刚体系中的轨迹\n（蓝：绕 $x_1$；绿：绕 $x_3$；红：分离轨道）",
              fontsize=10.5, pad=-6)

# (c) flip interval vs perturbation -----------------------------------------
ax = fig.add_axes([0.06, 0.08, 0.40, 0.36])
epss = np.logspace(-6, -0.7, 12)
num, exact, asym = [], [], []
for e in epss:
    w = [e, 1.0, e]
    dtx, kp, nu = flip_interval_exact(w)
    s = solve_ivp(euler, (0, 4*dtx + 20), w, rtol=1e-12, atol=1e-14, method="DOP853",
                  dense_output=True, max_step=0.05)
    tz = s.t[np.nonzero(np.diff(np.sign(s.y[1])))[0]]
    num.append(np.diff(tz).mean() if len(tz) > 1 else np.nan)
    exact.append(dtx); asym.append(2/lam*np.log(4/kp))
ee = np.logspace(-6.3, -0.5, 200)
ax.semilogx(epss, np.array(num)/(2*np.pi), "o", color=RED, ms=5, label="数值积分")
ax.semilogx(epss, np.array(asym)/(2*np.pi), "-", color="k", lw=1.0,
            label=r"$\Delta t\approx\dfrac{2}{\lambda}\ln\dfrac{4}{k'}$")
ax.set_xlabel(r"初始扰动 $\epsilon=\Omega_1(0)/\Omega_0=\Omega_3(0)/\Omega_0$")
ax.set_ylabel(r"翻转间隔 $\Delta t\ /\ (2\pi/\Omega_0)$")
ax.legend(fontsize=9.5, frameon=False, loc="upper right")
ax.set_title("(c) 扰动每小 10 倍，翻转间隔只增加一个固定值", fontsize=10.5)

# (d) energy landscape on the sphere (Mercator-like map) --------------------
ax = fig.add_axes([0.56, 0.08, 0.42, 0.30])
ph, th = np.meshgrid(np.linspace(-np.pi, np.pi, 600), np.linspace(0, np.pi, 300))
m1 = np.sin(th)*np.cos(ph); m2 = np.sin(th)*np.sin(ph); m3 = np.cos(th)
Eg = 0.5*(m1**2/I1 + m2**2/I2 + m3**2/I3)        # energy for M = 1
cs = ax.contourf(ph, th, Eg, levels=24, cmap="viridis")
ax.contour(ph, th, Eg, levels=[0.5/I2], colors=RED, linewidths=1.6)
ax.plot([0, np.pi, -np.pi], [np.pi/2]*3, "^", color="w", ms=7, mec="k")
ax.plot([np.pi/2, -np.pi/2], [np.pi/2]*2, "x", color="w", ms=8, mew=2)
ax.plot([0], [0.04], "v", color="w", ms=7, mec="k")
ax.text(0.12, np.pi/2 + 0.08, r"$\pm x_1$：能量极大", color="w", fontsize=9)
ax.text(np.pi/2 + 0.12, np.pi/2 + 0.08, r"$\pm x_2$：鞍点", color="w", fontsize=9)
ax.text(0.15, 0.22, r"$\pm x_3$：能量极小", color="w", fontsize=9)
ax.set_xlabel(r"$\boldsymbol{M}$ 方向的方位角"); ax.set_ylabel(r"与 $x_3$ 轴的夹角")
ax.set_xticks([-np.pi, -np.pi/2, 0, np.pi/2, np.pi])
ax.set_xticklabels([r"$-\pi$", r"$-\pi/2$", "0", r"$\pi/2$", r"$\pi$"])
ax.set_yticks([0, np.pi/2, np.pi]); ax.set_yticklabels(["0", r"$\pi/2$", r"$\pi$"])
cb = fig.colorbar(cs, ax=ax, fraction=0.04, pad=0.02)
cb.set_label(r"$E/(M^2/I_2)$", fontsize=9)
ax.set_title(r"(d) 固定 $M$ 时转动能 $E$ 在方向球面上的“地形图”", fontsize=10.5)

fig.savefig(OUT + "dzhanibekov.png", bbox_inches="tight", facecolor="white")
print("lambda =", lam, " flip interval (eps=1e-2):", dt_flip, dt_flip/(2*np.pi), "turns")
for e, a, b, c in zip(epss, num, exact, asym):
    print(f"{e:.2e}  num {a:8.3f}  exact {b:8.3f}  asym {c:8.3f}")
