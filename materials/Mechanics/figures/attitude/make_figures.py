"""Figures for 欧拉角与航天器姿态控制.md (conventions of 刚体运动.md).

Passive attitude matrix R maps inertial components to body components; R_x, R_y, R_z as in the text.
  proper Euler angles (z-x-z):   R = R_z(psi) R_x(theta) R_z(phi)
  Tait-Bryan 3-2-1 angles:       R = R_x(Phi) R_y(Theta) R_z(Psi)
Kinematics: dR/dt = -[Omega x] R, Omega = body components of the angular velocity.
Quaternion q = (q0, qv), R = (q0^2 - qv.qv) 1 + 2 qv qv^T - 2 q0 [qv x],
  dq0/dt = -1/2 Omega.qv,  dqv/dt = 1/2 (q0 Omega + qv x Omega).
Run: python3 make_figures.py   (numpy, scipy, matplotlib, Noto Sans CJK)
"""
import os
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
                     "font.size": 10.5, "savefig.dpi": 220})
OUT = os.path.dirname(os.path.abspath(__file__)) + "/"
BLUE = "#1f4e9c"; RED = "#c8102e"; ORANGE = "#e08a00"; GREEN = "#2e7d32"; GRAY = "#777777"

def skew(w):
    return np.array([[0, -w[2], w[1]], [w[2], 0, -w[0]], [-w[1], w[0], 0]])

def Rx(a):
    c, s = np.cos(a), np.sin(a); return np.array([[1, 0, 0], [0, c, s], [0, -s, c]])
def Ry(a):
    c, s = np.cos(a), np.sin(a); return np.array([[c, 0, -s], [0, 1, 0], [s, 0, c]])
def Rz(a):
    c, s = np.cos(a), np.sin(a); return np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]])

def R_of_q(q):
    q0, qv = q[0], q[1:]
    return (q0**2 - qv @ qv)*np.eye(3) + 2*np.outer(qv, qv) - 2*q0*skew(qv)

def q_of_R(R):
    """Inverse of R_of_q (Shepperd-like, returns q0 >= 0)."""
    tr = np.trace(R)
    q0 = 0.5*np.sqrt(max(1 + tr, 0))
    if q0 > 1e-6:
        qv = np.array([R[1, 2] - R[2, 1], R[2, 0] - R[0, 2], R[0, 1] - R[1, 0]])/(4*q0)
    else:  # 180 degree case
        i = np.argmax(np.diag(R))
        qv = np.zeros(3); qv[i] = np.sqrt((1 + 2*R[i, i] - tr)/4)
        j, k = (i + 1) % 3, (i + 2) % 3
        qv[j] = (R[i, j] + R[j, i])/(4*qv[i]); qv[k] = (R[i, k] + R[k, i])/(4*qv[i])
    q = np.concatenate([[q0], qv]); return q/np.linalg.norm(q)

def qdot(q, w):
    q0, qv = q[0], q[1:]
    return np.concatenate([[-0.5*w @ qv], 0.5*(q0*w + np.cross(qv, w))])

def zxz_angles(R):
    th = np.arccos(np.clip(R[2, 2], -1, 1))
    ph = np.arctan2(R[2, 0], -R[2, 1])
    ps = np.arctan2(R[0, 2], R[1, 2])
    return ph, th, ps

def ypr_angles(R):
    Th = -np.arcsin(np.clip(R[0, 2], -1, 1))
    Ph = np.arctan2(R[1, 2], R[2, 2])
    Ps = np.arctan2(R[0, 1], R[0, 0])
    return Ph, Th, Ps

# ---------------------------------------------------------------- self-checks
_a, _b, _c = 0.7, 0.4, -1.1
assert np.allclose(zxz_angles(Rz(_c) @ Rx(_b) @ Rz(_a)), (_a, _b, _c))
assert np.allclose(ypr_angles(Rx(_a) @ Ry(_b) @ Rz(_c)), (_a, _b, _c))
_q = np.array([0.3, -0.5, 0.6, 0.2]); _q /= np.linalg.norm(_q)
assert np.allclose(q_of_R(R_of_q(_q)), _q*np.sign(_q[0]))
_w = np.array([0.3, -0.2, 0.5]); _dt = 1e-6
assert np.allclose((R_of_q(_q + _dt*qdot(_q, _w)) - R_of_q(_q))/_dt, -skew(_w) @ R_of_q(_q), atol=1e-4)
# z-x-z angular velocity formula of the text
_ph, _th, _ps = 0.3, 0.8, 1.2; _d = np.array([0.1, -0.4, 0.25])
_R0 = Rz(_ps) @ Rx(_th) @ Rz(_ph)
_R1 = Rz(_ps + _dt*_d[2]) @ Rx(_th + _dt*_d[1]) @ Rz(_ph + _dt*_d[0])
_W = -(_R1 - _R0)/_dt @ _R0.T
_Wv = np.array([_W[2, 1], _W[0, 2], _W[1, 0]])
_Wtext = np.array([_d[0]*np.sin(_th)*np.sin(_ps) + _d[1]*np.cos(_ps),
                   _d[0]*np.sin(_th)*np.cos(_ps) - _d[1]*np.sin(_ps),
                   _d[0]*np.cos(_th) + _d[2]])
