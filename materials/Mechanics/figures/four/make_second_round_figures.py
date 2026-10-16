"""Generate the second-round teaching figures for 刚体运动.md.

The script creates

* inertia_distribution_comparison.png
* lagrange_top_effective_potential.png
* poinsot_construction.png

All numerical examples use dimensionless parameters stated in the figures.
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
from matplotlib.patches import Circle
from PIL import Image
from scipy.integrate import solve_ivp
from scipy.optimize import brentq, minimize_scalar
from scipy.spatial.transform import Rotation


OUT = Path(__file__).resolve().parent
BLUE = "#1f4e9c"
LIGHT_BLUE = "#9eb9de"
RED = "#c8102e"
GREEN = "#2e7d32"
ORANGE = "#e08a00"
GRAY = "#6f7782"
LIGHT = "#e9eef5"

for candidate in (
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
):
    if Path(candidate).exists():
        font_manager.fontManager.addfont(candidate)

plt.rcParams.update(
    {
        "font.family": ["Songti SC", "Heiti TC", "Arial Unicode MS", "DejaVu Sans"],
        "mathtext.fontset": "cm",
        "axes.unicode_minus": False,
        "font.size": 11,
    }
)


def save(fig: plt.Figure, name: str) -> None:
    path = OUT / name
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    image = Image.open(path).convert("RGB")
    pixels = np.asarray(image)
    nonwhite = np.any(pixels < 250, axis=2)
    ys, xs = np.nonzero(nonwhite)
    if len(xs):
        padding = 14
        box = (
            max(0, int(xs.min()) - padding),
            max(0, int(ys.min()) - padding),
            min(image.width, int(xs.max()) + padding + 1),
            min(image.height, int(ys.max()) + padding + 1),
        )
        image.crop(box).save(path)
    print(f"wrote {path}")


def inertia_distribution_figure() -> None:
    objects = [
        ("均匀实心球", r"$I=\frac{2}{5}MR^2$", 2 / 5, "solid_sphere"),
        ("均匀薄圆盘", r"$I=\frac{1}{2}MR^2$", 1 / 2, "disk"),
        ("均匀薄球壳", r"$I=\frac{2}{3}MR^2$", 2 / 3, "shell"),
        ("均匀细圆环", r"$I=MR^2$", 1.0, "ring"),
    ]

    fig, axes = plt.subplots(1, 4, figsize=(12.0, 3.35))
    for ax, (title, formula, coeff, kind) in zip(axes, objects):
        ax.set_aspect("equal")
        ax.set_xlim(-1.18, 1.18)
        ax.set_ylim(-1.52, 1.18)
        ax.axis("off")

        if kind == "solid_sphere":
            for radius in np.linspace(1.0, 0.05, 36):
                shade = 0.40 + 0.42 * radius
                ax.add_patch(Circle((0, 0), radius, color=plt.cm.Blues(shade), ec="none"))
            ax.add_patch(Circle((0, 0), 1.0, fill=False, ec=BLUE, lw=1.7))
        elif kind == "shell":
            ax.add_patch(Circle((0, 0), 1.0, fc="#f8fbff", ec=BLUE, lw=6.0))
            ax.add_patch(Circle((0, 0), 0.94, fill=False, ec="#d8e5f5", lw=1.0))
        elif kind == "disk":
            ax.add_patch(Circle((0, 0), 1.0, fc=LIGHT_BLUE, ec=BLUE, lw=1.7, alpha=0.88))
            for radius in (0.25, 0.5, 0.75):
                ax.add_patch(Circle((0, 0), radius, fill=False, ec="#dce6f4", lw=0.8))
        else:
            ax.add_patch(Circle((0, 0), 1.0, fill=False, ec=BLUE, lw=8.0))

        ax.scatter([0], [0], s=38, fc="white", ec="black", lw=1.0, zorder=5)
        ax.text(0.10, 0.08, r"$\odot\ z$", fontsize=12, va="bottom")
        ax.set_title(title, fontsize=13, pad=5)
        ax.text(0, -1.18, formula, ha="center", fontsize=13, color=BLUE)
        ax.plot([-0.92, 0.92], [-1.40, -1.40], color=LIGHT, lw=8, solid_capstyle="round")
        ax.plot(
            [-0.92, -0.92 + 1.84 * coeff],
            [-1.40, -1.40],
            color=ORANGE,
            lw=8,
            solid_capstyle="round",
        )

    fig.suptitle("同一质量 $M$、同一外半径 $R$：质量越靠外，转动惯量越大", fontsize=15, y=1.02)
    fig.text(0.5, 0.015, "转轴均过质心并垂直于图面；橙色条长表示 $I/(MR^2)$", ha="center", fontsize=10)
    fig.subplots_adjust(left=0.02, right=0.98, bottom=0.11, top=0.84, wspace=0.08)
    save(fig, "inertia_distribution_comparison.png")


def effective_potential_figure() -> None:
    I1, mgl, M3, Mz = 1.0, 0.75, 2.2, 1.93

    def ueff(theta):
        return (Mz - M3 * np.cos(theta)) ** 2 / (2 * I1 * np.sin(theta) ** 2) + mgl * np.cos(theta)

    theta = np.linspace(0.025, np.pi - 0.025, 4000)
    potential = ueff(theta)
    minimum = minimize_scalar(ueff, bounds=(0.03, np.pi - 0.03), method="bounded")
    theta0, umin = minimum.x, minimum.fun
    energy = ueff(0.72)

    residual = potential - energy
    roots = []
    for a, b, fa, fb in zip(theta[:-1], theta[1:], residual[:-1], residual[1:]):
        if fa * fb < 0:
            root = brentq(lambda x: ueff(x) - energy, a, b)
            if not roots or abs(root - roots[-1]) > 1e-5:
                roots.append(root)
    theta1, theta2 = roots

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 4.25))
    degrees = np.rad2deg(theta)
    ax1.plot(degrees, potential, color=BLUE, lw=2.2)
    ax1.axvline(0, color=GRAY, lw=0.8)
    ax1.axvline(180, color=GRAY, lw=0.8)
    ax1.set_xlim(0, 180)
    ax1.set_ylim(0.48, 3.2)
    ax1.set_xlabel(r"倾角 $\theta$（度）")
    ax1.set_ylabel(r"$U_{\rm eff}$")
    ax1.set_title("全局形状：两端的“势垒”")
    ax1.annotate(
        r"一般情形下 $U_{\rm eff}\to\infty$",
        xy=(8, min(ueff(np.deg2rad(8)), 3.0)),
        xytext=(35, 2.65),
        arrowprops=dict(arrowstyle="->", color=GRAY),
        fontsize=10,
    )
    ax1.grid(alpha=0.22)

    zoom = (theta > 0.43) & (theta < 0.81)
    ax2.plot(degrees[zoom], potential[zoom], color=BLUE, lw=2.4, label=r"$U_{\rm eff}(\theta)$")
    ax2.axhline(energy, color=RED, lw=1.8, ls="--", label=r"选定的 $E'$")
    ax2.fill_between(
        degrees[zoom],
        potential[zoom],
        energy,
        where=potential[zoom] <= energy,
        color=ORANGE,
        alpha=0.20,
        label="章动允许区间",
    )
    ax2.scatter(np.rad2deg([theta1, theta2]), [energy, energy], color=RED, zorder=5)
    ax2.scatter([np.rad2deg(theta0)], [umin], color=GREEN, zorder=5)
    ax2.annotate(
        r"$\theta_1$",
        (np.rad2deg(theta1), energy),
        xytext=(-3, 12),
        textcoords="offset points",
        ha="right",
    )
    ax2.annotate(
        r"$\theta_2$",
        (np.rad2deg(theta2), energy),
        xytext=(3, 12),
        textcoords="offset points",
        ha="left",
    )
    ax2.annotate(
        "势阑极小：稳定进动",
        (np.rad2deg(theta0), umin),
        xytext=(18, 16),
        textcoords="offset points",
        arrowprops=dict(arrowstyle="->", color=GREEN),
        color=GREEN,
        fontsize=10,
    )
    ax2.set_xlim(np.rad2deg(0.43), np.rad2deg(0.81))
    ax2.set_ylim(umin - 0.003, energy + 0.012)
    ax2.set_xlabel(r"倾角 $\theta$（度）")
    ax2.set_title("势阑底部：进动与章动")
    ax2.grid(alpha=0.22)
    ax2.legend(loc="upper center", fontsize=9, frameon=False)

    fig.suptitle(
        r"拉格朗日陀螺的有效势　$I_1'=1, \mu gl=0.75, M_3=2.2, M_Z=1.93$",
        fontsize=14,
        y=1.01,
    )
    fig.text(
        0.5,
        0.01,
        rf"$\theta_1={np.rad2deg(theta1):.1f}^\circ$，$\theta_2={np.rad2deg(theta2):.1f}^\circ$；$E'>U_{{\rm eff,min}}$ 时倾角在两转折点之间往复",
        ha="center",
        fontsize=10,
    )
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.16, top=0.84, wspace=0.25)
    save(fig, "lagrange_top_effective_potential.png")

    print(
        "effective-potential check:",
        f"theta_min={np.rad2deg(theta0):.6f} deg,",
        f"turning_points={np.rad2deg(theta1):.6f},{np.rad2deg(theta2):.6f} deg,",
        f"root_residual={max(abs(ueff(theta1)-energy), abs(ueff(theta2)-energy)):.3e}",
    )


def qmul(q: np.ndarray, p: np.ndarray) -> np.ndarray:
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


def torque_free_motion(I: np.ndarray, omega0: np.ndarray, times: np.ndarray):
    m0 = I * omega0
    initial_rotation, _ = Rotation.align_vectors(
        np.array([[0.0, 0.0, 1.0]]), np.array([m0 / np.linalg.norm(m0)])
    )
    x, y, z, w = initial_rotation.as_quat()
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

    state0 = np.r_[omega0, q0]
    sol = solve_ivp(
        rhs,
        (times[0], times[-1]),
        state0,
        t_eval=times,
        rtol=2e-11,
        atol=2e-13,
        method="DOP853",
    )
    quaternions = sol.y[3:].T
    quaternions /= np.linalg.norm(quaternions, axis=1)[:, None]
    rotations = np.asarray([qmatrix(q) for q in quaternions])
    return sol.y[:3].T, rotations


def set_equal_3d(ax, lim=1.25):
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_zlim(-lim, lim)
    ax.set_box_aspect((1, 1, 1))
    ax.set_axis_off()


def poinsot_figure() -> None:
    inertia = np.array([1.0, 2.0, 3.0])
    omega0 = np.array([0.55, 0.18, 0.85])
    times = np.linspace(0.0, 70.0, 1800)
    omega, rotations = torque_free_motion(inertia, omega0, times)

    twice_energy = np.sum(inertia * omega0**2)
    energy = 0.5 * twice_energy
    m_body = inertia * omega
    m_norm = np.linalg.norm(inertia * omega0)
    xi = omega / np.sqrt(twice_energy)
    r_space = np.einsum("nij,nj->ni", rotations, xi)
    plane_height = np.sqrt(twice_energy) / m_norm

    current = 1040
    q_now = rotations[current]
    ellipsoid_polhode = xi @ q_now.T
    contact = r_space[current]

    u = np.linspace(0, 2 * np.pi, 90)
    v = np.linspace(0, np.pi, 55)
    uu, vv = np.meshgrid(u, v)
    semiaxes = 1 / np.sqrt(inertia)
    body_surface = np.stack(
        [
            semiaxes[0] * np.sin(vv) * np.cos(uu),
            semiaxes[1] * np.sin(vv) * np.sin(uu),
            semiaxes[2] * np.cos(vv),
        ],
        axis=-1,
    )
    space_surface = body_surface @ q_now.T

    fig = plt.figure(figsize=(11.6, 4.45))
    ax1 = fig.add_subplot(1, 2, 1, projection="3d")
    ax2 = fig.add_subplot(1, 2, 2, projection="3d")

    # Fixed-space view: the current ellipsoid is tangent to the invariable plane.
    grid = np.linspace(-1.12, 1.12, 2)
    xx, yy = np.meshgrid(grid, grid)
    zz = np.full_like(xx, plane_height)
    ax1.plot_surface(xx, yy, zz, color="#dfe6ef", alpha=0.44, shade=False)
    ax1.plot_surface(
        space_surface[..., 0],
        space_surface[..., 1],
        space_surface[..., 2],
        color=LIGHT_BLUE,
        edgecolor="#b8cae2",
        linewidth=0.25,
        alpha=0.48,
        shade=False,
    )
    ax1.plot(
        ellipsoid_polhode[:, 0],
        ellipsoid_polhode[:, 1],
        ellipsoid_polhode[:, 2],
        color=RED,
        lw=2.0,
        label="polhode（随刚体）",
    )
    ax1.plot(
        r_space[:, 0],
        r_space[:, 1],
        r_space[:, 2] + 0.006,
        color=ORANGE,
        lw=2.2,
        label="herpolhode（不变平面）",
    )
    ax1.scatter(*contact, color="black", s=30, zorder=10)
    ax1.text(*(contact + np.array([0.05, 0.03, 0.04])), r"接触点 $P$", fontsize=10)
    ax1.quiver(0, 0, -0.15, 0, 0, 1.35, color="black", arrow_length_ratio=0.08, linewidth=1.5)
    ax1.text(0.04, 0.03, 1.18, r"固定的 $\boldsymbol{M}$", fontsize=10)
    ax1.text(-1.05, 0.85, plane_height + 0.04, "不变平面", color=GRAY, fontsize=10)
    ax1.set_title("惯性系：惯量椭球在固定平面上无滑动滚动", fontsize=11, y=0.91)
    ax1.view_init(elev=21, azim=-56)
    set_equal_3d(ax1, 1.25)
    ax1.text2D(
        0.03,
        0.80,
        "红：polhode（随刚体）\n橙：herpolhode（不变平面）",
        transform=ax1.transAxes,
        fontsize=9,
        va="top",
    )

    # Body-frame view: the polhode is painted on the body-fixed inertia ellipsoid.
    ax2.plot_surface(
        body_surface[..., 0],
        body_surface[..., 1],
        body_surface[..., 2],
        color=LIGHT_BLUE,
        edgecolor="#b8cae2",
        linewidth=0.25,
        alpha=0.52,
        shade=False,
    )
    ax2.plot(xi[:, 0], xi[:, 1], xi[:, 2], color=RED, lw=2.4)
    ax2.scatter(*xi[current], color="black", s=30)
    for axis, label, color in zip(np.eye(3), (r"$x_1$", r"$x_2$", r"$x_3$"), (BLUE, RED, GREEN)):
        ax2.quiver(0, 0, 0, *axis, length=1.05, color=color, arrow_length_ratio=0.08, linewidth=1.2)
        ax2.text(*(1.10 * axis), label, color=color, fontsize=10)
    ax2.set_title("随体系：polhode 是接触点在惯量椭球上的轨迹", fontsize=11, y=0.91)
    ax2.view_init(elev=24, azim=42)
    set_equal_3d(ax2, 1.16)

    fig.suptitle(r"泊安索构图　$I_1:I_2:I_3=1:2:3$", fontsize=15, y=0.985)
    fig.subplots_adjust(left=0.01, right=0.99, bottom=0.01, top=0.93, wspace=0.02)
    save(fig, "poinsot_construction.png")

    energy_series = 0.5 * np.sum(inertia * omega**2, axis=1)
    m_space = np.einsum("nij,nj->ni", rotations, m_body)
    plane_residual = r_space @ m_space[0] - np.sqrt(twice_energy)
    ellipsoid_residual = np.sum(inertia * xi**2, axis=1) - 1.0
    tangent_normal = q_now @ (inertia * xi[current])
    tangent_cross = np.linalg.norm(np.cross(tangent_normal, m_space[0]))
    print(
        "Poinsot checks:",
        f"relative_energy_drift={np.ptp(energy_series)/energy:.3e},",
        f"relative_M_drift={np.max(np.linalg.norm(m_space-m_space[0], axis=1))/m_norm:.3e},",
        f"ellipsoid_residual={np.max(np.abs(ellipsoid_residual)):.3e},",
        f"plane_residual={np.max(np.abs(plane_residual)):.3e},",
        f"tangent_cross={tangent_cross:.3e}",
    )


if __name__ == "__main__":
    inertia_distribution_figure()
    effective_potential_figure()
    poinsot_figure()
