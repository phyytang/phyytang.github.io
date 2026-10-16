"""Generate teaching media for 无碰撞粒子体系.md."""

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
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image


OUT = Path(__file__).resolve().parent
BLUE = "#1f4e9c"
RED = "#c8102e"
GREEN = "#2e7d32"
ORANGE = "#e08a00"
PURPLE = "#6f4c9b"
GRAY = "#666666"
LIGHT = "#dce6f3"

for candidate in (
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
):
    if Path(candidate).exists():
        font_manager.fontManager.addfont(candidate)
for candidate in font_manager.findSystemFonts():
    if "NotoSansCJK-Regular" in candidate:
        font_manager.fontManager.addfont(candidate)
plt.rcParams.update(
    {
        "font.family": ["Hiragino Sans GB", "Heiti TC", "Noto Sans CJK SC", "DejaVu Sans"],
        "mathtext.fontset": "cm",
        "axes.unicode_minus": False,
        "font.size": 10.5,
    }
)


def clean(ax):
    ax.spines[["top", "right"]].set_visible(False)


def frame(fig):
    fig.canvas.draw()
    return Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[..., :3].copy())


def crop_uniform(frames, padding=8):
    boxes = []
    for im in frames:
        rgb = np.asarray(im.convert("RGB"))
        ys, xs = np.nonzero(np.any(rgb < 250, axis=2))
        if len(xs):
            boxes.append((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    if not boxes:
        return frames
    w, h = frames[0].size
    box = (
        max(0, min(b[0] for b in boxes) - padding),
        max(0, min(b[1] for b in boxes) - padding),
        min(w, max(b[2] for b in boxes) + padding),
        min(h, max(b[3] for b in boxes) + padding),
    )
    return [im.crop(box) for im in frames]


def save_gif(frames, name, duration=70, hold=2200):
    frames = crop_uniform(frames)
    pal = [im.convert("P", palette=Image.Palette.ADAPTIVE, colors=128) for im in frames]
    durations = [hold] + [duration] * (len(pal) - 1)
    pal[0].save(OUT / name, save_all=True, append_images=pal[1:], duration=durations,
                loop=0, optimize=True, disposal=2)
    print(name, pal[0].size, f"{(OUT / name).stat().st_size / 1024**2:.2f} MiB")


def integrate_anharmonic(q0, v0, dt=0.025, steps=5200):
    """Vectorized leapfrog for Phi=q^2/2+0.08 q^4."""
    q = q0.copy(); v = v0.copy()
    qs, vs = [], []
    acceleration = lambda x: -x - 0.32 * x**3
    v += 0.5 * dt * acceleration(q)
    for i in range(steps):
        q += dt * v
        v += dt * acceleration(q)
        if i % 40 == 0:
            qs.append(q.copy()); vs.append(v.copy())
    v -= 0.5 * dt * acceleration(q)
    return np.asarray(qs), np.asarray(vs)


def phase_mixing():
    rng = np.random.default_rng(12)
    n = 420
    # A compact patch crossing several anharmonic energy shells.
    q0 = 1.10 + 0.25 * rng.normal(size=n)
    v0 = 0.05 + 0.23 * rng.normal(size=n)
    qs, vs = integrate_anharmonic(q0, v0)
    keep = np.arange(0, len(qs), 2)
    keep = np.r_[min(45, len(qs) - 1), keep, keep[::-1]]
    colors = np.arctan2(v0, q0)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.4, 4.15), dpi=125)
    frames = []
    for k in keep:
        ax1.clear(); ax2.clear()
        q, v = qs[k], vs[k]
        ax1.scatter(q, v, c=colors, cmap="viridis", s=8, alpha=0.7, linewidths=0)
        x = np.linspace(-2.0, 2.0, 500)
        for energy in (0.4, 0.8, 1.25, 1.8):
            vv = np.sqrt(np.maximum(0, 2 * (energy - 0.5 * x**2 - 0.08 * x**4)))
            mask = vv > 0
            ax1.plot(x[mask], vv[mask], color="#b8c3d2", lw=0.65)
            ax1.plot(x[mask], -vv[mask], color="#b8c3d2", lw=0.65)
        ax1.set(xlim=(-2.05, 2.05), ylim=(-2.0, 2.0), xlabel="$x$", ylabel="$v$")
        ax1.set_title("细粒化相空间：相点被拉成长丝")
        clean(ax1)

        bins = np.linspace(-2.05, 2.05, 45)
        ax2.hist(q, bins=bins, density=True, color=LIGHT, edgecolor=BLUE, lw=0.5)
        ax2.hist(q, bins=12, density=True, histtype="step", color=RED, lw=2.0, label="粗粒化分布")
        ax2.set(xlim=(-2.05, 2.05), ylim=(0, 0.78), xlabel="$x$", ylabel="数密度")
        ax2.set_title("有限分辨率下看起来逐渐平滑")
        ax2.legend(frameon=False, loc="upper right")
        clean(ax2)
        fig.suptitle(f"相混合：沿每条轨道仍有 $df/dt=0$，但不同能量轨道的频率不同（$t={k:.0f}$）", fontsize=12)
        fig.tight_layout(rect=(0, 0, 1, 0.94))
        frames.append(frame(fig))
    plt.close(fig)
    save_gif(frames, "phase_mixing.gif", duration=65)


