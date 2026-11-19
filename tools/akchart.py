import json,datetime as dt
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.dates as md
from matplotlib.lines import Line2D
E=json.load(open('engine_out.json'))
P=lambda s: dt.datetime.fromisoformat(s)
H=dt.timedelta(hours=1)
COL={'Elimbari':'#2f6db5','Diamond':'#2a9d8f'}
A,K=0,2.5
fig,ax=plt.subplots(figsize=(13,4.8),dpi=200)
t0,t1=dt.datetime(2026,11,18),dt.datetime(2027,1,13)
d=t0
while d<t1:
    if d.weekday()>=5: ax.axvspan(d,d+dt.timedelta(days=1),color='#f2f2f2',zorder=0)
    d+=dt.timedelta(days=1)
rows=sorted(E['river'],key=lambda r:(r[0],r[5]))
last={}
for r in rows:
    v,at,frm,ls,dep,k,cfo,ret=r[0],r[1],r[2],P(r[3]),P(r[4]),P(r[5]),r[6],P(r[7])
    c=COL[v]
    if at=='POM':
        mid=dep+(k-dep)*(4/6.5); ax.plot([mid,k],[A,K],color=c,lw=2)
        if k>=t0: ax.annotate(f"{cfo/1e3:.0f}k (from POM)",(k,K),xytext=(0,19),textcoords='offset points',ha='center',fontsize=7,color=c,fontweight='bold')
    else:
        if v in last and last[v] and last[v]<ls: ax.plot([last[v],ls],[A,A],color=c,lw=3,alpha=.35,solid_capstyle='butt')
        ax.plot([ls,dep],[A,A],color=c,lw=5,alpha=.6,solid_capstyle='butt')
        ax.plot([dep,k],[A,K],color=c,lw=2)
        if k>=t0: ax.annotate(f"{cfo/1e3:.0f}k",(k,K),xytext=(0,6),textcoords='offset points',ha='center',fontsize=7,color=c)
    dk=k+12*H
    ax.plot([k,dk],[K,K],color=c,lw=5,alpha=.6,solid_capstyle='butt')
    if 'back to POM' in frm:
        ax.plot([dk,dk+60*H],[K,A],color=c,lw=1.5,ls=(0,(4,3)))
        ax.annotate('to POM',(dk+60*H,A),xytext=(2,-11),textcoords='offset points',fontsize=7,color=c); last[v]=None
    else:
        ax.plot([dk,ret],[K,A],color=c,lw=1.5,ls=(0,(4,3))); last[v]=ret
ax.set_xlim(t0,t1); ax.set_ylim(-0.35,3.15)
ax.set_yticks([A,K]); ax.set_yticklabels(['Aiambak','Kiunga'],fontsize=10,fontweight='bold')
ax.xaxis.set_major_locator(md.WeekdayLocator(byweekday=md.WE)); ax.xaxis.set_major_formatter(md.DateFormatter('%a %d %b'))
ax.xaxis.set_minor_locator(md.DayLocator()); ax.tick_params(axis='x',labelsize=8)
for s in ['top','right','left']: ax.spines[s].set_visible(False)
ax.grid(axis='x',which='major',color='#dddddd',lw=.8)
for y in (A,K): ax.axhline(y,color='#bbbbbb',lw=1,zorder=0)
h=[Line2D([],[],color=COL['Elimbari'],lw=2,label='Elimbari'),Line2D([],[],color=COL['Diamond'],lw=2,label='Diamond'),
   Line2D([],[],color='#555',lw=2,label='Laden'),Line2D([],[],color='#555',lw=1.5,ls=(0,(4,3)),label='Empty'),Line2D([],[],color='#555',lw=5,alpha=.5,label='Loading / discharging / waiting')]
ax.legend(handles=h,loc='upper center',bbox_to_anchor=(.5,-.13),ncol=5,frameon=False,fontsize=8)
ax.set_title('Aiambak – Kiunga river runs, 18 Nov 2026 – 13 Jan 2027 (litres delivered to Kiunga labelled)',fontsize=10,loc='left',color='#333')
plt.tight_layout(); plt.savefig('ak_motion_8wk.png')
