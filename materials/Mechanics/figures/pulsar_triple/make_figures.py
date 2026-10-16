import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Circle, FancyArrowPatch, Ellipse, Rectangle
from scipy.integrate import solve_ivp

for f in font_manager.findSystemFonts():
    if "NotoSansCJK-Regular" in f: font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family":["Noto Sans CJK SC"],"mathtext.fontset":"cm",
    "axes.unicode_minus":False,"font.size":11,"savefig.dpi":220})
OUT=__import__("os").path.dirname(__import__("os").path.abspath(__file__))+"/"
import os; os.makedirs(OUT,exist_ok=True)
BLUE="#1f4e9c"; RED="#c8102e"; ORANGE="#e08a00"; GREEN="#2e7d32"; GRAY="#777777"

# ---------- Fig 1: system schematic ----------
mp,mw,m3=1.16,0.273,0.91; Min=mp+mw; Mt=Min+m3
a2=23.31; e2=0.598; a1=0.0883
E=np.linspace(0,2*np.pi,400)
x=a2*(np.cos(E)-e2); y=a2*np.sqrt(1-e2**2)*np.sin(E)
fig=plt.figure(figsize=(7.4,3.9))
ax=fig.add_axes([0.0,0.0,0.64,1.0])
xin=-m3/Mt*x; yin=-m3/Mt*y; x3=Min/Mt*x; y3=Min/Mt*y
ax.plot(xin,yin,color=BLUE,ls="--",lw=1.2)
ax.plot(x3,y3,color=ORANGE,ls="--",lw=1.2)
k=200
ax.add_patch(Circle((xin[k],yin[k]),0.8,color=BLUE,zorder=5))
ax.add_patch(Circle((x3[k],y3[k]),1.0,color=ORANGE,zorder=5))
ax.plot([xin[k],x3[k]],[yin[k],y3[k]],color=GRAY,lw=0.6,ls=":")
ax.plot(0,0,"k+",ms=9,mew=1.3); ax.text(0,-1.8,"系统质心",fontsize=9,ha="center")
ax.text(x3[k]+2.0,y3[k]-1.0,"第三体\n（类太阳亚巨星）",color=ORANGE,fontsize=9.5,ha="left",va="top")
ax.text(xin[k]-1.8,yin[k]-1.2,"内双星",color=BLUE,fontsize=9.5,ha="right",va="top")
ax.text(-4,-15.5,"外轨道：$P_2\\approx73.5$ 年，$e_2\\approx0.60$，$a_2\\approx23$ AU\n近星点距离 $\\approx9.4$ AU，远星点距离 $\\approx37$ AU",fontsize=9,ha="center")
ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-25,17); ax.set_ylim(-18,13)
ins=fig.add_axes([0.68,0.25,0.30,0.55])
r_p=a1*mw/Min; r_w=a1*mp/Min
th=np.linspace(0,2*np.pi,300)
ins.plot(r_p*np.cos(th),r_p*np.sin(th),color=BLUE,lw=1)
ins.plot(r_w*np.cos(th),r_w*np.sin(th),color=GREEN,lw=1)
ph=2.3
ins.add_patch(Circle((r_p*np.cos(ph),r_p*np.sin(ph)),0.004,color=BLUE,zorder=5))
ins.add_patch(Circle((-r_w*np.cos(ph),-r_w*np.sin(ph)),0.006,color=GREEN,zorder=5))
ins.plot(0,0,"k+",ms=6)
ins.text(-0.035,0.035,"脉冲星",color=BLUE,fontsize=8.5,ha="center")
ins.text(0.03,-0.085,"氦白矮星",color=GREEN,fontsize=8.5,ha="center")
ins.set_aspect("equal"); ins.set_xticks([]); ins.set_yticks([])
ins.set_xlim(-0.1,0.1); ins.set_ylim(-0.1,0.1)
for sp in ins.spines.values(): sp.set_color(BLUE); sp.set_lw(0.8)
ins.set_title("内双星（尺度放大约 250 倍）",fontsize=9,color=BLUE)
ins.text(0,-0.11,"$P_1=8.0$ 天，$a_1\\approx0.09$ AU\n$e_1\\approx1.6\\times10^{-4}$，自转周期 3.2 ms",fontsize=8.5,ha="center",va="top")
fig.savefig(OUT+"triple_schematic.png",bbox_inches="tight",facecolor="white"); plt.close(fig)

# ---------- Fig 2: acceleration along outer orbit ----------
G=6.674e-11; Msun=1.989e30; AU=1.496e11; c=2.998e8
P2=73.5
M_mean=np.linspace(0,2*np.pi,4000)
def kepler(M,e):
    E=M.copy()
    for _ in range(50): E=E-(E-e*np.sin(E)-M)/(1-e*np.cos(E))
    return E
