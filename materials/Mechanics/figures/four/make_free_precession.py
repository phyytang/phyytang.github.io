"""Free precession of nearly symmetric bodies: one formula from the Earth to neutron stars.

Body-frame free-precession period P_fp = P / |eps|, eps = (I3 - I1) / I1.
Run: python3 make_free_precession.py  -> free_precession.png (needs matplotlib, Noto Sans CJK)
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

for f in font_manager.findSystemFonts():
    if "NotoSansCJK-Regular" in f:
        font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": ["Noto Sans CJK SC", "Noto Sans CJK JP"],
                     "mathtext.fontset": "cm", "axes.unicode_minus": False,
                     "font.size": 11, "savefig.dpi": 220})
OUT = os.path.dirname(os.path.abspath(__file__)) + "/"
DAY = 86400.0

fig, ax = plt.subplots(figsize=(7.2, 5.0))
P = np.logspace(-3, 6, 50)
for k in range(1, 11, 1):
    eps = 10.0**(-k)
    ax.loglog(P, P/eps, color="#bbbbbb", lw=0.7, zorder=0)
    x, y = 2e9*eps, 2e9                      # label where the line crosses P_fp = 2e9 s
    if x > 3e5:
        x, y = 3e5, 3e5/eps
    ax.text(x, y, rf"$\epsilon=10^{{-{k}}}$", fontsize=8, color="#888888", rotation=29,
            rotation_mode="anchor", ha="right", va="bottom")

objs = [
    ("地球（刚体预言，欧拉 305 天）", 86164.0, 305*DAY, "#1f4e9c", "o"),
    ("地球（实测钱德勒摆动，约 433 天）", 86164.0, 433*DAY, "#1f4e9c", "s"),
    ("PSR B1828$-$11（约 500 天调制）", 0.405, 500*DAY, "#c8102e", "D"),
    ("磁星 4U 0142+61（约 15 小时调制）", 8.69, 15*3600.0, "#e08a00", "^"),
]
for lab, p, pf, c, m in objs:
    ax.loglog(p, pf, m, color=c, ms=8, mec="k", mew=0.6, label=lab, zorder=3)

ax.set_xlim(1e-3, 1e6); ax.set_ylim(1, 3e10)
ax.set_xlabel(r"自转周期 $P$（秒）")
ax.set_ylabel(r"自由进动（调制）周期 $P_{\rm fp}$（秒）")
for yv, lab in [(3600, "1 小时"), (DAY, "1 天"), (365.25*DAY, "1 年"), (100*365.25*DAY, "100 年")]:
    ax.axhline(yv, color="#dddddd", lw=0.6, ls=":", zorder=0)
    ax.text(1.2e-3, yv*1.15, lab, fontsize=8, color="#777777", ha="left")
ax.legend(loc="lower right", fontsize=8.5, frameon=False)
ax.set_title(r"同一个公式 $P_{\rm fp}=P/|\epsilon|$：从地球到中子星", fontsize=11)
fig.tight_layout()
fig.savefig(OUT + "free_precession.png", bbox_inches="tight", facecolor="white")
for lab, p, pf, c, m in objs:
    print(f"{lab}: eps = {p/pf:.3g}")
