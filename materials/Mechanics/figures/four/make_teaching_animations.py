"""Generate the three teaching animations embedded in 刚体运动.md.

Outputs
-------
euler_angles_sequence.gif
    The intrinsic z-x-z construction of the Euler angles.
intermediate_axis_comparison.gif
    Torque-free rotations about the minimum, intermediate, and maximum
    principal-inertia axes, integrated from Euler's equations.
lagrange_top_nutation.gif
    A heavy symmetric top with simultaneous spin, precession, and nutation,
    integrated using the two cyclic momenta and the effective potential.

Run from any directory with
    python3 figures/four/make_teaching_animations.py
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "mechanics-mpl-cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image
from scipy.integrate import solve_ivp
from scipy.spatial.transform import Rotation


OUT = Path(__file__).resolve().parent
BLUE = "#1f4e9c"
RED = "#c8102e"
GREEN = "#2e7d32"
ORANGE = "#e08a00"
GRAY = "#777777"
LIGHT = "#dfe6f0"

for candidate in (
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
):
    if Path(candidate).exists():
        font_manager.fontManager.addfont(candidate)
for _f in font_manager.findSystemFonts():  # Linux fallback (Noto CJK)
    if "NotoSansCJK-Regular" in _f:
        font_manager.fontManager.addfont(_f)
plt.rcParams.update(
    {
        "font.family": ["Songti SC", "Heiti TC", "Arial Unicode MS", "Noto Sans CJK SC", "DejaVu Sans"],
        "mathtext.fontset": "cm",
        "axes.unicode_minus": False,
        "font.size": 10,
    }
)


def rot_x(a: float) -> np.ndarray:
    c, s = np.cos(a), np.sin(a)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])


def rot_z(a: float) -> np.ndarray:
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def qmul(q: np.ndarray, p: np.ndarray) -> np.ndarray:
    """Hamilton product for w-x-y-z quaternions."""
    w, x, y, z = q
    a, b, c, d = p
    return np.array(
        [
            w * a - x * b - y * c - z * d,
            w * b + x * a + y * d - z * c,
            w * c - x * d + y * a + z * b,
            w * d + x * c - y * b + z * a,
        ]
    )


def qmatrix(q: np.ndarray) -> np.ndarray:
    q = q / np.linalg.norm(q)
    w, x, y, z = q
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ]
    )


def frame_from_figure(fig: plt.Figure) -> Image.Image:
    fig.canvas.draw()
    rgba = np.asarray(fig.canvas.buffer_rgba()).copy()
    plt.close(fig)
    return Image.fromarray(rgba, "RGBA").convert("P", palette=Image.Palette.ADAPTIVE)


def crop_frames_uniformly(frames: list[Image.Image], padding: int = 8) -> list[Image.Image]:
    """Remove the common white border without changing the frame registration."""
    boxes = []
    for frame in frames:
        rgb = np.asarray(frame.convert("RGB"))
        nonwhite = np.any(rgb < 250, axis=2)
        ys, xs = np.nonzero(nonwhite)
        if len(xs):
            boxes.append((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    if not boxes:
        return frames

    width, height = frames[0].size
    left = max(0, min(box[0] for box in boxes) - padding)
    top = max(0, min(box[1] for box in boxes) - padding)
    right = min(width, max(box[2] for box in boxes) + padding)
    bottom = min(height, max(box[3] for box in boxes) + padding)
    return [frame.crop((left, top, right, bottom)) for frame in frames]


def save_gif(frames: list[Image.Image], name: str, duration: int = 70, hold: int | None = None) -> None:
    """hold: if given, frames[0] is an overview frame shown for `hold` ms (PDF shows only frame 0)."""
    frames = crop_frames_uniformly(frames)
    durations = [duration] * len(frames)
    if hold is not None:
        durations[0] = hold
    frames[0].save(
        OUT / name,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        disposal=2,
        optimize=True,
    )
    print(f"wrote {OUT / name} ({(OUT / name).stat().st_size / 1024**2:.2f} MiB)")


def box_vertices(size=(1.6, 1.0, 0.55)) -> np.ndarray:
    a, b, c = np.asarray(size) / 2
    return np.array([[sx * a, sy * b, sz * c] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)])


FACES = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]]


def draw_box(ax, Q: np.ndarray, size=(1.6, 1.0, 0.55), alpha=0.65) -> None:
    verts = box_vertices(size) @ Q.T
    polys = [[verts[i] for i in face] for face in FACES]
    pc = Poly3DCollection(polys, facecolors="#89a9d6", edgecolors="#24496f", linewidths=0.8, alpha=alpha)
    ax.add_collection3d(pc)


def draw_body_axes(ax, Q: np.ndarray, length=1.35, labels=True) -> None:
    colors = (BLUE, RED, GREEN)
    for i, (color, label) in enumerate(zip(colors, (r"$x_1$", r"$x_2$", r"$x_3$"))):
        v = Q[:, i]
        ax.quiver(0, 0, 0, *v, length=length, color=color, arrow_length_ratio=0.11, linewidth=1.5)
        if labels:
            ax.text(*(1.12 * length * v), label, color=color, fontsize=10, ha="center")


def finish_3d(ax, lim=2.0, elev=22, azim=35) -> None:
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_zlim(-lim, lim)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()


def smoothstep(x: float) -> float:
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def euler_angles_animation() -> None:
    phi_f, theta_f, psi_f = np.deg2rad([50.0, 38.0, 40.0])
    forward = []
    for u in np.linspace(0, 1, 10, endpoint=False):
        forward.append((0.0, 0.0, 0.0, "初始取向：随体系与惯性系重合"))
    for u in np.linspace(0, 1, 18, endpoint=False):
        forward.append((phi_f * smoothstep(u), 0.0, 0.0, r"第一步：绕固定轴 $Z$ 转动 $\varphi$"))
    for u in np.linspace(0, 1, 18, endpoint=False):
        forward.append((phi_f, theta_f * smoothstep(u), 0.0, r"第二步：绕节线转动 $\theta$"))
    for u in np.linspace(0, 1, 18):
        forward.append((phi_f, theta_f, psi_f * smoothstep(u), r"第三步：绕随体轴 $x_3$ 转动 $\psi$"))
    forward.extend([(phi_f, theta_f, psi_f, "最终取向") for _ in range(10)])
    sequence = forward + list(reversed(forward[10:-10]))
    # Overview frame (shown first, and the only frame visible in a PDF).
    sequence = [(phi_f, theta_f, psi_f, r"三步转动后的最终取向（$\varphi=50^\circ,\ \theta=38^\circ,\ \psi=40^\circ$）")] + sequence

    frames = []
    for phi, theta, psi, stage in sequence:
        Q = rot_z(phi) @ rot_x(theta) @ rot_z(psi)
        fig = plt.figure(figsize=(5.4, 4.2), dpi=230)
        ax = fig.add_subplot(111, projection="3d")
        draw_box(ax, Q, size=(1.70, 1.05, 0.44), alpha=0.58)
        draw_body_axes(ax, Q, length=1.40)
        # Fixed inertial axes.
        for i, label in enumerate((r"$X$", r"$Y$", r"$Z$")):
            v = np.eye(3)[:, i]
            ax.plot([0, 1.35 * v[0]], [0, 1.35 * v[1]], [0, 1.35 * v[2]], color=GRAY, lw=0.9, ls="--")
            ax.text(*(1.47 * v), label, color=GRAY, fontsize=10)
        # Line of nodes after the first rotation.
        node = rot_z(phi_f if theta > 1e-4 else phi)[:, 0]
        ax.plot([-1.50 * node[0], 1.50 * node[0]], [-1.50 * node[1], 1.50 * node[1]], [0, 0], color="black", lw=1.0)
        ax.text(*(1.54 * node), r"$ON$", fontsize=9)
        finish_3d(ax, 1.68, elev=24, azim=38)
        ax.set_title(stage, fontsize=11, pad=-2)
        frames.append(frame_from_figure(fig))
    save_gif(frames, "euler_angles_sequence.gif", duration=65, hold=3000)


def integrate_free_body(I: np.ndarray, omega0: np.ndarray, times: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    M0 = I * omega0
    # Choose the initial attitude so that the conserved angular momentum is vertical.
    rot0, _ = Rotation.align_vectors(np.array([[0.0, 0.0, 1.0]]), np.array([M0 / np.linalg.norm(M0)]))
    x, y, z, w = rot0.as_quat()
    q0 = np.array([w, x, y, z])

    def rhs(_t, state):
        omega = state[:3]
        q = state[3:] / np.linalg.norm(state[3:])
        w1, w2, w3 = omega
        domega = np.array(
            [
                (I[1] - I[2]) * w2 * w3 / I[0],
                (I[2] - I[0]) * w3 * w1 / I[1],
                (I[0] - I[1]) * w1 * w2 / I[2],
            ]
        )
        dq = 0.5 * qmul(q, np.r_[0.0, omega])
        return np.r_[domega, dq]

    sol = solve_ivp(rhs, (times[0], times[-1]), np.r_[omega0, q0], t_eval=times, rtol=2e-10, atol=2e-12, method="DOP853")
    q = sol.y[3:].T
    q /= np.linalg.norm(q, axis=1)[:, None]
    return sol.y[:3].T, q


def intermediate_axis_animation() -> None:
    I = np.array([1.0, 2.0, 2.8])
    times = np.linspace(0.0, 40.0, 128)
    initials = [np.array([1.0, 0.025, 0.018]), np.array([0.025, 1.0, 0.018]), np.array([0.025, 0.018, 1.0])]
    results = [integrate_free_body(I, w0, times) for w0 in initials]
    dims = np.sqrt(6 * np.array([I[1] + I[2] - I[0], I[0] + I[2] - I[1], I[0] + I[1] - I[2]]))
    dims = 2.05 * dims / dims.max()
    titles = [r"绕最小轴 $x_1$：稳定", r"绕中间轴 $x_2$：翻转", r"绕最大轴 $x_3$：稳定"]
    colors = (BLUE, RED, GREEN)
    # Cosine of the angle between the spin axis x_k and the fixed M (= Z): +1 aligned, -1 flipped.
    cosines = [np.array([qmatrix(q)[2, k] for q in results[k][1]]) for k in range(3)]
    j_over = int(np.argmin(cosines[1]))  # overview: the middle body is upside down

    def render(j: int, overview: bool) -> Image.Image:
        fig = plt.figure(figsize=(10.2, 4.7), dpi=100)
        for k in range(3):
            ax = fig.add_axes([0.005 + k / 3, 0.36, 0.325, 0.56], projection="3d")
            omega, quats = results[k]
            Q = qmatrix(quats[j])
            draw_box(ax, Q, size=dims, alpha=0.72)
            draw_body_axes(ax, Q, length=1.28, labels=True)
            ax.quiver(0, 0, -1.30, 0, 0, 2.55, color="black", arrow_length_ratio=0.07, linewidth=1.7)
            ax.text(0.06, 0.06, 1.38, r"固定的 $\boldsymbol{M}$", fontsize=9)
            finish_3d(ax, 1.52, elev=20, azim=38)
            fig.text(0.168 + k / 3, 0.94, titles[k], fontsize=12, ha="center", color=colors[k])
            a2 = fig.add_axes([0.045 + k / 3, 0.09, 0.27, 0.22])
            a2.plot(times, cosines[k], color=colors[k], lw=1.0, alpha=0.35 if not overview else 1.0)
            if not overview:
                a2.plot(times[: j + 1], cosines[k][: j + 1], color=colors[k], lw=1.6)
            a2.axvline(times[j], color=GRAY, lw=0.8, ls=":")
            a2.axhline(0, color=GRAY, lw=0.5)
            a2.set_ylim(-1.15, 1.15); a2.set_xlim(times[0], times[-1])
            a2.set_yticks([-1, 0, 1]); a2.tick_params(labelsize=8)
            a2.set_xlabel(r"$t$", fontsize=9, labelpad=0)
            if k == 0:
                a2.set_ylabel(r"$\cos\angle(x_k,\boldsymbol{M})$", fontsize=9)
            for sp in ("top", "right"):
                a2.spines[sp].set_visible(False)
        if overview:
            fig.text(0.5, 0.005, "总览：下排曲线为自转轴与固定角动量夹角的余弦，中间轴的余弦在 +1 与 −1 之间反复跳变（翻转）",
                     ha="center", fontsize=9.5, color="#333333")
        return frame_from_figure(fig)

    frames = [render(j_over, True)] + [render(j, False) for j in range(len(times))]
    save_gif(frames, "intermediate_axis_comparison.gif", duration=75, hold=3500)


def integrate_lagrange_top(times: np.ndarray):
    I1, I3, mgl = 1.0, 0.32, 0.75
    M3, Mz = 2.2, 1.93

    def rhs(_t, state):
        theta, vtheta, phi, psi = state
        s, c = np.sin(theta), np.cos(theta)
        N = Mz - M3 * c
        dU = N * M3 / (I1 * s) - N * N * c / (I1 * s**3) - mgl * s
        phidot = N / (I1 * s**2)
        psidot = M3 / I3 - phidot * c
        return [vtheta, -dU / I1, phidot, psidot]

    y0 = [0.72, 0.0, 0.0, 0.0]
    sol = solve_ivp(rhs, (times[0], times[-1]), y0, t_eval=times, rtol=2e-10, atol=2e-12, method="DOP853")
    return sol.y.T


def lagrange_top_animation() -> None:
    times = np.linspace(0.0, 26.0, 110)
    states = integrate_lagrange_top(times)
    axes = []
    for theta, _v, phi, _psi in states:
        Qaxis = rot_z(phi) @ rot_x(theta)
        axes.append(Qaxis[:, 2])
    axes = np.asarray(axes)

    frames = []
    for j, (theta, _vtheta, phi, psi) in enumerate(states):
        Q = rot_z(phi) @ rot_x(theta) @ rot_z(psi)
        e3, e1 = Q[:, 2], Q[:, 0]
        fig = plt.figure(figsize=(5.8, 4.15), dpi=320)
        ax = fig.add_subplot(111, projection="3d")
        # A stylized symmetric top: apex at the fixed point and a circular rim.
        center = 1.08 * e3
        radius = 0.62
        ang = np.linspace(0, 2 * np.pi, 50)
        rim = center[:, None] + radius * (e1[:, None] * np.cos(ang) + Q[:, 1, None] * np.sin(ang))
        apex = np.zeros(3)
        for m in range(0, len(ang), 4):
            ax.plot([apex[0], rim[0, m]], [apex[1], rim[1, m]], [apex[2], rim[2, m]], color="#89a9d6", lw=1.2)
        ax.plot(rim[0], rim[1], rim[2], color="#24496f", lw=1.4)
        ax.plot([0, 1.52 * e3[0]], [0, 1.52 * e3[1]], [0, 1.52 * e3[2]], color=GREEN, lw=2.0)
        ax.plot([center[0], center[0] + 0.75 * e1[0]], [center[1], center[1] + 0.75 * e1[1]], [center[2], center[2] + 0.75 * e1[2]], color=BLUE, lw=2.0)
        ax.scatter([0], [0], [0], color="black", s=24)
        ax.text(0.06, 0.04, -0.08, r"支点 $O$", fontsize=9)
        # Vertical axis, gravity, and the trace of the symmetry axis.
        ax.plot([0, 0], [0, 0], [-0.30, 1.70], color=GRAY, ls="--", lw=1.0)
        ax.text(0.05, 0.02, 1.70, r"$Z$", color=GRAY)
        ax.quiver(*center, 0, 0, -0.75, color=RED, arrow_length_ratio=0.17, linewidth=1.5)
        ax.text(center[0] + 0.08, center[1], center[2] - 0.55, r"$\mu\boldsymbol{g}$", color=RED, fontsize=9)
        trail = 1.50 * axes[: j + 1]
        ax.plot(trail[:, 0], trail[:, 1], trail[:, 2], color=ORANGE, lw=1.3)
        ax.scatter([1.50 * e3[0]], [1.50 * e3[1]], [1.50 * e3[2]], color=ORANGE, s=20)
        finish_3d(ax, 1.78, elev=22, azim=38)
        frames.append(frame_from_figure(fig))
    # Overview: the final frame (full trace of the axis) is shown first.
    frames = [frames[-1]] + frames
    save_gif(frames, "lagrange_top_nutation.gif", duration=70, hold=3000)


if __name__ == "__main__":
    euler_angles_animation()
    intermediate_axis_animation()
    lagrange_top_animation()
