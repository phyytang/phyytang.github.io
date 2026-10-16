"""Third-round teaching figures and animations for 刚体运动.md (2026-10).

Static figures
  noncommuting_rotations.png  有限转动不可交换：同一本书，两种转动顺序
  rolling_wheel.png           纯滚动：瞬时转轴通过接触点，各点速度垂直于到接触点的连线
  top_loci.png                重力场中对称陀螺：轴端的波浪形、尖点形、打圈形轨迹
  precession_schematic.png    地球岁差：赤道隆起受到的力矩，以及北天极在恒星间的路径
Animations (frame 0 is an overview frame; a PDF shows only frame 0)
  body_space_cones.gif        自由对称陀螺：本体锥在空间锥上滚动（扁球 / 长球）
  max_axis_rule.gif           能量耗散使转动从最小轴漂移到最大轴（M 守恒，E 减小）
  poinsot_rolling.gif         泊安索构图：惯量椭球在不变平面上滚动，画出 polhode 与 herpolhode

Run:  python3 figures/four/make_third_round_figures.py [name ...]
Needs numpy, scipy, matplotlib, pillow; reuses helpers from make_teaching_animations.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_teaching_animations as mta  # noqa: E402  (fonts, colors, 3-D helpers)

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, Polygon  # noqa: E402
from PIL import Image  # noqa: E402
from scipy.integrate import solve_ivp  # noqa: E402
from scipy.spatial.transform import Rotation  # noqa: E402

OUT = mta.OUT
BLUE, RED, GREEN, ORANGE, GRAY = mta.BLUE, mta.RED, mta.GREEN, mta.ORANGE, mta.GRAY
rot_x, rot_z, qmatrix = mta.rot_x, mta.rot_z, mta.qmatrix


def rot_y(a: float) -> np.ndarray:
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


def savefig(fig, name):
    fig.savefig(OUT / name, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", OUT / name)


def grab(fig) -> Image.Image:
    fig.canvas.draw()
    im = Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[..., :3].copy())
    return im


def save_gif(frames, name, ms=70, hold=3000):
    pal = [f.convert("P", palette=Image.Palette.ADAPTIVE, colors=128) for f in frames]
    dur = [hold] + [ms] * (len(pal) - 1)
    pal[0].save(OUT / name, save_all=True, append_images=pal[1:], duration=dur, loop=0, optimize=True, disposal=1)
    print(f"wrote {OUT / name} ({(OUT / name).stat().st_size / 1024**2:.2f} MiB, {len(pal)} frames)")


# ------------------------------------------------------------------ static 1
def noncommuting_rotations():
    size = np.array([1.5, 1.05, 0.28])  # a "book"
    verts0 = mta.box_vertices(size)
    face_colors = ["#d9d9d9", RED, "#d9d9d9", GREEN, "#d9d9d9", "#5b84c4"]  # -x,+x,-y,+y,-z,+z

    def draw(ax, Q, title):
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
        v = verts0 @ Q.T
        polys = [[v[i] for i in f] for f in mta.FACES]
        ax.add_collection3d(Poly3DCollection(polys, facecolors=face_colors, edgecolors="#24496f", linewidths=0.8, alpha=0.9))
        for i, lab in enumerate(("$X$", "$Y$", "$Z$")):
            e = np.eye(3)[:, i]
            ax.plot([0, 1.25 * e[0]], [0, 1.25 * e[1]], [0, 1.25 * e[2]], color=GRAY, lw=0.9, ls="--")
            ax.text(*(1.38 * e), lab, color=GRAY, fontsize=10)
        mta.finish_3d(ax, 1.25, elev=22, azim=-58)
        ax.set_title(title, fontsize=10.5, pad=-6)

    q90 = np.pi / 2
    rows = [
        [(np.eye(3), "初始"), (rot_x(q90), "① 绕固定 $X$ 轴转 $90^\\circ$"),
         (rot_y(q90) @ rot_x(q90), "② 再绕固定 $Y$ 轴转 $90^\\circ$")],
        [(np.eye(3), "初始"), (rot_y(q90), "① 绕固定 $Y$ 轴转 $90^\\circ$"),
         (rot_x(q90) @ rot_y(q90), "② 再绕固定 $X$ 轴转 $90^\\circ$")],
    ]
    fig = plt.figure(figsize=(10.4, 6.4))
    for r, row in enumerate(rows):
        for c, (Q, t) in enumerate(row):
            ax = fig.add_axes([0.07 + 0.31 * c, 0.47 - 0.45 * r, 0.30, 0.40], projection="3d")
            draw(ax, Q, t)
    fig.text(0.5, 0.965, "有限转动不可交换：同样两次 $90^\\circ$ 转动，顺序不同，书最后的朝向不同",
             ha="center", fontsize=12.5)
    fig.text(0.03, 0.67, "先 $X$ 后 $Y$", ha="center", va="center", rotation=90, fontsize=12, color=BLUE)
    fig.text(0.03, 0.22, "先 $Y$ 后 $X$", ha="center", va="center", rotation=90, fontsize=12, color=BLUE)
    fig.text(0.5, 0.01, "蓝：封面　红：书脊　绿：书顶；转轴都是空间中固定的坐标轴", ha="center", fontsize=10, color="#444444")
    savefig(fig, "noncommuting_rotations.png")


# ------------------------------------------------------------------ static 2
def rolling_wheel():
    R, V = 1.0, 1.0
    xc = 3.3  # current wheel centre
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.axhline(0, color="k", lw=1.2)
    ax.fill_between([-0.3, 7.6], -0.25, 0, color="#eeeeee")
    # Cycloid traced by a rim point
    s = np.linspace(0, 2.35 * np.pi, 400)
    ax.plot(R * s - R * np.sin(s), R - R * np.cos(s), color=ORANGE, lw=1.3, ls="--")
    ax.text(0.25, 1.62, "轮缘上一点的轨迹（摆线）", color=ORANGE, fontsize=10)
    for xg in (1.0, 5.9):
        ax.add_patch(Circle((xg, R), R, fill=False, ec="#bbbbbb", lw=0.8, ls=":"))
    ax.add_patch(Circle((xc, R), R, fill=True, fc="#eef3fb", ec=BLUE, lw=1.6))
    P = np.array([xc, 0.0])
    ax.plot(*P, "o", color=RED, ms=8, zorder=6)
    ax.annotate("接触点 $P$：速度为零\n（瞬时转轴过此点，垂直纸面）", xy=P, xytext=(xc + 1.25, -0.62), fontsize=10, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED, lw=0.9), annotation_clip=False)
    scale = 0.55
    pts = [np.array([xc, R])] + [np.array([xc + R * np.cos(a), R + R * np.sin(a)]) for a in np.deg2rad([90, 45, 0, 135, 180, -45, -135])]
    for p in pts:
        d = p - P
        v = np.array([V * d[1] / R, -V * d[0] / R])
        ax.plot([P[0], p[0]], [P[1], p[1]], color=GRAY, lw=0.7, ls=":")
        ax.add_patch(FancyArrowPatch(p, p + scale * v, arrowstyle="-|>", mutation_scale=12, color=GREEN, lw=1.5))
        ax.plot(*p, "o", color=BLUE, ms=4)
    ax.text(xc + 0.08, R + 0.12, "$C$", fontsize=11)
    ax.text(xc + scale * 2 * V + 0.05, 2 * R + 0.05, "$2V$", color=GREEN, fontsize=11)
    ax.text(xc + scale * V + 0.05, R - 0.22, "$V$", color=GREEN, fontsize=11)
    ax.annotate("", xy=(xc + 0.55, R + 0.62), xytext=(xc - 0.55, R + 0.62),
                arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.2, connectionstyle="arc3,rad=-0.45"))
    ax.text(xc - 0.85, R + 0.5, "$\\Omega$", color=BLUE, fontsize=13)
    ax.text(7.55, 2.45, "纯滚动条件：$v_P=V-\\Omega R=0$\n各点速度 $\\boldsymbol{v}=\\boldsymbol{\\Omega}\\times(\\boldsymbol{r}-\\boldsymbol{r}_P)$：\n垂直于到 $P$ 的连线，大小正比于距离",
            fontsize=10.5, ha="right", va="top")
    ax.set_xlim(-0.3, 7.6); ax.set_ylim(-0.95, 2.6); ax.set_aspect("equal"); ax.axis("off")
    savefig(fig, "rolling_wheel.png")


# ------------------------------------------------------------------ static 3
def top_loci():
    I1, I3, mgl, M3 = 1.0, 0.32, 0.75, 2.2
    th0 = 0.72

    def run(phidot0, T=19.0):
        Mz = I1 * phidot0 * np.sin(th0) ** 2 + M3 * np.cos(th0)

        def rhs(_t, y):
            th, vth, ph = y
            s, c = np.sin(th), np.cos(th)
            N = Mz - M3 * c
            dU = N * M3 / (I1 * s) - N * N * c / (I1 * s ** 3) - mgl * s
            return [vth, -dU / I1, N / (I1 * s * s)]

        t = np.linspace(0, T, 6000)
        y = solve_ivp(rhs, (0, T), [th0, 0.0, 0.0], t_eval=t, rtol=1e-10, atol=1e-12, method="DOP853").y
        return y[0], y[2]

    cases = [(0.18, "(a) 波浪形：$\\dot\\varphi$ 始终同号", BLUE),
             (0.0, "(b) 尖点形：从静止释放，$\\dot\\varphi=0$ 处为尖点", GREEN),
             (-0.45, "(c) 打圈形：$\\dot\\varphi$ 在一个转折点附近反号", RED)]
    fig, axs = plt.subplots(1, 3, figsize=(11.4, 4.2))
    for ax, (pd, title, col) in zip(axs, cases):
        th, ph = run(pd)
        x, y = np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph)
        a = np.linspace(0, 2 * np.pi, 300)
        for tb in (th.min(), th.max()):
            ax.plot(np.sin(tb) * np.cos(a), np.sin(tb) * np.sin(a), color=GRAY, lw=0.7, ls=":")
        ax.plot(x, y, color=col, lw=1.3)
        ax.plot([x[0]], [y[0]], "o", color="k", ms=4)
        ax.plot([0], [0], "+", color="k", ms=8)
        ax.set_aspect("equal"); ax.axis("off")
        lim = np.sin(th.max()) * 1.08
        ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim)
        ax.set_title(title, fontsize=10.5)
    fig.text(0.5, 0.02, "俯视图：对称轴端点在水平面上的投影（虚线圆为两个章动转折角 $\\theta_1,\\theta_2$；“+”为竖直方向，黑点为起点）",
             ha="center", fontsize=9.5, color="#444444")
    savefig(fig, "top_loci.png")


# ------------------------------------------------------------------ static 4
def ecliptic(ra_h, dec_d, eps=np.deg2rad(23.4393)):
    a, d = np.deg2rad(ra_h * 15), np.deg2rad(dec_d)
    sb = np.sin(d) * np.cos(eps) - np.cos(d) * np.sin(eps) * np.sin(a)
    lam = np.arctan2(np.sin(a) * np.cos(eps) + np.tan(d) * np.sin(eps), np.cos(a))
    return lam % (2 * np.pi), np.arcsin(sb)


def precession_schematic():
    fig = plt.figure(figsize=(11.6, 5.2))
    # (a) torque on the equatorial bulge
    ax = fig.add_axes([0.0, 0.05, 0.55, 0.86])
    tilt = np.deg2rad(23.44)
    ax.axhline(0, color=GRAY, lw=0.9, ls="--")
    ax.text(3.35, -0.14, "黄道面", color=GRAY, fontsize=10, ha="right")
    ax.add_patch(Circle((-3.5, 0), 0.45, color="#f2b632"))
    ax.text(-3.5, -0.75, "太阳（很远）", ha="center", fontsize=10)
    for yy in (-0.25, 0, 0.25):
        ax.annotate("", xy=(-2.15, yy), xytext=(-2.85, yy), arrowprops=dict(arrowstyle="-", color="#f2b632", lw=1))
    ax.add_patch(Ellipse((0, 0), 2.4, 1.85, angle=-np.rad2deg(tilt), fc="#dbe7f5", ec=BLUE, lw=1.5))
    eq = np.array([np.cos(tilt), -np.sin(tilt)])
    axis = np.array([np.sin(tilt), np.cos(tilt)])
    ax.plot([-1.55 * eq[0], 1.55 * eq[0]], [-1.55 * eq[1], 1.55 * eq[1]], color=BLUE, lw=0.8, ls=":")
    ax.text(1.62 * eq[0], 1.62 * eq[1] - 0.12, "赤道面", color=BLUE, fontsize=9.5)
    ax.annotate("", xy=2.0 * axis, xytext=(0, 0), arrowprops=dict(arrowstyle="-|>", color="k", lw=2))
    ax.text(*(2.07 * axis), "$\\boldsymbol{M}$（自转轴）", fontsize=11)
    ax.plot([0, 0], [0, 2.7], color=GRAY, lw=1, ls="--")
    ax.text(0.05, 2.75, "黄道法线 $Z$", color=GRAY, fontsize=10)
    near, far = -1.05 * eq, 1.05 * eq
    for p, sgn, lab in ((near, -1, "近侧隆起：受太阳引力较大"), (far, 1, "远侧隆起：受太阳引力较小")):
        ax.plot(*p, "o", color=RED, ms=7)
        ax.annotate("", xy=(p[0] + 0.6 * sgn, p[1]), xytext=p, arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.6))
    ax.text(near[0] - 0.15, near[1] + 0.38, "近侧隆起：\n被多拉向太阳", color=RED, fontsize=9.5, ha="center")
    ax.text(far[0] + 0.2, far[1] - 0.62, "远侧隆起：\n相对地心被推开", color=RED, fontsize=9.5, ha="center")
    ax.plot(0, 0, "o", ms=13, mfc="white", mec="k", mew=1.4)
    ax.plot(0, 0, "o", ms=3.5, color="k")
    ax.text(0.3, 0.12, "力矩 $\\boldsymbol{K}$ 指向\n纸面外 ⊙", fontsize=9.5)
    ax.text(1.55, 1.05, "力矩试图把赤道\n拉向黄道面", fontsize=9.5, color="#444444")
    # precession cone at the tip of M
    tip = 2.0 * axis
    ax.add_patch(Ellipse((0, tip[1]), 2 * tip[0], 0.32, fill=False, ec=GREEN, lw=1.2, ls="--"))
    ax.annotate("", xy=(-0.25, tip[1] - 0.155), xytext=(0.25, tip[1] - 0.155),
                arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=1.4))
    ax.text(-4.0, tip[1] + 0.55, "$d\\boldsymbol{M}=\\boldsymbol{K}\\,dt$ ⊥ $\\boldsymbol{M}$：\n自转轴绕 $Z$ 缓慢进动（向西，周期约 2.6 万年）",
            color=GREEN, fontsize=9.5)
    ax.set_xlim(-4.1, 3.4); ax.set_ylim(-1.45, 3.15); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("(a) 太阳对赤道隆起的力矩（示意，扁率极度夸大）", fontsize=11, loc="left")

    # (b) path of the north celestial pole among the stars
    ax = fig.add_axes([0.60, 0.06, 0.39, 0.84], projection="polar")
    ax.set_theta_zero_location("E"); ax.set_theta_direction(1)
    obl = 23.44
    years = np.linspace(-13000, 13000, 400)
    lam_p = np.deg2rad(90.0 - 50.29 / 3600 * (years - 2000))
    ax.plot(lam_p, np.full_like(lam_p, obl), color=GREEN, lw=1.5)
    for yr, lab in ((2000, "2000"), (-3000, "公元前 3000"), (8000, "8000"), (14000, "约 14000")):
        l = np.deg2rad(90.0 - 50.29 / 3600 * (yr - 2000))
        ax.plot([l], [obl], "o", color=GREEN, ms=4)
        ax.text(l, obl + 7.5, lab, color=GREEN, fontsize=9, ha="center", va="center")
    l1, l2 = np.deg2rad(90.0 - 50.29 / 3600 * 3000), np.deg2rad(90.0 - 50.29 / 3600 * 4500)
    ax.annotate("", xy=(l2, obl), xytext=(l1, obl), arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=1.6))
    stars = [("北极星 Polaris", 2 + 31 / 60 + 49 / 3600, 89.264, -6), ("织女星 Vega", 18 + 36 / 60 + 56 / 3600, 38.784, -6),
             ("右枢 Thuban", 14 + 4 / 60 + 23 / 3600, 64.376, -6.5), ("天津四 Deneb", 20 + 41 / 60 + 26 / 3600, 45.280, -6),
             ("少卫增八 Errai", 23 + 39 / 60 + 21 / 3600, 77.632, 6.5)]
    for name, ra, dec, dr in stars:
        l, b = ecliptic(ra, dec)
        r = 90 - np.rad2deg(b)
        ax.plot([l], [r], "*", color=ORANGE, ms=11, mec="k", mew=0.4)
        ax.text(l, r + dr, name, fontsize=8.5, ha="center", va="center")
    ax.plot([0], [0], "+", color="k", ms=10)
    ax.set_rmax(48); ax.set_rticks([10, 20, 30, 40]); ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.grid(color="#dddddd", lw=0.6)
    ax.set_title("(b) 北天极在恒星间的路径（中心为黄极）", fontsize=11, pad=12)
    savefig(fig, "precession_schematic.png")


# ------------------------------------------------------------------ animation 1
def cone_lines(axis, half, L, e_ref, n=18):
    axis = axis / np.linalg.norm(axis)
    u = e_ref - axis * (e_ref @ axis); u /= np.linalg.norm(u)
    w = np.cross(axis, u)
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    gens = [L * (np.cos(half) * axis + np.sin(half) * (np.cos(t) * u + np.sin(t) * w)) for t in a]
    aa = np.linspace(0, 2 * np.pi, 120)
    rim = L * (np.cos(half) * axis[:, None] + np.sin(half) * (np.outer(u, np.cos(aa)) + np.outer(w, np.sin(aa))))
    return gens, rim


def body_space_cones():
    cases = [dict(r=2.0, th=np.deg2rad(20), title="扁球 $I_3>I_1$（如地球）：空间锥在本体锥之内", L=1.5),
             dict(r=0.4, th=np.deg2rad(40), title="长球 $I_3<I_1$（如被磁场拉长的磁星）：两锥外切", L=1.5)]
    I1, M = 1.0, 1.0
    for c in cases:
        I3 = c["r"] * I1
        c["phid"] = M / I1
        Om3 = M * np.cos(c["th"]) / I3
        c["psid"] = -(I3 - I1) / I1 * Om3
    nfr = 64
    T = 2 * np.pi
    times = np.linspace(0, T, nfr, endpoint=False)

    def state(c, t):
        Q = rot_z(c["phid"] * t) @ rot_x(c["th"]) @ rot_z(c["psid"] * t)
        e3 = Q[:, 2]
        Om = c["phid"] * np.array([0, 0, 1.0]) + c["psid"] * e3
        return Q, e3, Om

    def render(t, overview=False):
        fig = plt.figure(figsize=(10.4, 5.0), dpi=95)
        for k, c in enumerate(cases):
            ax = fig.add_axes([0.0 + 0.5 * k, 0.11, 0.5, 0.80], projection="3d")
            Q, e3, Om = state(c, t)
            Oh = Om / np.linalg.norm(Om)
            beta = np.arccos(Oh[2]); alpha = np.arccos(Oh @ e3)
            L = c["L"]
            g, rim = cone_lines(np.array([0, 0, 1.0]), beta, L, Oh)
            for v in g:
                ax.plot([0, v[0]], [0, v[1]], [0, v[2]], color=ORANGE, lw=0.6, alpha=0.6)
            ax.plot(*rim, color=ORANGE, lw=1.4)
            g, rim = cone_lines(e3, alpha, L, Q[:, 0])
            for i, v in enumerate(g):
                ax.plot([0, v[0]], [0, v[1]], [0, v[2]], color=BLUE if i else "#0b2a5c", lw=0.6 if i else 2.2, alpha=0.55 if i else 1)
            ax.plot(*rim, color=BLUE, lw=1.4)
            # traces of the tips of e3 and Omega (fixed circles in space)
            tt = np.linspace(0, T, 200)
            E3 = np.array([state(c, s)[1] for s in tt]) * 1.75
            ax.plot(E3[:, 0], E3[:, 1], E3[:, 2], color=GREEN, lw=0.8, ls=":")
            ax.quiver(0, 0, 0, 0, 0, 1.95, color="k", lw=2.2, arrow_length_ratio=0.08)
            ax.text(0.05, 0.05, 2.02, "$\\boldsymbol{M}$", fontsize=12)
            ax.quiver(0, 0, 0, *(1.75 * e3), color=GREEN, lw=2.2, arrow_length_ratio=0.09)
            ax.text(*(1.88 * e3), "$x_3$", color=GREEN, fontsize=12)
            ax.quiver(0, 0, 0, *(1.85 * Oh), color=RED, lw=2.4, arrow_length_ratio=0.09)
            ax.text(*(1.98 * Oh), "$\\boldsymbol{\\Omega}$", color=RED, fontsize=12)
            ax.set_xlim(-1.0, 1.0); ax.set_ylim(-1.0, 1.0); ax.set_zlim(0.0, 2.0)
            ax.set_box_aspect((1, 1, 1), zoom=1.35)
            ax.view_init(elev=14, azim=-60); ax.set_axis_off()
            fig.text(0.25 + 0.5 * k, 0.92, c["title"], ha="center", fontsize=11)
        msg = ("橙：空间锥（固定在惯性系，轴为 $\\boldsymbol{M}$）　蓝：本体锥（固定在刚体上，轴为对称轴 $x_3$，深蓝线随刚体转动）\n"
               "两锥沿瞬时角速度 $\\boldsymbol{\\Omega}$（红）相切，本体锥在空间锥上无滑动地滚动；$\\boldsymbol{M}$、$\\boldsymbol{\\Omega}$、$x_3$ 始终共面")
        fig.text(0.5, 0.02, msg, ha="center", fontsize=9.5, color="#333333")
        return grab_close(fig)

    frames = [render(0.0, True)] + [render(t) for t in times]
    save_gif(frames, "body_space_cones.gif", ms=70, hold=3000)


def grab_close(fig):
    im = grab(fig)
    plt.close(fig)
    return im


# ------------------------------------------------------------------ animation 2
def view_vector(elev, azim):
    e, a = np.deg2rad(elev), np.deg2rad(azim)
    return np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])


def plot_depth(ax, P, vv, color, lw=1.2, back_alpha=0.18, **kw):
    """Plot a 3-D polyline on the unit sphere, fading the part on the far side."""
    front = P @ vv >= 0
    A = P.copy(); A[~front] = np.nan
    B = P.copy(); B[front] = np.nan
    ax.plot(A[:, 0], A[:, 1], A[:, 2], color=color, lw=lw, **kw)
    ax.plot(B[:, 0], B[:, 1], B[:, 2], color=color, lw=lw * 0.8, alpha=back_alpha, **kw)


def max_axis_rule():
    I = np.array([1.0, 2.0, 3.0]); gam = 0.035
    def rhs(_t, Mv):
        Om = Mv / I
        Mh = Mv / np.linalg.norm(Mv)
        D = -gam * (Om - (Om @ Mh) * Mh)
        return np.cross(Mv, Om) + D
    a = 0.12
    M0 = np.array([np.cos(a), np.sin(a) * 0.6, np.sin(a) * 0.8])
    T = 330.0
    t = np.linspace(0, T, 12000)
    Mt = solve_ivp(rhs, (0, T), M0, t_eval=t, rtol=1e-10, atol=1e-12, method="DOP853").y.T
    n = Mt / np.linalg.norm(Mt, axis=1)[:, None]
    E = 0.5 * np.sum(n ** 2 / I, axis=1)
    print("max_axis: |M| drift", np.ptp(np.linalg.norm(Mt, axis=1)), "E end", E[-1])
    # energy contours on the sphere via a lat-lon grid
    th = np.linspace(0, np.pi, 181); ph = np.linspace(-np.pi, np.pi, 361)
    TH, PH = np.meshgrid(th, ph, indexing="ij")
    X, Y, Z = np.sin(TH) * np.cos(PH), np.sin(TH) * np.sin(PH), np.cos(TH)
    EG = 0.5 * (X ** 2 / I[0] + Y ** 2 / I[1] + Z ** 2 / I[2])
    tmp = plt.figure(); cs = plt.contour(PH, TH, EG, levels=[0.18, 0.21, 0.29, 0.36, 0.43]); seg_levels = cs.allsegs; plt.close(tmp)
    tmp = plt.figure(); cs2 = plt.contour(PH, TH, EG, levels=[0.5 / I[1]]); sep = cs2.allsegs[0]; plt.close(tmp)

    def to3(seg):
        p, q = seg[:, 0], seg[:, 1]
        return np.c_[np.sin(q) * np.cos(p), np.sin(q) * np.sin(p), np.cos(q)]

    elev, azim = 22, 35
    vv = view_vector(elev, azim)
    idx = np.unique(np.r_[np.linspace(0, len(t) - 1, 150).astype(int)])

    def render(j, overview=False):
        fig = plt.figure(figsize=(10.2, 4.8), dpi=95)
        ax = fig.add_axes([0.0, 0.02, 0.5, 0.9], projection="3d")
        u = np.linspace(0, 2 * np.pi, 40); v = np.linspace(0, np.pi, 20)
        ax.plot_surface(np.outer(np.cos(u), np.sin(v)), np.outer(np.sin(u), np.sin(v)), np.outer(np.ones_like(u), np.cos(v)),
                        color="#f2f4f8", alpha=0.25, linewidth=0, shade=False)
        for lev in seg_levels:
            for sg in lev:
                plot_depth(ax, to3(sg), vv, "#c3cad4", lw=0.6, back_alpha=0.08)
        for sg in sep:
            plot_depth(ax, to3(sg), vv, RED, lw=1.4)
        plot_depth(ax, n[: j + 1], vv, ORANGE, lw=1.1, back_alpha=0.25)
        ax.scatter(*n[j], color="k", s=30, depthshade=False, zorder=10)
        for k, (lab, col) in enumerate(((r"$\pm x_1$ 能量最高", BLUE), (r"$\pm x_2$ 鞍点", RED), (r"$\pm x_3$ 能量最低", GREEN))):
            e = np.eye(3)[k]
            ax.scatter(*e, color=col, s=30, marker="^" if k != 1 else "x", depthshade=False)
            ax.text(*(1.22 * e), lab, color=col, fontsize=9.5, zorder=11)
        mta.finish_3d(ax, 1.05, elev=elev, azim=azim)
        fig.text(0.25, 0.94, "角动量方向 $\\boldsymbol{n}=\\boldsymbol{M}/M$ 在刚体系中的轨迹（橙）", ha="center", fontsize=11)
        fig.text(0.25, 0.03, "灰线：等能线　红线：经过鞍点 $\\pm x_2$ 的分离线", ha="center", fontsize=9.5, color="#444444")
        a2 = fig.add_axes([0.58, 0.18, 0.39, 0.66])
        a2.plot(t, E / 0.5, color=ORANGE, lw=0.6, alpha=0.3 if not overview else 1.0)
        if not overview:
            a2.plot(t[: j + 1], E[: j + 1] / 0.5, color=ORANGE, lw=1.1)
        for val, lab, col in ((1 / I[0], "绕 $x_1$（最小轴）", BLUE), (1 / I[1], "分离线（中间轴）", RED), (1 / I[2], "绕 $x_3$（最大轴）", GREEN)):
            a2.axhline(val, color=col, ls="--", lw=1)
            a2.text(T * 0.99, val + 0.015, lab, color=col, fontsize=9.5, ha="right", va="bottom")
        a2.set_xlim(0, T); a2.set_ylim(0.28, 1.08)
        a2.set_xlabel("时间 $t$"); a2.set_ylabel("转动能 $E/(M^2/2)$")
        for sp in ("top", "right"):
            a2.spines[sp].set_visible(False)
        a2.set_title("$M$ 守恒、$E$ 缓慢减小：从最小轴“下坡”到最大轴", fontsize=10.5, loc="left")
        return grab_close(fig)

    frames = [render(len(t) - 1, True)] + [render(j) for j in idx]
    save_gif(frames, "max_axis_rule.gif", ms=70, hold=3000)


# ------------------------------------------------------------------ animation 3
def poinsot_rolling():
    I = np.array([1.0, 2.0, 3.0])
    w0 = np.array([1.2, 0.0, 1.0])  # polhode around x3 (largest I): the ellipsoid rolls on its flattest side
    T = 30.0
    times = np.linspace(0, T, 1500)
    omega, quats = mta.integrate_free_body(I, w0, times)   # M along +Z
    flip = rot_x(np.pi)                                       # put M along -Z: ellipsoid rests on a plane below
    Qs = np.array([flip @ qmatrix(q) for q in quats])
    E2 = np.sum(I * w0 ** 2); Mmag = np.linalg.norm(I * w0)
    xiP = omega / np.sqrt(E2)                                 # contact point in body coordinates
    rP = np.einsum("tij,tj->ti", Qs, xiP)                      # in space
    d = np.sqrt(E2) / Mmag
    print("poinsot: plane height spread", np.ptp(rP[:, 2]), "expected", -d)
    ax_s = 1 / np.sqrt(I)
    u = np.linspace(0, 2 * np.pi, 28); v = np.linspace(0, np.pi, 14)
    body_pts = np.stack([ax_s[0] * np.outer(np.cos(u), np.sin(v)), ax_s[1] * np.outer(np.sin(u), np.sin(v)),
                         ax_s[2] * np.outer(np.ones_like(u), np.cos(v))], axis=-1)
    idx = np.linspace(0, len(times) - 1, 110).astype(int)
    lim = 1.1

    def render(j, overview=False):
        Q = Qs[j]
        fig = plt.figure(figsize=(6.4, 5.4), dpi=88)
        ax = fig.add_axes([0, 0.06, 1, 0.86], projection="3d")
        pl = np.array([[-lim, -lim], [lim, -lim], [lim, lim], [-lim, lim]])
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
        ax.add_collection3d(Poly3DCollection([[(x, y, -d) for x, y in pl]], facecolors="#f3ead9", edgecolors="#c9b48a", alpha=0.35))
        P = body_pts @ Q.T
        ax.plot_surface(P[..., 0], P[..., 1], P[..., 2], color="#89a9d6", alpha=0.35, linewidth=0.3, edgecolor="#4c6f9c", shade=True)
        pol = xiP @ Q.T
        ax.plot(pol[:, 0], pol[:, 1], pol[:, 2], color=RED, lw=1.6)
        ax.plot(rP[: j + 1, 0], rP[: j + 1, 1], rP[: j + 1, 2], color=ORANGE, lw=1.6, zorder=8)
        ax.scatter(*rP[j], color="k", s=22, depthshade=False)
        ax.plot([0, rP[j, 0]], [0, rP[j, 1]], [0, rP[j, 2]], color=RED, lw=1.0, ls="--")
        ax.quiver(0, 0, 0, 0, 0, -0.95 * d, color="k", lw=1.6, arrow_length_ratio=0.15)
        ax.text(-0.9, 0.9, 0.55, "$\\boldsymbol{M}$ 竖直向下，不变平面水平", fontsize=9)
        mta.finish_3d(ax, 0.95, elev=24, azim=-55)
        fig.text(0.5, 0.95, "惯量椭球在不变平面上无滑动地滚动", ha="center", fontsize=11.5)
        fig.text(0.5, 0.02, "红：polhode（画在椭球上，随刚体转动）　橙：herpolhode（画在固定平面上）\n红色虚线：瞬时角速度方向（指向接触点）",
                 ha="center", fontsize=9, color="#333333")
        return grab_close(fig)

    frames = [render(len(times) - 1, True)] + [render(j) for j in idx]
    save_gif(frames, "poinsot_rolling.gif", ms=70, hold=3000)


ALL = {f.__name__: f for f in (noncommuting_rotations, rolling_wheel, top_loci, precession_schematic,
                               body_space_cones, max_axis_rule, poinsot_rolling)}
if __name__ == "__main__":
    for name in sys.argv[1:] or ALL:
        ALL[name]()
