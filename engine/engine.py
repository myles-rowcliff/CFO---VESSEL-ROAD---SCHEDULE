import json, datetime as dt, math
D=dt.datetime; H=dt.timedelta(hours=1); days=lambda x: dt.timedelta(days=x)
import os
P=json.load(open(os.environ.get('PFILE','params.json')))
def T(s): return D.fromisoformat(s) if s else None
START=T(P['start']); NOW=T(P['now']); END=START+days(7*P['weeks'])
TO,TB,LP,DA=P['t_out'],P['t_back'],P['load_pom'],P['dis_aia']
TAK,TKA,LA,DK=P['t_ak'],P['t_ka'],P['load_aia'],P['dis_k']
CAP=P['amigo_cap']; RATE=P['truck_rate']; HRS=P['truck_hours']; RESTART=T(P['trucks_restart'])
USE=P['site_use']; BUF=P['buffer_days']; W=P['window']
WS=P['wonder']
# ---------- vessels
fly=[]; FLYK=[]
for v in P['fly']:
    f=dict(name=v['name'],cap=v['cap'],cargo=0,phase=None,t=None,voy=0,rec=None,recs=[],busy=NOW,hold=v.get('hold',0),da=v.get('dis_aia',DA),dfrom=T(v.get('dis_from')),amigo_only=v.get('amigo_only',[]))  # amigo_only: voyage numbers whose CFO all goes into Amigo 1 (not to river vessels)  # dis_from: alongside at Aiambak but not discharging before this time
    ev,d=v['event'],T(v['date'])
    # 'Standby at Aiambak' = alongside at Aiambak, treated as discharging there until a decision is entered
    if ev in('ETA Aiambak','Standby at Aiambak'): f.update(phase='to_aia',t=d,cargo=v['now'] or v['cap'],dep=d-days(TO),ls=d-days(TO+LP))
    elif ev=='Departed Aiambak': f.update(phase='to_pom',t=d+days(TB),cargo=0)
    elif ev=='Loading at POM': f.update(phase='load_pom',t=d+days(LP),cargo=v['now'] or v['cap'],ls=d)
    elif ev=='Departed POM': f.update(phase='to_aia',t=d+days(TO),cargo=v['now'] or v['cap'],dep=d,ls=d-days(LP))
    elif ev=='Passed Aiambak to Kiunga':
        # Fly vessel sails on past Aiambak and discharges its own cargo at Kiunga, then returns empty to POM
        # optional per-vessel: t_ak / t_ka sailing days, depart_aia=True when 'date' is the departure from Aiambak, since = time it arrived at Aiambak
        k=d+days(v.get('t_ak',TAK)); c=v['now'] or v['cap']; dk=v.get('dis_k',DK); ret=k+days(dk+v.get('t_ka',TKA)+TB)
        f.update(phase='to_pom',t=ret,cargo=0)
        if v.get('depart_aia'):
            FLYK.append(dict(Vessel=v['name'],at='Aiambak',frm='Own cargo – direct to Kiunga, then back to POM',ls=T(v['since']) if v.get('since') else d,dep=d,k=k,cfo=c,ret=ret,dk=dk))
        else:
            FLYK.append(dict(Vessel=v['name'],at='POM',frm='Own cargo – direct to Kiunga past Aiambak',ls=d-days(TO+LP),dep=d-days(TO),k=k,cfo=c,ret=ret,dk=dk))
    fly.append(f)
riv=[]; rrecs=[]
for v in P['river']:
    r=dict(name=v['name'],cap=v['cap'],phase=None,t=None,cargo=0,rec=None,combo=v.get('pom_cycle',False),pom_once=T(v.get('pom_once')))  # pom_once: first time it is back at Aiambak empty before this time, it sails to POM, loads there and goes straight to Kiunga
    ev,d=v['event'],T(v['date'])
    if ev=='ETA Kiunga':
        r.update(phase='to_k',t=d,cargo=v['cap']); r['rec']=dict(Vessel=r['name'],at='Aiambak',frm='Before schedule start',ls=d-days(TAK+LA),dep=d-days(TAK),k=d,cfo=v['cap'])
    elif ev=='Loading at POM':
        dep=d+days(LP); k=dep+days(TO+TAK)
        r.update(phase='to_k',t=k,cargo=v['cap']); r['rec']=dict(Vessel=r['name'],at='POM',frm='Johnny Traveller',ls=d,dep=dep,k=k,cfo=v['cap'])
    riv.append(r)