def collisionless_characteristics():
    rng = np.random.default_rng(4)
    n = 260
    x0 = 0.9 + 0.22 * rng.normal(size=n)
    v0 = -0.15 + 0.22 * rng.normal(size=n)
    weight = np.exp(-((x0 - 0.9) ** 2 + (v0 + 0.15) ** 2) / (2 * 0.22**2))
    phases = np.r_[1.0, np.linspace(0, 2 * np.pi, 94, endpoint=False)]
    orbit = np.linspace(0, 2 * np.pi, 500)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.4, 3.95), dpi=125)
    frames = []
    special = np.argmax(weight)
    vertical_jitter = 0.035 * np.random.default_rng(7).normal(size=n)
    for t in phases:
        ax1.clear(); ax2.clear()
        x = x0 * np.cos(t) + v0 * np.sin(t)
        v = -x0 * np.sin(t) + v0 * np.cos(t)
        ax1.axhline(0, color="black", lw=1)
        ax1.scatter(x, vertical_jitter, c=weight, cmap="plasma",
                    s=14, alpha=0.75, linewidths=0)
        ax1.plot([x[special]], [0], "o", color=GREEN, ms=9, mec="black", mew=0.5)
        ax1.arrow(x[special], 0.18, 0.32 * v[special], 0, color=GREEN, width=0.012,
                  head_width=0.08, length_includes_head=True)
        ax1.set(xlim=(-1.75, 1.75), ylim=(-0.35, 0.4), xlabel="真实空间位置 $x$")
        ax1.set_yticks([]); ax1.set_title("真实空间：恒星沿轨道运动")
        clean(ax1)

        ax2.plot(np.cos(orbit), -np.sin(orbit), color="#b8c3d2", lw=1)
        ax2.scatter(x, v, c=weight, cmap="plasma", s=14, alpha=0.75, linewidths=0)
        ax2.plot([x[special]], [v[special]], "o", color=GREEN, ms=9, mec="black", mew=0.5)
        ax2.arrow(x[special], v[special], 0.18 * v[special], -0.18 * x[special], color=GREEN,
                  width=0.009, head_width=0.07, length_includes_head=True)
        ax2.text(-1.55, 1.42, f"绿色相点携带的 $f={weight[special]:.2f}$ 始终不变", color=GREEN)
        ax2.set(xlim=(-1.62, 1.62), ylim=(-1.62, 1.62), xlabel="$x$", ylabel="$v$", aspect="equal")
        ax2.set_title("相空间：沿特征线输运")
        clean(ax2)
        fig.suptitle("无碰撞玻尔兹曼方程：分布函数沿单粒子轨道保持不变", fontsize=12)
        fig.tight_layout(rect=(0, 0, 1, 0.94))
        frames.append(frame(fig))
    plt.close(fig)
    save_gif(frames, "collisionless_characteristics.gif")