Ek=kepler(M_mean,e2); r=a2*(1-e2*np.cos(Ek))*AU
acc=G*m3*Msun/r**2
t=M_mean/(2*np.pi)*P2
fig,ax=plt.subplots(figsize=(6.6,3.3))
ax.semilogy(t,acc,color=ORANGE,lw=1.8,label="第三体对内双星的引力加速度 $Gm_3/r^2$")
need=c*4.88e-17/3.2e-3
ax.axhline(need,color=RED,ls="--",lw=1.2)
ax.text(40,need*0.62,"解释 $\\dot P_{\\rm obs}$ 所需视向加速度 $c\\dot P/P\\approx4.6\\times10^{-6}\\,{\\rm m\\,s^{-2}}$",color=RED,fontsize=9,ha="center")
t08=73.5-(2036.3-2008.6); t26=73.5-(2036.3-2026.8)
ax.axvspan(t08,t26,color=BLUE,alpha=0.10)
ax.text((t08+t26)/2,1.2e-4,"2008–2026 年观测\n（Fermi + FAST）",color=BLUE,fontsize=8.5,ha="center")
ax.set_xlabel("外轨道时间（年，以近星点为 0）"); ax.set_ylabel("加速度 (m s$^{-2}$)")
ax.set_xlim(0,73.5); ax.set_ylim(2e-6,3e-4)
ax.legend(fontsize=9,frameon=False,loc="upper left")
pass
fig.savefig(OUT+"outer_acceleration.png",bbox_inches="tight",facecolor="white"); plt.close(fig)

# ---------- Fig 3: ZLK phase portraits ----------
def F(e,w,h,eps):
    j=np.sqrt(1-e**2); s2i=1-h**2/j**2
    return 3*s2i*(1-e**2+5*e**2*np.sin(w)**2)-2-3*e**2-8*eps/j
i0=np.radians(85.); h=np.cos(i0)
emax_dom=np.sqrt(1-h**2)
fig,axs=plt.subplots(1,2,figsize=(7.2,3.6))
for ax,eps,title in zip(axs,[0,7.2],["只有牛顿引力（四极近似）","加入广义相对论近星点进动"]):
    ex,ey=np.meshgrid(np.linspace(-1,1,601),np.linspace(-1,1,601))
    e=np.hypot(ex,ey); w=np.arctan2(ey,ex)
    Z=np.where(e<emax_dom*0.9995,F(np.minimum(e,0.999),w,h,eps),np.nan)
    ax.contour(ex,ey,Z,levels=28,colors=BLUE,linewidths=0.7,negative_linestyles="solid")
    # separatrix / level through e=0
    lev=F(np.array(1e-9),np.array(0.),h,eps)
    ax.contour(ex,ey,Z,levels=[float(lev)],colors=RED,linewidths=1.5)
    ax.add_patch(Circle((0,0),emax_dom,fill=False,color=GRAY,lw=0.8))
    ax.plot(0,0,"o",color=RED,ms=4)
    ax.set_aspect("equal"); ax.set_xlim(-1.05,1.05); ax.set_ylim(-1.05,1.05)
    ax.set_xlabel("$e_1\\cos\\omega_1$"); ax.set_title(title,fontsize=10)
axs[0].set_ylabel("$e_1\\sin\\omega_1$")
fig.suptitle("内轨道偏心率矢量的相图（$i_0=85^\\circ$，红线经过圆轨道 $e_1=0$）",fontsize=10.5,y=1.0)
fig.savefig(OUT+"zlk_phase.png",bbox_inches="tight",facecolor="white"); plt.close(fig)

# ---------- Fig 4: secular evolution e(t) ----------
OmK_yr=1/5.20e4   # 1/yr
def rhs(t,y,eps):
    e,w,i=y; j=np.sqrt(1-e**2)
    de=15/8*e*j*np.sin(i)**2*np.sin(2*w)
    dw=0.75*(2*j**2+5*np.sin(w)**2*(e**2-np.sin(i)**2))/j+eps/j**2
    di=-15/16*e**2*np.sin(2*w)*np.sin(2*i)/j
    return [de*OmK_yr,dw*OmK_yr,di*OmK_yr]
T=2.0e6
fig,ax=plt.subplots(figsize=(6.6,3.2))
for inc,eps,col,lab in [(85,0,RED,"$i_0=85^\\circ$，无 GR"),(54,0,ORANGE,"$i_0=54^\\circ$，无 GR"),(85,7.2,BLUE,"$i_0=85^\\circ$，含 GR（$\\varepsilon_{\\rm GR}\\approx7$）"),(54,7.5,GREEN,"$i_0=54^\\circ$，含 GR")]:
    sol=solve_ivp(rhs,[0,T],[1.6e-4,np.radians(45),np.radians(inc)],args=(eps,),rtol=1e-10,atol=1e-13,max_step=2e3,dense_output=True)
    tt=np.linspace(0,T,6000); ee=sol.sol(tt)[0]
    ax.plot(tt/1e6,ee,color=col,lw=1.3 if eps==0 else 2.0,ls="-" if eps==0 else "--",label=lab)
ax.set_xlabel("时间（百万年）"); ax.set_ylabel("内轨道偏心率 $e_1$")
ax.set_yscale("log"); ax.set_ylim(1e-4,1.2); ax.set_xlim(0,T/1e6)
ax.legend(fontsize=8.5,frameon=False,loc="upper center",bbox_to_anchor=(0.5,-0.2),ncol=2)
fig.savefig(OUT+"zlk_evolution.png",bbox_inches="tight",facecolor="white"); plt.close(fig)
print("done")