shs=[]
for _ws in ([dict(P['wonder'],name='Wonderland')] if P['wonder'].get('start') else [])+P.get('shuttles',[]):
    shs.append(dict(name=_ws['name'],ws=_ws,cap=_ws['cap'],phase='load_pom',t=T(_ws['start'])+days(_ws['freight_pom']+_ws['cfo']/2),ls=T(_ws['start']),cargo=_ws['cap'],voy=0,recs=[]))
ros=[]
for _r in P.get('roster',[]):
    ros.append(dict(name=_r['name'],sp=_r,cap=_r['cap'],trip=_r['first'],phase='load_pom',ls=T(_r['start']),t=T(_r['first_depart']),cargo=_r['cap'],voy=0,recs=[],krecs=[]))
def ros_pomtime(v):
    if 'load_pom' in v['sp']: return v['sp']['load_pom']+v['sp'].get('freight_pom',0)
    return 0.5 if v['trip']=='A' else 0.25+v['sp'].get('freight_pom',0)
amigo=P['amigo_open']; site=P['site_open']-(USE*((NOW-T(P['site_measured'])).total_seconds()/86400) if P.get('site_measured') else 0); truck_q=[]; dis_q=[]  # (arrive_time, litres)
hourly=[]; emerg=[]
for x in FLYK:
    if x['k']>=NOW: n=max(1,round(x['dk']*24)); dis_q.append([x['k'],n,x['cfo']/n])
def trucks_on(t): return RESTART is None or t>=RESTART
STEPS=[(T(a),n) for a,n in P.get('truck_steps',[])]
TSIZE=P.get('truck_size',40000); CH=P.get('convoy_hour',6)
PRE=[(T(a),l) for a,l in P.get('preloaded',[])]
EXTRA=[(T(a),l,fa) for a,l,fa in P.get('extra_loads',[])]
PREFILL=[(T(a),l) for a,l in P.get('prefill',[])]; CREDIT=0  # trucks filled from Amigo 1 ahead of their convoy: [time, litres]
def ntrucks(t):
    n=round(RATE/TSIZE)
    for a,v in STEPS:
        if t>=a: n=v
    return n
TRUCKS=[]; TRUCKLOG=[]; TRUCKMODE=P.get('truck_mode',False); PEND={}; LASTDEP={}; CONVLOG=[]; HOLD=P.get('hold_convoys',False); TURN=P.get('truck_turnaround_h',16)
CONV=P.get('convoys',[])  # [[hour, trucks], ...] used when the day's truck count equals their total
def convoys(t):
    n=ntrucks(t)
    if CONV and sum(k for h,k in CONV)==n: return [(h,k) for h,k in CONV]
    return [(CH,n)]
def rate(t):
    return ntrucks(t)*TSIZE if trucks_on(t) else 0