def vertical_jeans_equilibrium():
    rng = np.random.default_rng(9)
    n = 520
    sigma = 0.75
    z0 = rng.normal(scale=sigma, size=n)
    v0 = rng.normal(scale=sigma, size=n)
    phases = np.r_[1.0, np.linspace(0, 2 * np.pi, 96, endpoint=False)]
    zz = np.linspace(-2.8, 2.8, 400)
    analytic = np.exp(-0.5 * (zz / sigma) ** 2) / (np.sqrt(2 * np.pi) * sigma)
    fig = plt.figure(figsize=(9.4, 4.15), dpi=125)
    ax0 = fig.add_axes([0.075, 0.13, 0.205, 0.76])
    ax1 = fig.add_axes([0.35, 0.15, 0.28, 0.72])
    ax2 = fig.add_axes([0.69, 0.15, 0.28, 0.72])
    frames = []
    horizontal_positions = 0.85 * np.random.default_rng(11).normal(size=n)
    for t in phases:
        for ax in (ax0, ax1, ax2): ax.clear()
        z = z0 * np.cos(t) + v0 * np.sin(t)
        v = -z0 * np.sin(t) + v0 * np.cos(t)
        ax0.fill_between([-1.25, 1.25], [-0.08, -0.08], [0.08, 0.08], color="#d8b48b")
        ax0.scatter(horizontal_positions, z, s=5, color=BLUE, alpha=0.35, linewidths=0)
        ax0.set(xlim=(-1.35, 1.35), ylim=(-2.8, 2.8), ylabel="盘面高度 $z$")
        ax0.set_xticks([]); ax0.set_title("恒星不断穿越盘面")
        clean(ax0)

        ax1.hist(z, bins=np.linspace(-2.8, 2.8, 32), density=True, orientation="horizontal",
                 color=LIGHT, edgecolor=BLUE, lw=0.45)
        ax1.plot(analytic, zz, color=RED, lw=2, label="稳态密度 $\\nu(z)$")
        ax1.set(xlim=(0, 0.65), ylim=(-2.8, 2.8), xlabel="数密度")
        ax1.set_yticklabels([]); ax1.legend(frameon=False, loc="upper right", fontsize=9)
        ax1.set_title("宏观密度近似不变")
        clean(ax1)

        ax2.scatter(z, v, s=6, color=PURPLE, alpha=0.35, linewidths=0)
        ax2.set(xlim=(-2.8, 2.8), ylim=(-2.8, 2.8), xlabel="$z$", ylabel="$v_z$")
        ax2.set_title("速度弥散提供动力学支撑")
        ax2.text(-2.55, 2.42, "$\\partial_z(\\nu\\sigma_z^2)=-\\nu\\,\\partial_z\\Phi$", color=PURPLE)
        clean(ax2)
        fig.suptitle("竖直金斯平衡：微观恒星在运动，统计分布保持稳态", fontsize=12)
        frames.append(frame(fig))
    plt.close(fig)
    save_gif(frames, "vertical_jeans_equilibrium.gif")