assert np.allclose(_Wv, _Wtext, atol=1e-4)
print("self-checks passed")

# ------------------------------------------------- Fig 1: Euler-angle singularity
def fig_gimbal():
    # body spins uniformly about a fixed inertial axis; x3 passes close to Z
    w_I = np.array([1.0, 0.0, 0.0])                 # inertial rotation axis X, rate 1 rad/s
    R0 = Rx(np.deg2rad(-60)) @ Rz(np.deg2rad(4.0))  # initial attitude
    # make the x3-axis miss Z by ~2.5 degrees: tilt initial attitude slightly
    R0 = R0 @ Ry(np.deg2rad(2.5))
    t = np.linspace(0, 2.2, 4001)
    ang = []; qs = []
    q_prev = None
    for tt in t:
        # rotation of the body by angle tt about the inertial X axis: R(t) = R0 Rx(-tt)?  use exact composition
        R = R0 @ Rx(tt)        # body turned by angle tt about the inertial X axis
        ang.append(zxz_angles(R))
        q = q_of_R(R)
        if q_prev is not None and q @ q_prev < 0:
            q = -q
        q_prev = q; qs.append(q)
    ang = np.unwrap(np.array(ang), axis=0); qs = np.array(qs)
    rates = np.gradient(ang, t, axis=0)
    fig, axs = plt.subplots(3, 1, figsize=(7.4, 7.4), sharex=True,
                            gridspec_kw={"height_ratios": [1.1, 1.1, 1]})
    ax = axs[0]
    for k, (lab, c) in enumerate([(r"$\varphi$", BLUE), (r"$\theta$", RED), (r"$\psi$", GREEN)]):
        ax.plot(t, np.rad2deg(ang[:, k]), color=c, lw=1.4, label=lab)
    ax.set_ylabel("欧拉角（度）"); ax.legend(ncol=3, fontsize=9.5, frameon=False, loc="upper left")
    ax.set_title(r"刚体以恒定角速度 $|\boldsymbol{\Omega}|=1\ \mathrm{rad/s}$ 绕固定轴转动，$x_3$ 轴从 $Z$ 轴旁约 $2^\circ$ 处掠过",
                 fontsize=10.5)
    ax = axs[1]
    for k, (lab, c) in enumerate([(r"$\dot\varphi$", BLUE), (r"$\dot\theta$", RED), (r"$\dot\psi$", GREEN)]):
        ax.plot(t, rates[:, k], color=c, lw=1.4, label=lab)
    ax.axhline(1, color=GRAY, lw=0.6, ls=":"); ax.axhline(-1, color=GRAY, lw=0.6, ls=":")
    ax.set_ylabel(r"角度变化率（rad/s）"); ax.legend(ncol=3, fontsize=9.5, frameon=False, loc="upper left")
    ax.text(t[-1], 1.6, r"$|\boldsymbol{\Omega}|=1$", color=GRAY, ha="right", fontsize=9)
    ax = axs[2]
    for k, (lab, c) in enumerate([(r"$q_0$", "k"), (r"$q_1$", BLUE), (r"$q_2$", RED), (r"$q_3$", GREEN)]):
        ax.plot(t, qs[:, k], color=c, lw=1.4, label=lab)
    ax.set_ylabel("四元数分量"); ax.set_xlabel(r"时间 $t$（s）")
    ax.legend(ncol=4, fontsize=9.5, frameon=False, loc="lower left")
    imin = np.argmin(ang[:, 1])
    for a in axs:
        a.axvline(t[imin], color=GRAY, lw=0.7, ls="--")
    axs[1].text(t[imin] + 0.03, axs[1].get_ylim()[0]*0.8, r"$\theta$ 最小（$\sin\theta\to0$）", fontsize=9, color=GRAY)
    fig.tight_layout()
    fig.savefig(OUT + "euler_singularity.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
    print("theta_min (deg) =", np.rad2deg(ang[imin, 1]), " max |phidot| =", np.abs(rates[:, 0]).max())

# ------------------------------------------------- Fig 2: quaternion-feedback slew with reaction wheels
def fig_slew():
    I = np.diag([1800.0, 2300.0, 2700.0])           # kg m^2 (a small space telescope)
    Iinv = np.linalg.inv(I)
    wn, zeta = 0.035, 1.0
    Kp = 2*wn**2*np.trace(I)/3*np.eye(3)            # scalar gain k_p (small angles: q_v ~ chi/2)
    Kd = 2*zeta*wn*I
    umax = 0.8                                       # N m, reaction-wheel torque limit
    R_t = np.eye(3)                                  # target attitude
    # initial attitude: 3-2-1 angles (Phi, Theta, Psi) = (40, -30, 100) deg relative to target
    R0 = Rx(np.deg2rad(40)) @ Ry(np.deg2rad(-30)) @ Rz(np.deg2rad(100))
    q_init = q_of_R(R0)
    def rhs(t, y):
        q = y[:4]/np.linalg.norm(y[:4]); w = y[4:7]; h = y[7:10]
        qe = q_of_R(R_of_q(q) @ R_t.T)
        u = -Kp @ qe[1:] - Kd @ w
        u = np.clip(u, -umax, umax)
        wdot = Iinv @ (u - np.cross(w, I @ w + h))
        hdot = -u
        return np.concatenate([qdot(q, w), wdot, hdot])
    y0 = np.concatenate([q_init, np.zeros(3), np.zeros(3)])
    T = 400
    tt = np.linspace(0, T, 4001)
    sol = solve_ivp(rhs, (0, T), y0, t_eval=tt, rtol=1e-9, atol=1e-11, max_step=0.5)
    ypr = []; chi = []; U = []
    for k in range(len(tt)):
        q = sol.y[:4, k]/np.linalg.norm(sol.y[:4, k])
        R = R_of_q(q) @ R_t.T
        ypr.append(ypr_angles(R))
        qe = q_of_R(R)
        chi.append(2*np.arccos(np.clip(qe[0], -1, 1)))
        U.append(np.clip(-Kp @ qe[1:] - Kd @ sol.y[4:7, k], -umax, umax))
    ypr = np.rad2deg(np.array(ypr)); chi = np.rad2deg(np.array(chi)); U = np.array(U)
    Mtot = np.array([I @ sol.y[4:7, k] + sol.y[7:10, k] for k in range(len(tt))])
    fig, axs = plt.subplots(2, 2, figsize=(10.0, 6.6), sharex=True)
    ax = axs[0, 0]
    for k, (lab, c) in enumerate([(r"滚转 $\Phi$", BLUE), (r"俯仰 $\Theta$", RED), (r"偏航 $\Psi$", GREEN)]):
        ax.plot(tt, ypr[:, k], color=c, lw=1.4, label=lab)
    ax.plot(tt, chi, color="k", lw=1.0, ls="--", label=r"欧拉转角 $\chi$")
    ax.set_ylabel("相对目标姿态（度）"); ax.legend(fontsize=9, frameon=False)
    ax.set_title("(a) 姿态误差：3-2-1 角与欧拉转角", fontsize=10.5)
    ax = axs[0, 1]
    for k, c in enumerate([BLUE, RED, GREEN]):
        ax.plot(tt, np.rad2deg(sol.y[4 + k]), color=c, lw=1.4, label=rf"$\Omega_{k+1}$")
    ax.set_ylabel("本体角速度（度/秒）"); ax.legend(fontsize=9, frameon=False)
    ax.set_title(r"(b) 本体角速度 $\Omega_i$", fontsize=10.5)
    ax = axs[1, 0]
    for k, c in enumerate([BLUE, RED, GREEN]):
        ax.plot(tt, U[:, k], color=c, lw=1.4, label=rf"$K_{{\mathrm{{c}},{k+1}}}$")
    ax.axhline(umax, color=GRAY, lw=0.6, ls=":"); ax.axhline(-umax, color=GRAY, lw=0.6, ls=":")
    ax.set_ylabel(r"控制力矩（N$\cdot$m）"); ax.set_xlabel(r"时间 $t$（s）")
    ax.legend(fontsize=9, frameon=False, ncol=3)
    ax.set_title("(c) 反作用轮施加在本体上的力矩（饱和 0.8 N·m）", fontsize=10.5)
    ax = axs[1, 1]
    for k, c in enumerate([BLUE, RED, GREEN]):
        ax.plot(tt, sol.y[7 + k], color=c, lw=1.4, label=rf"$h_{k+1}$")
    ax.plot(tt, np.linalg.norm(Mtot, axis=1), color="k", lw=1.0, ls="--",
            label=r"$|I\boldsymbol{\Omega}+\boldsymbol{h}|$")
    ax.set_ylabel(r"角动量（N$\cdot$m$\cdot$s）"); ax.set_xlabel(r"时间 $t$（s）")
    ax.legend(fontsize=9, frameon=False, ncol=2)
    ax.set_title(r"(d) 反作用轮角动量 $h_i$ 与总角动量", fontsize=10.5)
    fig.tight_layout()
    fig.savefig(OUT + "attitude_slew.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
    print("initial error angle chi =", chi[0], " final =", chi[-1], " max |M_tot| =", np.abs(Mtot).max())

fig_gimbal()
fig_slew()