t=NOW
while t<END+days(4):
    # --- phase transitions
    for f in fly:
        while f['t'] is not None and f['t']<=t and f['phase']!='at_aia':
            if f['phase']=='load_pom': f['phase']='to_aia'; f['dep']=f['t']; f['t']=f['t']+days(TO)
            elif f['phase']=='to_aia':
                f['phase']='at_aia'; f['voy']+=1
                f['rec']=dict(Vessel=f['name'],n=f['voy'],ls=f['ls'],dep=f['dep'],eta=f['t'],cfo=f['cargo'],to={},amigo=0,ks=[])
                f['arr']=f['t']; f['t']=None
            elif f['phase']=='to_pom':
                h=0 if f.get('held') else f.get('hold',0); f['held']=True
                f['phase']='load_pom'; f['ls']=f['t']+days(h); f['cargo']=f['cap']; f['t']=f['t']+days(h+LP)
    for r in riv:
        if r['t'] is not None and r['t']<=t:
            if r['phase']=='to_k':
                rec=r['rec']; rec['ret']=r['t']+days(DK+TKA); rrecs.append(rec)
                if r['t']>=NOW: dis_q.append([r['t'],max(1,round(DK*24)),r['cargo']/max(1,round(DK*24))])
                if r['combo'] and rec['at']=='Aiambak':
                    # POM cycle: after its Aiambak–Kiunga run the vessel goes back down to POM to load for a direct trip
                    rec['ret']=r['t']+days(DK+TKA+TB); rec['frm']=rec['frm']+' – then back to POM'
                    r['phase']='to_pom_r'; r['t']=rec['ret']; r['cargo']=0
                else:
                    r['phase']='to_aia'; r['t']=r['t']+days(DK+TKA); r['cargo']=0
            elif r['phase']=='to_pom_r':
                ls=r['t']; dep=ls+days(LP); k=dep+days(TO+TAK)
                r['phase']='to_k'; r['t']=k; r['cargo']=r['cap']
                r['rec']=dict(Vessel=r['name'],at='POM',frm='Johnny Traveller',ls=ls,dep=dep,k=k,cfo=r['cap'])
            elif r['phase']=='to_aia' and r['pom_once'] and t<=r['pom_once']:
                r['pom_once']=None; ls=t+days(TB); dep=ls+days(LP); k=dep+days(TO+TAK)
                r['phase']='to_k'; r['t']=k; r['cargo']=r['cap']; r['rec']=dict(Vessel=r['name'],at='POM',frm='Loaded at POM (one-off trip from Aiambak)',ls=ls,dep=dep,k=k,cfo=r['cap'])
            elif r['phase']=='to_aia': r['phase']='waiting'; r['t']=None; r['since']=t
            elif r['phase']=='loading':
                r['phase']='to_k'; r['rec']['dep']=r['t']; r['rec']['k']=r['t']+days(TAK); r['t']=r['t']+days(TAK)
    for won in shs:
        WS=won['ws']
        if won and won['t'] is not None and won['t']<=t:
            if won['phase']=='load_pom': won['phase']='to_aia'; won['dep']=won['t']; won['t']=won['t']+days(WS['t_out'])
            elif won['phase']=='to_aia':
                won['phase']='at_aia'; won['voy']+=1; won['rec']=dict(Vessel=won['name'],n=won['voy'],ls=won['ls'],dep=won['dep'],eta=won['t'],cfo=WS['cap'],to={},amigo=0,ks=[]); won['t']=None; won['arr']=t
            elif won['phase']=='freight': won['phase']='to_pom'; won['t']=won['t']+days(WS['t_back'])
            elif won['phase']=='to_pom': won['phase']='load_pom'; won['ls']=won['t']; won['cargo']=WS['cap']; won['t']=won['t']+days(WS['freight_pom']+WS['cfo']/2)  # cfo = CFO hours at both ends combined (half at POM, half at Aiambak)
        # --- Wonderland discharge into Amigo (priority for room)
        if won and won['phase']=='at_aia':
            mv=min(won['cargo'],CAP-amigo)
            if mv>0: amigo+=mv; won['cargo']-=mv; won['rec']['amigo']+=mv
            if won['cargo']<=0 and t>=won['arr']+days(WS['cfo']/2):
                won['rec']['depA']=t+days(WS['freight_aia']); won['rec']['etaP']=won['rec']['depA']+days(WS['t_back']); won['recs'].append(won['rec'])
                won['phase']='freight'; won['t']=t+days(WS['freight_aia'])
    for v in ros:
        sp=v['sp']
        while v['t'] is not None and v['t']<=t:
            if v['phase']=='load_pom':
                v['dep']=v['t']; v['voy']+=1
                if v['trip']=='A': v['phase']='to_k'; v['t']=v['t']+days(sp['t_pa']+sp['t_ak'])
                else: v['phase']='to_aia'; v['t']=v['t']+days(sp['t_pa'])
            elif v['phase']=='to_k':
                dis_q.append([v['t'],12,v['cargo']/12]); v['krecs'].append(dict(Vessel=v['name'],at='POM',frm='Johnny Traveller (direct)',ls=v['ls'],dep=v['dep'],k=v['t'],cfo=v['cargo'],ret=v['t']+days(0.5+sp['t_pa']+sp['t_ak'])))
                v['cargo']=0; v['phase']='to_pom'; v['t']=v['t']+days(0.5+sp['t_pa']+sp['t_ak'])
            elif v['phase']=='to_aia':
                v['phase']='at_aia'; v['arr']=v['t']; v['rec']=dict(Vessel=v['name'],n=v['voy'],ls=v['ls'],dep=v['dep'],eta=v['t'],cfo=v['cargo'],to={},amigo=0,ks=[]); v['t']=None
            elif v['phase']=='freight': v['phase']='to_pom'; v['t']=v['t']+days(sp['t_pa'])
            elif v['phase']=='to_pom':
                mode=sp.get('mode','alt')
                if mode=='alt': v['trip']='B' if v['trip']=='A' else 'A'
                elif mode=='A' or mode=='B': v['trip']=mode
                else:
                    eta=v['t']+days(ros_pomtime(dict(v,trip='B'))+sp['t_pa'])
                    held=sum(f['cargo'] for f in fly if f['phase']=='at_aia')
                    inc=sum(f['cargo'] for f in fly if f['phase'] in('to_aia','load_pom') and f['t'] and f['t']<=eta and f['phase']=='to_aia')+sum(f['cap'] for f in fly if f['phase']=='load_pom' and f['t']+days(TO)<=eta)
                    inc+=sum(w['cargo'] for w in shs if w['phase'] in('to_aia','at_aia') and (w['t'] is None or w['t']<=eta))
                    dd=(eta-t).total_seconds()/86400
                    trout=rate(t)*dd; rivtake=sum(r['cap'] for r in riv)*dd/(TAK+TKA+LA+DK)
                    proj=amigo+held+inc-trout-rivtake
                    v['trip']='A' if (held>0 or proj+v['cap']>CAP*sp.get('room',1.0)) else 'B'
                v.setdefault('log',[]).append((t,v['trip']))
                v['phase']='load_pom'; v['ls']=v['t']; v['cargo']=v['cap']; v['t']=v['t']+days(ros_pomtime(v))
        if v['phase']=='at_aia':
            mv=min(v['cargo'],CAP-amigo)
            if mv>0: amigo+=mv; v['cargo']-=mv; v['rec']['amigo']+=mv
            if v['cargo']<=0 and t>=v['arr']+days(sp.get('dis_aia',0.25)):
                fa=sp.get('freight_aia',0); v['rec']['depA']=t+days(fa); v['rec']['etaP']=v['rec']['depA']+days(sp['t_pa']); v['recs'].append(v['rec'])
                v['phase']='freight'; v['t']=t+days(fa)
    # --- Fly allocation
    here=[f for f in fly if f['phase']=='at_aia' and not (f['dfrom'] and t<f['dfrom'])]
    waiting=sorted([r for r in riv if r['phase']=='waiting'],key=lambda r:r['since'])
    # 1. Amigo first if low
    for f in sorted(here,key=lambda f:f['arr']):
        if amigo<P['amigo_low'] and f['cargo']>0:
            mv=min(f['cargo'],max(0,min(CAP,P['amigo_target'])-amigo))
            amigo+=mv; f['cargo']-=mv; f['rec']['amigo']+=mv
    # 2. waiting river vessels take loads
    NOR=lambda f: f['rec']['n'] in f['amigo_only']
    for r in waiting:
        avail=sum(f['cargo'] for f in here if not NOR(f))
        if avail<=0: continue
        incoming=any(f['phase']=='to_aia' and f['t']-t<=days(0.5) for f in fly)
        take=min(r['cap'],avail)
        if take<r['cap'] and incoming: continue
        # don't send a river vessel off with a small part load if a Fly vessel arrives within 1.5 days
        if take<0.5*r['cap'] and any(f['phase']=='to_aia' and f['t']-t<=days(1.5) for f in fly): continue
        srcs=[]; need=take
        for f in sorted([f for f in here if not NOR(f)],key=lambda f:f['arr']):
            if need<=0: break
            m=min(f['cargo'],need); 
            if m<=0: continue
            f['cargo']-=m; need-=m; f['rec']['to'][r['name']]=f['rec']['to'].get(r['name'],0)+m; f['busy']=t+days(LA); srcs.append(f)
        r['phase']='loading'; r['t']=t+days(LA); r['cargo']=take
        r['rec']=dict(Vessel=r['name'],at='Aiambak',frm=', '.join(s['name'] for s in srcs),ls=t,dep=None,k=None,cfo=take)
        for s in srcs: s['rec']['ks'].append(r['rec'])
    # 3. reserve for river vessels due within window, rest to Amigo
    due=sorted([r for r in riv if r['phase']=='to_aia' and r['t']-t<=days(W)],key=lambda r:r['t'])
    for f in sorted(here,key=lambda f:f['arr']):
        reserve=0
        soon=any(g['phase']=='to_aia' and g['t']-t<=days(1.5) for g in fly)
        for r in riv:
            if r['phase']=='waiting' and not (soon and f['cargo']<0.5*r['cap']) and not NOR(f): reserve+=r['cap']
        if t<f['arr']+days(W) and not NOR(f):
            for r in due: reserve+=r['cap']
        mv=min(max(0,f['cargo']-reserve),CAP-amigo)
        if mv>0: amigo+=mv; f['cargo']-=mv; f['rec']['amigo']+=mv
    # 4. Fly departures
    for f in here:
        if f['cargo']<=0 and t>=f['busy'] and t>=f['arr']+days(f.get('da',DA)) and (f['dfrom'] is None or t>=f['dfrom']+days(f.get('da',DA))):
            f['rec']['depA']=t; f['rec']['etaP']=t+days(TB); f['recs'].append(f['rec']); f['phase']='to_pom'; f['t']=t+days(TB)
    # 5. emergency river loads from Amigo
    for r in [r for r in riv if r['phase']=='waiting']:
        horizon=t+days(LA+TAK)
        en_route=sum(x['cargo'] for x in riv if x['phase'] in('to_k','loading') and x['rec'] and (x['rec'].get('k') or x['t']+days(TAK))<=horizon)
        trucks_in=sum(l for a,l in truck_q if a<=horizon)+(rate(t)*(LA+TAK) if trucks_on(t) and amigo>rate(t) else 0)
        proj=site+en_route+trucks_in-USE*(LA+TAK)
        if proj<USE*BUF and amigo>0 and sum(f['cargo'] for f in here)<=0:
            take=min(r['cap'],amigo); amigo-=take
            r['phase']='loading'; r['t']=t+days(LA); r['cargo']=take
            r['rec']=dict(Vessel=r['name'],at='Aiambak',frm='Amigo 1 (emergency)',ls=t,dep=None,k=None,cfo=take); emerg.append((t,r['name'],take))
    # --- trucks & site (hourly)
    out=0; q0=len(truck_q)  # out = litres taken from Amigo 1; sent = litres leaving Aiambak by truck
    for a,l in PREFILL:
        if a==t: l=min(l,amigo); amigo-=l; out+=l; CREDIT+=l
    for a,l,fa in EXTRA:  # one-off loads, e.g. diesel tank-tainers (fa = filled from Amigo 1)
        if a==t:
            if fa: l=min(l,amigo); amigo-=l; out+=l
            truck_q.append((t+dt.timedelta(hours=HRS),l))
    if trucks_on(t) and TRUCKMODE and CONV and convoys(t)==[(h,k) for h,k in CONV]:
        # per-truck model: a truck leaves with its convoy if it can be filled; trucks that can't be fuelled
        # wait at Aiambak and leave with the next convoy once there is CFO for them
        if not TRUCKS:
            for h,k in CONV: TRUCKS.extend(dict(home=h,ready=t,missed=False) for _ in range(k))
        for k in TRUCKS:
            if t.hour==k['home'] and k['ready']>t and (k.get('last') is None or t-k['last']>dt.timedelta(hours=12)): k['missed']=True  # not back in time for its own convoy
        if t.hour in [h for h,k in CONV]:
            elig=[k for k in TRUCKS if k['ready']<=t and (k['home']==t.hour or k['missed'])]
            elig.sort(key=lambda k:(not k['missed']))
            for k in elig:
                if CREDIT>=TSIZE or amigo>=TSIZE:
                    if CREDIT>=TSIZE: CREDIT-=TSIZE
                    else: amigo-=TSIZE; out+=TSIZE
                    truck_q.append((t+dt.timedelta(hours=HRS),TSIZE)); k['ready']=t+dt.timedelta(hours=TURN); k['missed']=False; k['last']=t
                    TRUCKLOG.append((t,k['home']))
                else: k['missed']=True
    elif trucks_on(t):
        for ch,nk in convoys(t):  # each convoy: all its trucks leave together at hour ch
            if t.hour!=ch or ch in PEND: continue
            pre=sum(l for a,l in PRE if a.date()==t.date() and a.hour==ch)  # trucks already loaded before this convoy
            PEND[ch]=[nk*TSIZE-pre,pre,t]
        for ch in sorted(PEND):
            need,pre,due=PEND[ch]
            if t<LASTDEP.get(ch,t-days(9))+dt.timedelta(hours=TURN): continue
            if HOLD and amigo<need: continue  # convoy waits at Aiambak until Amigo 1 can fill every truck
            o=min(need,amigo); amigo-=o; out+=o; truck_q.append((t+dt.timedelta(hours=HRS),o+pre))
            CONVLOG.append((due,t,ch,o+pre)); LASTDEP[ch]=t; del PEND[ch]
    sent=sum(l for a,l in truck_q[q0:])
    rin=0
    for r in riv:
        pass
    arrived=sum(l for a,l in truck_q if a<=t); truck_q=[(a,l) for a,l in truck_q if a>t]
    rv_in=sum(rec['cfo'] for rec in rrecs if rec['k']>=t and rec['k']<t+H and rec['k']>=NOW) if False else 0
    rin=0
    for q in dis_q:
        # a discharge that runs past midnight is counted in full when it finishes, so it isn't split across two days
        if q[1]>1 and (q[0]+H*(q[1]-1)).date()!=q[0].date(): q[0]=q[0]+H*(q[1]-1); q[2]=q[2]*q[1]; q[1]=1
        if q[0]<=t and q[1]>0: rin+=q[2]; q[1]-=1
    dis_q=[q for q in dis_q if q[1]>0]
    site+=arrived+rin-USE/24
    hourly.append(dict(t=t,amigo=amigo,out=out,sent=sent,truck_in=arrived,river_in=rin,site=site,held=sum(f['cargo'] for f in fly if f['phase']=='at_aia')+sum(w['cargo'] for w in shs if w['phase']=='at_aia')+sum(w['cargo'] for w in ros if w['phase']=='at_aia')))
    t+=H
    # river arrivals to site are handled by matching recs after the loop (added at ETA)