def flat_rotation_curve():
    r = np.linspace(0.35, 8.0, 400)
    v_disk = 1.00 * np.sqrt(r) / (1 + r**2 / 3.0) ** 0.7
    v_halo = 1.00 * r / np.sqrt(r**2 + 1.0)
    v_total = np.sqrt(v_disk**2 + v_halo**2)
    fig, ax = plt.subplots(figsize=(7.8, 4.5), dpi=170)
    ax.plot(r, v_disk, color=ORANGE, lw=2, label="可见盘的贡献：外区下降")
    ax.plot(r, v_halo, color=BLUE, lw=2, label="近等温暗晕的贡献")
    ax.plot(r, v_total, color=RED, lw=2.5, label="总旋转曲线：近似平坦")
    ax.fill_between(r, v_disk, v_total, color=LIGHT, alpha=0.55)
    ax.text(4.25, 1.12, "$M(<r)\\propto r\\;\\Rightarrow\\;v_c^2=GM(<r)/r\\approx\\mathrm{const}$", color=RED)
    ax.set(xlim=(0.3, 8.0), ylim=(0, 1.30), xlabel="半径 $r$（示意单位）", ylabel="圆周速度 $v_c$")
    ax.set_title("平坦旋转曲线需要外区仍有持续增加的包围质量")
    ax.legend(frameon=False, loc="lower right")
    clean(ax); fig.tight_layout(pad=0.4)
    fig.savefig(OUT / "flat_rotation_curve.png", bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


def velocity_ellipsoid():
    fig, axs = plt.subplots(1, 3, figsize=(9.2, 3.25), dpi=170)
    phi = np.linspace(0, 2 * np.pi, 400)
    cases = [(0.70, 1.15, "切向占优", "$\\beta<0$", ORANGE),
             (1.0, 1.0, "各向同性", "$\\beta=0$", GREEN),
             (1.25, 0.70, "径向占优", "$\\beta>0$", BLUE)]
    for ax, (sr, st, title, beta, color) in zip(axs, cases):
        ax.fill(sr * np.cos(phi), st * np.sin(phi), color=color, alpha=0.18)
        ax.plot(sr * np.cos(phi), st * np.sin(phi), color=color, lw=2)
        ax.axhline(0, color="#bbbbbb", lw=0.7); ax.axvline(0, color="#bbbbbb", lw=0.7)
        ax.arrow(0, 0, 0.78 * sr, 0, color=RED, head_width=0.08, length_includes_head=True)
        ax.text(0.82 * sr, -0.15, "$\\sigma_r$", color=RED, ha="center")
        ax.arrow(0, 0, 0, 0.78 * st, color=PURPLE, head_width=0.08, length_includes_head=True)
        ax.text(0.12, 0.84 * st, "$\\sigma_t$", color=PURPLE)
        ax.set(xlim=(-1.45, 1.45), ylim=(-1.45, 1.45), aspect="equal", xlabel="$v_r$")
        ax.set_title(f"{title}\n{beta}")
        ax.set_yticks([]); clean(ax)
    fig.suptitle("速度椭球与各向异性参数 $\\beta=1-(\\sigma_\\theta^2+\\sigma_\\phi^2)/(2\\sigma_r^2)$", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.90), pad=0.35)
    fig.savefig(OUT / "velocity_ellipsoid.png", bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


def mass_anisotropy_degeneracy():
    r = np.logspace(-0.6, 1.0, 250)
    target = 0.82 / (1 + (r / 3.3) ** 0.35) + 0.13
    model_iso = target * (1 + 0.018 * np.sin(2 * np.log(r)))
    model_radial = target * (1 - 0.020 * np.sin(2 * np.log(r)))
    mass_iso = 1.0 * r ** 1.05
    mass_radial = 0.72 * r ** 1.20
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.2, 4.0), dpi=170)
    ax1.plot(r, model_iso, color=BLUE, lw=2.2, label="模型 A：$\\beta=0$")
    ax1.plot(r, model_radial, color=ORANGE, lw=2.2, ls="--", label="模型 B：$\\beta=0.5$")
    ax1.scatter(r[::18], target[::18], color=RED, s=18, label="同一组视线速度数据", zorder=4)
    ax1.set(xscale="log", xlabel="投影半径 $R$", ylabel="$\\sigma_{\\rm los}(R)$")
    ax1.set_title("投影速度弥散几乎不可区分")
    ax1.legend(frameon=False, fontsize=9); clean(ax1)
    ax2.plot(r, mass_iso, color=BLUE, lw=2.2, label="模型 A 的 $M(<r)$")
    ax2.plot(r, mass_radial, color=ORANGE, lw=2.2, ls="--", label="模型 B 的 $M(<r)$")
    ax2.set(xscale="log", yscale="log", xlabel="三维半径 $r$", ylabel="包围质量 $M(<r)$")
    ax2.set_title("对应的质量分布却明显不同")
    ax2.legend(frameon=False, fontsize=9); clean(ax2)
    fig.suptitle("质量—各向异性简并（示意）：只有视线速度时，$M(r)$ 与 $\\beta(r)$ 可以互相补偿", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.92), pad=0.45)
    fig.savefig(OUT / "mass_anisotropy_degeneracy.png", bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


def distribution_to_moments():
    fig, ax = plt.subplots(figsize=(9.2, 4.4), dpi=170)
    ax.set(xlim=(0, 10), ylim=(0, 5)); ax.axis("off")
    boxes = [
        (0.35, 1.65, 2.25, 1.65, "$f(\\boldsymbol{x},\\boldsymbol{v},t)$\n六维分布函数", BLUE),
        (3.35, 3.25, 2.35, 1.05, "$\\nu=\\int f\\,d^3v$\n零阶矩：数密度", GREEN),
        (3.35, 1.75, 2.35, 1.05, "$\\nu\\overline{v_i}=\\int fv_i\\,d^3v$\n一阶矩：平均流", ORANGE),
        (3.35, 0.25, 2.35, 1.05, "$\\nu\\overline{v_iv_j}=\\int fv_iv_j\\,d^3v$\n二阶矩：速度弥散", PURPLE),
        (6.75, 2.45, 2.55, 1.25, "连续性方程\n恒星数守恒", GREEN),
        (6.75, 0.85, 2.55, 1.25, "金斯方程\n引力 + 速度弥散支撑", RED),
    ]
    for x, y, w, h, text, color in boxes:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08", fc=color, ec=color,
                                    alpha=0.14, lw=1.7))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=color, fontsize=10.5)
    arrows = [((2.6, 2.48), (3.3, 3.77)), ((2.6, 2.48), (3.3, 2.27)), ((2.6, 2.48), (3.3, 0.77)),
              ((5.72, 3.77), (6.70, 3.05)), ((5.72, 2.27), (6.70, 2.95)),
              ((5.72, 2.27), (6.70, 1.48)), ((5.72, 0.77), (6.70, 1.48))]
    for start, end in arrows:
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=12, color=GRAY, lw=1.2))
    ax.text(5.0, 4.65, "对速度取矩：用信息损失换取可观测的低维方程", ha="center", fontsize=13)
    ax.text(5.0, 0.02, "矩层级不会自动封闭：一阶方程含二阶矩，二阶方程还会含三阶矩", ha="center", color=RED)
    fig.tight_layout(pad=0.15)
    fig.savefig(OUT / "distribution_to_moments.png", bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


if __name__ == "__main__":
    phase_mixing()
    collisionless_characteristics()
    vertical_jeans_equilibrium()
    flat_rotation_curve()
    velocity_ellipsoid()
    mass_anisotropy_degeneracy()
    distribution_to_moments()
