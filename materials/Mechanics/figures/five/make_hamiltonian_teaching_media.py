"""Generate teaching media for 哈密顿力学.md.

The first GIF frame is a readable overview frame.  All frames are cropped with
one common bounding box so that the animation does not jump in Markdown.
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
from matplotlib.patches import FancyArrowPatch
from PIL import Image


OUT = Path(__file__).resolve().parent
BLUE = "#1f4e9c"
RED = "#c8102e"
GREEN = "#2e7d32"
ORANGE = "#e08a00"
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
    pal[0].save(
        OUT / name,
        save_all=True,
        append_images=pal[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(name, pal[0].size, f"{(OUT / name).stat().st_size / 1024**2:.2f} MiB")


def hamiltonian_flow():
    phases = np.linspace(0, 2 * np.pi, 84, endpoint=False)
    phases = np.r_[np.pi / 3, phases]
    tt = np.linspace(0, 2 * np.pi, 500)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.2, 4.0), dpi=125)
    frames = []
    qg, pg = np.meshgrid(np.linspace(-1.35, 1.35, 13), np.linspace(-1.35, 1.35, 13))
    for j, th in enumerate(phases):
        ax1.clear(); ax2.clear()
        q, p = np.cos(th), -np.sin(th)
        ax1.plot(tt, np.cos(tt), color=BLUE, lw=1.7, label="$q(t)$")
        ax1.plot(tt, -np.sin(tt), color=RED, lw=1.7, label="$p(t)$")
        ax1.axvline(th % (2 * np.pi), color=GRAY, lw=0.9, ls="--")
        ax1.plot([th % (2 * np.pi)], [q], "o", color=BLUE, ms=7)
        ax1.plot([th % (2 * np.pi)], [p], "o", color=RED, ms=7)
        ax1.set(xlim=(0, 2 * np.pi), ylim=(-1.25, 1.25), xlabel="$t$", ylabel="坐标与动量")
        ax1.set_xticks([0, np.pi, 2 * np.pi], ["0", "$\\pi$", "$2\\pi$"])
        ax1.legend(frameon=False, loc="upper right")
        clean(ax1)

        ax2.streamplot(qg, pg, pg, -qg, color="#bcc7d6", density=0.7, linewidth=0.7, arrowsize=0.7)
        for e in (0.25, 0.5, 0.8):
            r = np.sqrt(2 * e)
            ax2.plot(r * np.cos(tt), r * np.sin(tt), color="#aab4c3", lw=0.8)
        ax2.plot(np.cos(tt), -np.sin(tt), color=BLUE, lw=2.0)
        ax2.plot([q], [p], "o", color=RED, ms=8, zorder=5)
        ax2.arrow(q, p, 0.19 * p, -0.19 * q, color=RED, width=0.009, head_width=0.07,
                  length_includes_head=True, zorder=4)
        ax2.text(-1.37, 1.24, "$H=(p^2+q^2)/2=1/2$", color=BLUE)
        ax2.text(-1.37, 1.08, "$\\dot q=\\partial H/\\partial p,\\;\\dot p=-\\partial H/\\partial q$", color=GRAY)
        ax2.set(xlim=(-1.42, 1.42), ylim=(-1.42, 1.42), xlabel="$q$", ylabel="$p$", aspect="equal")
        clean(ax2)
        fig.suptitle("谐振子的哈密顿流：相点沿等能线运动，而不是沿能量梯度下降", fontsize=12)
        fig.tight_layout(rect=(0, 0, 1, 0.94))
        frames.append(frame(fig))
    plt.close(fig)
    save_gif(frames, "hamiltonian_flow.gif")


def action_angle_flow():
    phases = np.linspace(0, 2 * np.pi, 84, endpoint=False)
    phases = np.r_[1.1, phases]
    curve = np.linspace(0, 2 * np.pi, 500)
    m, omega, action = 2.0, 1.5, 1.0
    qamp = np.sqrt(2 * action / (m * omega))
    pamp = np.sqrt(2 * m * omega * action)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.2, 4.0), dpi=125)
    frames = []
    for th in phases:
        ax1.clear(); ax2.clear()
        q = qamp * np.sin(th); p = pamp * np.cos(th)
        ax1.plot(qamp * np.sin(curve), pamp * np.cos(curve), color=BLUE, lw=2)
        ax1.plot([q], [p], "o", color=RED, ms=8)
        ax1.arrow(q, p, 0.12 * qamp * np.cos(th), -0.12 * pamp * np.sin(th), color=RED,
                  width=0.008, head_width=0.08, length_includes_head=True)
        ax1.set(xlabel="$q$", ylabel="$p$", xlim=(-1.25 * qamp, 1.25 * qamp),
                ylim=(-1.25 * pamp, 1.25 * pamp))
        ax1.set_title("原变量：闭合椭圆轨道")
        clean(ax1)

        ax2.axhline(action, color=BLUE, lw=2)
        ax2.plot([th % (2 * np.pi)], [action], "o", color=RED, ms=8)
        ax2.arrow(th % (2 * np.pi), action, 0.48, 0, color=RED, width=0.012,
                  head_width=0.08, length_includes_head=True)
        ax2.text(0.15, 1.27, "$I=E/\\omega$：选择哪一条轨道", color=BLUE)
        ax2.text(0.15, 0.68, "$w(t)=\\omega t+w_0$：沿轨道的位置", color=GRAY)
        ax2.set(xlim=(0, 2 * np.pi), ylim=(0.5, 1.45), xlabel="角变量 $w$（模 $2\\pi$）", ylabel="作用量 $I$")
        ax2.set_xticks([0, np.pi, 2 * np.pi], ["0", "$\\pi$", "$2\\pi$"])
        ax2.set_title("作用量－角变量：匀速直线运动")
        clean(ax2)
        fig.suptitle("正则变换把周期运动写成“守恒作用量 + 线性相位”", fontsize=12)
        fig.tight_layout(rect=(0, 0, 1, 0.94))
        frames.append(frame(fig))
    plt.close(fig)
    save_gif(frames, "action_angle_flow.gif")


def liouville_flow():
    times = np.r_[1.0, np.linspace(0, 1.45, 52), np.linspace(1.45, 0, 52)]
    phi = np.linspace(0, 2 * np.pi, 300)
    q0, p0 = 0.72 * np.cos(phi), 0.42 * np.sin(phi)
    rng = np.random.default_rng(8)
    rr = np.sqrt(rng.random(260)); aa = 2 * np.pi * rng.random(260)
    qs, ps = 0.72 * rr * np.cos(aa), 0.42 * rr * np.sin(aa)
    colors = aa
    fig, ax = plt.subplots(figsize=(7.5, 4.3), dpi=125)
    frames = []
    area = np.pi * 0.72 * 0.42
    for t in times:
        ax.clear()
        q, p = np.exp(t) * q0, np.exp(-t) * p0
        qc, pc = np.exp(t) * qs, np.exp(-t) * ps
        ax.scatter(qc, pc, c=colors, cmap="viridis", s=8, alpha=0.65, linewidths=0)
        ax.plot(q0, p0, color=GRAY, lw=1.2, ls="--")
        ax.text(0.0, 0.47, "初始区域", color=GRAY, ha="center", fontsize=9.5)
        ax.plot(q, p, color=BLUE, lw=2)
        ax.quiver([-2.2, -1.1, 1.1, 2.2], [0.55, -0.55, 0.55, -0.55],
                  [-2.2, -1.1, 1.1, 2.2], [-0.55, 0.55, -0.55, 0.55],
                  color="#b8c3d2", angles="xy", scale_units="xy", scale=5.0, width=0.004)
        ax.text(-3.25, 0.98, "$H=qp:\\;q(t)=e^tq_0,\\;p(t)=e^{-t}p_0$", color=GRAY)
        ax.text(-3.25, 0.80, f"面积 $A={area:.3f}$（保持不变）", color=RED, fontsize=11)
        ax.text(-3.25, 0.64, f"长轴伸长 $e^t={np.exp(t):.2f}$，短轴压缩 $e^{{-t}}={np.exp(-t):.2f}$", color=BLUE)
        ax.set(xlim=(-3.35, 3.35), ylim=(-1.12, 1.12), xlabel="$q$", ylabel="$p$")
        ax.set_title("刘维尔定理：相点云可以拉伸、剪切和折叠，但相面积不变")
        clean(ax); fig.tight_layout()
        frames.append(frame(fig))
    plt.close(fig)
    save_gif(frames, "liouville_flow.gif", duration=65)


def legendre_transform():
    us = np.r_[0.9, np.linspace(-1.45, 1.45, 78), np.linspace(1.45, -1.45, 78)]
    x = np.linspace(-2.0, 2.0, 600)
    lag = 0.5 * x**2 + 0.08 * x**4
    fig, ax = plt.subplots(figsize=(7.5, 4.5), dpi=125)
    frames = []
    for u in us:
        ax.clear()
        Lu = 0.5 * u**2 + 0.08 * u**4
        p = u + 0.32 * u**3
        H = p * u - Lu
        tangent = Lu + p * (x - u)
        ax.plot(x, lag, color=BLUE, lw=2.2, label="$L(\\dot q)$")
        ax.plot(x, tangent, color=RED, lw=1.7, label="切线：斜率 $p$")
        ax.plot([u], [Lu], "o", color=RED, ms=8)
        ax.plot([0], [-H], "o", color=ORANGE, ms=8)
        ax.vlines(u, -1.45, Lu, color=GRAY, ls=":", lw=0.9)
        ax.text(-1.9, 2.02, f"$p=L'(\\dot q_*)={p:.2f}$", color=RED, fontsize=11)
        ax.text(-1.9, 1.72, f"纵轴截距 $=-H={-H:.2f}$", color=ORANGE, fontsize=11)
        ax.text(-1.9, 1.43, "用切线斜率 $p$ 取代切点位置 $\\dot q_*$", color=GRAY)
        ax.set(xlim=(-2.0, 2.0), ylim=(-1.5, 2.35), xlabel="$\\dot q$", ylabel="函数值")
        ax.set_title("勒让德变换的几何意义：$H=p\\dot q-L$")
        ax.legend(frameon=False, loc="lower right")
        clean(ax); fig.tight_layout()
        frames.append(frame(fig))
    plt.close(fig)
    save_gif(frames, "legendre_transform.gif", duration=55)


def adiabatic_invariant():
    omegas = np.r_[1.25, np.linspace(0.65, 1.65, 70), np.linspace(1.65, 0.65, 70)]
    phi = np.linspace(0, 2 * np.pi, 500)
    action = 1.0
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.2, 4.1), dpi=125)
    frames = []
    history_w, history_e = [], []
    for k, omega in enumerate(omegas):
        ax1.clear(); ax2.clear()
        qamp = np.sqrt(2 * action / omega); pamp = np.sqrt(2 * action * omega)
        if k == 0:
            for w_, c_ in ((0.65, GREEN), (1.0, ORANGE), (1.65, BLUE)):
                qa, pa = np.sqrt(2 * action / w_), np.sqrt(2 * action * w_)
                ax1.plot(qa * np.cos(phi), pa * np.sin(phi), color=c_, lw=2.0, label=f"$\\omega={w_:.2f}$")
            ax1.legend(frameon=False, loc="lower center", ncol=3, fontsize=9, handlelength=1.2, columnspacing=0.8)
            ax1.text(-1.95, 2.42, "三个椭圆形状不同，面积都等于 $2\\pi I=2\\pi$", color=RED)
        else:
            ax1.plot(qamp * np.cos(phi), pamp * np.sin(phi), color=BLUE, lw=2.2)
            ax1.fill(qamp * np.cos(phi), pamp * np.sin(phi), color=LIGHT, alpha=0.55)
            th = 0.18 * k
            ax1.plot([qamp * np.cos(th)], [pamp * np.sin(th)], "o", color=RED, ms=7)
            ax1.text(-1.95, 2.42, f"$\\omega={omega:.2f}$，面积 $=2\\pi I=2\\pi$", color=RED)
        ax1.set(xlim=(-2.0, 2.0), ylim=(-2.55, 2.75), xlabel="$q$", ylabel="$p$", aspect="equal")
        ax1.set_title("参数缓慢变化：椭圆变形，面积不变")
        clean(ax1)
        if k == 0:
            history_w = [omega]; history_e = [action * omega]
        else:
            history_w.append(omega); history_e.append(action * omega)
        if k == 0:
            for w_, c_ in ((0.65, GREEN), (1.0, ORANGE), (1.65, BLUE)):
                ax2.plot([w_], [action * w_], "o", color=c_, ms=8)
        else:
            ax2.plot(history_w, history_e, color=ORANGE, lw=1.5)
            ax2.plot([omega], [action * omega], "o", color=RED, ms=7)
        ax2.plot([0.6, 1.7], [0.6, 1.7], color=BLUE, ls="--", lw=1.2, label="$E=I\\omega$")
        ax2.text(0.64, 1.57, "$I=E/\\omega=1$", color=BLUE, fontsize=11)
        ax2.set(xlim=(0.58, 1.72), ylim=(0.55, 1.78), xlabel="缓慢变化的频率 $\\omega$", ylabel="能量 $E$")
        ax2.set_title("能量改变，但作用量近似不变")
        ax2.legend(frameon=False, loc="lower right")
        clean(ax2)
        fig.suptitle("绝热不变量：变化时间尺度远长于振动周期时，相轨道面积保持不变", fontsize=12)
        fig.subplots_adjust(left=0.07, right=0.985, bottom=0.13, top=0.82, wspace=0.28)
        frames.append(frame(fig))
    plt.close(fig)
    save_gif(frames, "adiabatic_invariant.gif", duration=60)


def hamilton_jacobi_wavefront():
    fig, ax = plt.subplots(figsize=(8.0, 4.7), dpi=170)
    ax.set_aspect("equal")
    radii = np.linspace(0.7, 3.2, 6)
    ph = np.linspace(0, 2 * np.pi, 500)
    for i, radius in enumerate(radii):
        ax.plot(radius * np.cos(ph), radius * np.sin(ph), color=BLUE, lw=1.2,
                alpha=0.45 + 0.08 * i)
    angles = np.linspace(0, 2 * np.pi, 12, endpoint=False)
    for angle in angles:
        x0, y0 = 0.42 * np.cos(angle), 0.42 * np.sin(angle)
        x1, y1 = 3.45 * np.cos(angle), 3.45 * np.sin(angle)
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=10,
                                     color=RED, lw=1.1))
    ax.scatter([0], [0], s=50, color=ORANGE, zorder=5)
    ax.text(2.18, 2.36, "$S(\\boldsymbol{q},t)=\\mathrm{const}$\n等作用量面（波前）", color=BLUE,
            ha="center", bbox=dict(fc="white", ec="none", alpha=0.82))
    ax.text(-3.55, 2.9, "$\\boldsymbol{p}=\\nabla S$：经典轨道沿波前法线", color=RED, fontsize=11)
    ax.text(-3.55, 2.55, "$\\psi\\sim e^{iS/\\hbar}$：经典作用量成为量子相位", color=GRAY, fontsize=11)
    ax.set(xlim=(-3.7, 3.7), ylim=(-3.45, 3.45))
    ax.axis("off")
    ax.set_title("哈密顿—雅可比理论与几何光学的对应", fontsize=13)
    fig.tight_layout(pad=0.25)
    fig.savefig(OUT / "hamilton_jacobi_wavefront.png", bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    print("hamilton_jacobi_wavefront.png")


if __name__ == "__main__":
    hamiltonian_flow()
    action_angle_flow()
    liouville_flow()
    legendre_transform()
    adiabatic_invariant()
    hamilton_jacobi_wavefront()