# finalize open records
for f in fly:
    if f['phase']=='at_aia': f['rec']['depA']=None; f['rec']['etaP']=None; f['recs'].append(f['rec'])
for r in riv:
    if r['phase'] in('to_k','loading') and r['rec'] and r['rec'] not in rrecs:
        rec=r['rec']; 
        if rec.get('dep') is None: rec['dep']=r['t']; rec['k']=r['t']+days(TAK)
        rec['ret']=rec['k']+days(DK+TKA+(TB if r['combo'] and rec['at']=='Aiambak' else 0)); rrecs.append(rec)
json.dump(dict(),open('/dev/null','w'))
F=lambda x: x.strftime("%Y-%m-%dT%H:%M:%S") if x else None
# ---------- outputs
flyrows=[]
DAV={f['name']:f['da'] for f in fly}
allrecs=sorted([r for f in fly for r in f['recs']]+[r for w in shs for r in w['recs']]+[r for w in ros for r in w['recs']],key=lambda r:r['eta'])
allrecs=[r for r in allrecs if r['eta']<=END]
for r in allrecs:
    to=r['to']; names=[k for k in ['Elimbari','Diamond'] if to.get(k)]+(['Amigo 1'] if r['amigo']>0 else [])
    ks=[x.get('k') for x in r['ks'] if x.get('k')]
    k=max(ks) if ks else None
    lead=round((k-r['dep']).total_seconds()/86400,2) if k else None
    wait=round(max(0,(r['depA']-r['eta']).total_seconds()/3600-(DAV.get(r['Vessel'],DA)*24 if r['Vessel']!='Wonderland' else (WS['cfo']/2+WS['freight_aia'])*24)),1) if r.get('depA') else None
    flyrows.append([r['Vessel'],r['n'],F(r['dep']),F(r['eta']),r['cfo'],', '.join(names),sum(to.values()),r['amigo'],F(k),lead,F(r['ls']),F(r.get('depA')),F(r.get('etaP')),wait])
riverrows=[[x['Vessel'],x['at'],x['frm'],F(x['ls']),F(x['dep']),F(x['k']),x['cfo'],F(x['ret'])] for x in sorted(rrecs+FLYK+[k for v in ros for k in v['krecs']],key=lambda x:x['k']) if x['k']<=END+days(1)]
# daily
daily=[]; sitedaily=[]
for i in range(7*P['weeks']):
    d0=START+days(i); d1=d0+days(1)
    hs=[h for h in hourly if d0<=h['t']<d1]
    out=sum(h['out'] for h in hs); close=hs[-1]['amigo'] if hs else P['amigo_open']; held=hs[-1]['held'] if hs else 0
    prevc=daily[-1][3] if daily else P['amigo_open']
    inn=max(0,close-prevc+out)
    arr=', '.join(r['Vessel'] for r in allrecs if d0<=r['eta']<d1) or None
    load=', '.join(x['Vessel'] for x in rrecs if x['at']=='Aiambak' and x['frm']!='Before schedule start' and d0<=x['ls']<d1) or None
    daily.append([d0.strftime('%Y-%m-%d'),round(inn),round(out),round(close),round(held),arr,load,round(sum(h['sent'] for h in hs))])
    rv=sum(h.get('river_in',0) for h in hs); tr=sum(h['truck_in'] for h in hs); use=USE/24*len(hs)+((USE*max(0,(NOW-max(d0,T(P['site_measured']))).total_seconds()/86400)) if (P.get('site_measured') and d0<=NOW<d1) else 0)
    sc=hs[-1]['site'] if hs else P['site_open']; dof=sc/USE
    low=min([h['site'] for h in hs]+[sc]) if hs else sc
    sitedaily.append([d0.strftime('%Y-%m-%d'),round(rv),round(tr),round(use),round(sc),round(dof,2),('SHORT – site runs out during the day' if low<0 else ('Below buffer' if dof<BUF or low<USE*0.5 else 'OK')),round(low)])
lowest=min(hourly,key=lambda h:h['site'])
out=dict(trucklog=[(F(a),b) for a,b in TRUCKLOG],convoys=[(F(a),F(b),c,d) for a,b,c,d in CONVLOG],fly=flyrows,river=riverrows,amigo=daily,site=sitedaily,emerg=[(F(a),b,c) for a,b,c in emerg],lowest=(F(lowest['t']),round(lowest['site'])))
json.dump(out,open('engine_out.json','w'),ensure_ascii=False,indent=0)
import sys
if os.environ.get('Q'): 
    pass
print('lowest site',out['lowest'],'emergencies',out['emerg'])
print('trucked',sum(r[2] for r in daily),'river',sum(r[6] for r in riverrows))
for r in flyrows: print(r[0],r[1],r[3][5:16],'cfo',r[4],'->',r[5],'amigo',r[7],'wait h',r[13],'depA',(r[11] or '')[5:16])

print('ROSTER',[(v['name'],[(F(a)[5:10],b) for a,b in v.get('log',[])]) for v in ros])
