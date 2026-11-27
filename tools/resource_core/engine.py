"""Pilot V4 candidate physiology; game units, not real-world physiology."""
from dataclasses import dataclass, field
import math
import random

def clamp(x, lo=0., hi=1.):
    return min(hi,max(lo,x))

@dataclass
class State:
    hp: float = 100
    st: float = 100
    ft: float = 0
    ns: float = 0
    bl: list = field(default_factory=lambda: [0.,0.,0.,0.])
    unconscious: bool = False
    protected: bool = False
    elapsed: float = 0
    recovering: bool = False

@dataclass(frozen=True)
class Character:
    strength: float = 10
    constitution: float = 10
    wisdom: float = 10
    will: float = 10
    hpmax: float = 100
    stmax: float = 100
    dexterity: float = 10

# omega and gamma are supplied by profiles; these are BL coefficients.
PROFILES={
    "force":(.9,.25,2.,(.65,.25,.10)),
    "strike":(.6,.35,1.5,(.65,.25,.10)),
    "lift":(.5,.25,1.2,(.35,.4,.25)),
    "hold":(.15,.15,.5,(.6,.35,.05)),
    "carry":(.25,.25,.6,(.35,.4,.25)),
    "run":(.25,.25,.6,(.1,.2,.7)),
    "sprint":(.75,.25,2.,(.1,.2,.7)),
    "walk":(.25,.25,0.,(.1,.2,.7)),
    "jump":(.45,.25,.8,(.05,.25,.7)),
    "aim":(.5,.15,.5,(.65,.3,.05)),
    "block":(.15,.15,.5,(.6,.35,.05)),
    "swim":(.35,.2,.6,(.4,.2,.4)),
    "climb":(.35,.2,.6,(.45,.25,.3)),
}
MOVEMENT={"run","sprint","walk","jump","swim","climb"}

def dual_cost(base, omega, absolute, relative, gamma=2., efficiency=1.):
    return base/efficiency*(omega*absolute+(1-omega)*relative**gamma)

def exhaustion_damage(ft, delta, harmful):
    # Integral of positive linear fatigue excess over this interval.
    if delta<=0: return .1*harmful*max(0.,ft-50)/50
    a=max(0.,ft-50)
    b=max(0.,ft+delta-50)
    return .1*harmful*(b*b-a*a)/(100*delta)

class Engine:
    def __init__(self, character, version=7, seed=0, keep_ledger=True, adaptive=True):
        if version not in (4,5,6,7): raise ValueError("version")
        if not all(math.isfinite(x) and x>0 for x in vars(character).values()):
            raise ValueError("character")
        self.c=character
        self.version=version
        self.state=State(character.hpmax,character.stmax)
        self.rng=random.Random(seed)
        self.hazard=self.rng.expovariate(1)
        self.reservations={}
        self.seen_ids=set()
        self.ledger=[]
        self.keep_ledger=keep_ledger
        self.last=None
        self.time=0.
        self.last_spend=-math.inf
        self.recovery_duration=10.
        self.adaptive=adaptive
        self.min_slice=.001
        self.refinements=0

    def label(self):
        s=self.state
        return ("DEAD" if s.hp<=0 else "UNCONSCIOUS" if s.unconscious else
                "PROTECTED" if s.protected else "RECOVERING" if s.recovering else "CONSCIOUS")

    def transition(self,label):
        s=self.state
        if label==self.label(): return
        s.unconscious=label=="UNCONSCIOUS"
        s.protected=label=="PROTECTED"
        s.recovering=label=="RECOVERING"
        s.elapsed=0.
        if label in ("UNCONSCIOUS","DEAD"):
            self.reservations.clear()
            self.hazard=self.rng.expovariate(1)
        if label=="RECOVERING":
            self.recovery_duration=5+15*(1-s.hp/self.c.hpmax)+10*s.ft/(120*(self.c.will/10)**.4)

    def validate(self,r):
        values=(r.power,r.minimum,r.duration,r.local_limit,r.omega,r.base,r.gamma,r.efficiency,r.load,r.support)
        if not all(math.isfinite(x) for x in values) or not (
            r.power>=0 and 0<=r.minimum<=1 and r.duration>0 and r.local_limit>=0
            and 0<=r.omega<=1 and r.base>=0 and r.gamma>=1 and 1<=r.efficiency<=3
            and r.load>0 and r.support>0 and 0<=r.priority<=4 and 0<r.channels<=31
            and r.kind in PROFILES and r.mode in ("natural","forced","maximum")):
            raise ValueError("invalid action")

    def step(self, requests=(), dt=.05):
        """Requests start now; split integration at physical reservation ends."""
        if not math.isfinite(dt) or dt<=0: raise ValueError("dt")
        requests=tuple(requests)
        if len({r.id for r in requests})!=len(requests): raise ValueError("duplicate action id")
        for r in requests: self.validate(r)
        self.reservations={k:v for k,v in self.reservations.items() if v[1]>self.time+1e-10}
        for r in requests:
            if r.id in self.reservations and self.reservations[r.id][0]!=r:
                raise ValueError("reservation id reused with different payload")
        requests=tuple(r for r in requests if r.id not in self.seen_ids or r.id in self.reservations)
        self.seen_ids.update(r.id for r in requests)
        finish=self.time+dt
        first=True
        result={}
        while self.time<finish-1e-10:
            fresh=requests if first else ()
            end=min([finish]+[v[1] for v in self.reservations.values() if v[1]>self.time+1e-10]+
                    [self.time+r.duration for r in fresh])
            res=self._slice(fresh,end-self.time)
            if first: result=res
            first=False
        return result

    def _slice(self,requests,dt):
        c,s=self.c,self.state
        before=s.st
        ft_before=s.ft
        hp_before=s.hp
        will=(c.will/10)**.4
        nfs=s.ft*(1-.65*s.ns)
        nfs_before=nfs
        if s.hp>0 and nfs>=210*will: self.transition("UNCONSCIOUS")
        elif self.label()=="CONSCIOUS" and s.ft>=210*will: self.transition("PROTECTED")
        start_state=self.label()
        if start_state in ("DEAD","UNCONSCIOUS"):
            self.reservations.clear()
            requests=()
        active={k:v[0] for k,v in self.reservations.items() if v[1]>self.time+1e-10}
        active.update({r.id:r for r in requests if r.id not in active})
        h=clamp(s.hp/c.hpmax)
        available=c.stmax/(1+s.ft/200)
        st_fraction=clamp(s.st/available)
        e=(.3+.7*min(1,2*st_fraction))/(1+s.ft/300)
        strength,con,dex,wis=c.strength/10,c.constitution/10,c.dexterity/10,c.wisdom/10
        force=10*strength**.9*con**.1
        durability=10*con**.9*strength**.1
        speed=10*dex**.8*strength**.2
        coordination=10*dex**.85*wis**.15
        recovery=1.
        if s.recovering: recovery=clamp(s.elapsed/self.recovery_duration)
        functional_force=force*e*(.7+.3*recovery)
        functional_speed=speed*(.4+.6*e)*(.6+.4*recovery)
        functional_coord=coordination*(.2+.8*e)*(.4+.6*recovery)
        health=.5+.5*math.sqrt(h)
        k=health/(1+s.ft/300)
        sustainable=10*con**.65*strength**.15*k
        extra=20*strength**.65*con**.15*k
        burst=sustainable+extra*math.exp(-s.bl[0]/5)
        budget=sustainable if s.protected else burst
        limited=self.version>=6 or s.protected
        protect=min(clamp(h/.25),1/(1+max(0,s.ft-50)/100),clamp((1.5-s.ft/(120*will))/.7))
        info={}
        for key,r in active.items():
            if s.protected and (r.kind not in ("walk","aim") or r.mode!="natural"): continue
            lb,ls,bl_rate,weights=PROFILES[r.kind]
            local=s.bl[0]+sum(w*b for w,b in zip(weights,s.bl[1:]))
            lam=ls+(lb-ls)*math.exp(-local/5)
            tolerance=durability*max(1.,force/durability)**lam*r.support
            cap=functional_speed if r.kind in MOVEMENT else functional_coord if r.kind=="aim" else functional_force
            if r.kind in MOVEMENT: tolerance*=speed/force
            elif r.kind=='aim': tolerance*=coordination/force
            reg=protect if r.mode=="natural" else .5+.5*protect if r.mode=="forced" else 1.
            top=min(1.,cap/max(r.power,1e-12))*reg
            if r.mode!="maximum":
                top=min(top,(1. if r.mode=="natural" else 1.5)*tolerance/max(r.power*r.load,1e-12))
            if s.protected:
                top=min(top,.25*math.sqrt(clamp(h/.25))*clamp((210*will-s.ft)/(90*will)))
                if r.kind=="walk": top=min(top,.1)
            factor=1.25 if r.mode=="forced" else 1.
            local_budget=min(r.local_limit,factor*(sustainable+extra*math.exp(-local/5))) if limited and r.mode!="maximum" else r.local_limit
            info[key]=(r,cap,tolerance,top,local_budget,bl_rate,weights)

        def evaluate(key,i):
            r,cap,tolerance,_,_,_,_=info[key]
            output=r.power*i
            q=output*r.load/max(tolerance,1e-12)
            base=0. if i<=0 else (r.base/r.efficiency*math.sqrt(output/10) if self.version==4 else
                dual_cost(r.base,r.omega,output/10,output/max(cap,1e-12),r.gamma,r.efficiency))
            return output,base*(1+max(0.,q-1)**2),q,base

        chosen={}
        occupied=0
        mode_power={"natural":0.,"forced":0.,"maximum":0.}
        zone_used={mode:[0.,0.,0.] for mode in mode_power}
        zone_limits=[sustainable if s.protected else sustainable+extra*math.exp(-(s.bl[0]+b)/5) for b in s.bl[1:]]
        # V4-V6 share one proportional group; V7 allocates by priority.
        groups=range(5) if self.version==7 else (None,)
        for priority in groups:
            pending=sorted((key for key,v in info.items() if priority is None or v[0].priority==priority))
            while pending:
                compatible=[]
                mask=occupied
                for key in pending:
                    r=info[key][0]
                    if not r.channels&mask:
                        compatible.append(key)
                        mask|=r.channels
                if not compatible: break
                def fits(scale):
                    costs=[evaluate(key,info[key][3]*scale)[1] for key in compatible]
                    if not all(p<=info[key][4] for key,p in zip(compatible,costs)): return False
                    if not limited: return True
                    totals=dict(mode_power)
                    zones={m:list(v) for m,v in zone_used.items()}
                    for key,p in zip(compatible,costs):
                        mode=info[key][0].mode
                        totals[mode]+=p
                        for j in range(3): zones[mode][j]+=p*info[key][6][j]
                    # Maximum may exceed throughput but cannot grant free capacity
                    # to natural/forced actions. Both restricted modes share one pool.
                    return (totals["natural"]<=budget+1e-10
                            and totals["natural"]+totals["forced"]<=1.25*budget+1e-10
                            and all(zones["natural"][j]<=zone_limits[j]+1e-10
                                    and zones["natural"][j]+zones["forced"][j]<=1.25*zone_limits[j]+1e-10
                                    for j in range(3)))
                if fits(1.): scale=1.
                else:
                    lo,hi=0.,1.
                    for _ in range(32):
                        mid=(lo+hi)/2
                        if fits(mid): lo=mid
                        else: hi=mid
                    scale=lo
                rejected={key for key in compatible if info[key][3]*scale<info[key][0].minimum*min(1.,info[key][1]/max(info[key][0].power,1e-12)) or info[key][3]*scale<=1e-12}
                if rejected:
                    pending=[key for key in pending if key not in rejected]
                    continue
                for key in compatible:
                    intensity=info[key][3]*scale
                    chosen[key]=intensity
                    allocated=evaluate(key,intensity)[1]
                    mode=info[key][0].mode
                    mode_power[mode]+=allocated
                    for j in range(3): zone_used[mode][j]+=allocated*info[key][6][j]
                    occupied|=info[key][0].channels
                break

        def preview(intensities):
            rows={key:evaluate(key,i) for key,i in intensities.items()}
            power=sum(row[1] for row in rows.values())
            demand=power*dt
            paid=min(max(0.,min(s.st,available)),demand)
            deficit=demand-paid
            overload=sum(.5*row[3]*max(0.,row[2]-1)**2*dt for row in rows.values())
            activity=sum(.03*paid*row[1]/max(power,1e-12)*row[2] for row in rows.values())
            strain=.05*paid*max(0.,power/max(sustainable,1e-12)-1)**2 if self.version>=6 else 0.
            harmful=.5*deficit/(con**.2)+overload
            fatigue=harmful+activity+strain
            damage=exhaustion_damage(s.ft,fatigue,harmful)+sum(.2*row[3]*max(0.,row[2]-1.5)**2*dt for row in rows.values())
            a=clamp(max([power/max(burst,1e-12)]+[.05 if info[key][0].kind=="walk" else i for key,i in intensities.items()]))
            ks=.2*health*(1. if not rows else .5 if a<=.05 else .25 if a<=.1 else 0.)
            kd=.8*a*a+.4*max([0.]+[row[2]-1 for row in rows.values()])
            eq=ks/(ks+kd) if ks+kd else s.ns
            ns=clamp(eq+(s.ns-eq)*math.exp(-(ks+kd)*dt))
            return rows,power,paid,fatigue,damage,ns,a,strain

        def safe(values,pr):
            modes={info[key][0].mode for key in values}
            if not modes or modes=={"maximum"}: return True
            reserve=.05 if "natural" in modes else .01
            threshold=180 if s.protected else 210
            return s.hp-pr[4]>=min(s.hp,reserve*c.hpmax)-1e-10 and (s.ft+pr[3])*(1-.65*pr[5])<threshold*will

        pr=preview(chosen)
        if not safe(chosen,pr):
            # Conservative joint backoff. Mixed mode requests do not bypass safety.
            lo,hi=0.,1.
            for _ in range(32):
                mid=(lo+hi)/2
                trial={key:i*mid for key,i in chosen.items() if i*mid>=info[key][0].minimum*min(1.,info[key][1]/max(info[key][0].power,1e-12)) and i*mid>1e-12}
                if safe(trial,preview(trial)): lo=mid
                else: hi=mid
            chosen={key:i*lo for key,i in chosen.items() if i*lo>=info[key][0].minimum*min(1.,info[key][1]/max(info[key][0].power,1e-12)) and i*lo>1e-12}
            pr=preview(chosen)
            if not safe(chosen,pr): chosen={}; pr=preview(chosen)
        rows,power,paid,fatigue,damage,ns,a,strain=pr
        # Refine BEFORE committing any resource/action effects. The outer step
        # integrates the remaining interval, preserving event start/end times.
        # Threshold crossing is bounded to min_slice, not claimed exact.
        projected_ft=s.ft+fatigue
        if s.hp>damage and (not rows or all(info[key][0].kind=="walk" for key in rows)):
            projected_ft=max(0.,projected_ft-.5*con**.4*max(.25,math.sqrt((s.hp-damage)/c.hpmax))*dt*(1. if not rows else .2))
        projected=projected_ft*(1-.65*ns)
        x=clamp((projected-120*will)/(90*will))
        p=x*x*(a*a if s.protected else 1.)
        hazard_loss=-math.log1p(-p)*dt if p<1 else math.inf
        crossing=(any(min(nfs,projected)<t*will<=max(nfs,projected) for t in (120,180,210))
                  or (not s.unconscious and hazard_loss>=self.hazard)
                  or (s.hp>0 and damage>=s.hp))
        critical=(fatigue>2.5 or damage>max(.1,.005*c.hpmax) or (rows and projected>=110*will))
        if self.adaptive and dt>2*self.min_slice and (crossing or (critical and dt>.005)):
            self.refinements+=1
            return self._slice(requests,dt/2)
        mode_power={m:sum(rows[k][1] for k in rows if info[k][0].mode==m) for m in mode_power}
        self.reservations={key:self.reservations.get(key,(active[key],self.time+active[key].duration))
                           for key in chosen}
        initial_clamp=max(0.,s.st-available)
        s.st-=initial_clamp+paid
        s.ft+=fatigue
        s.hp=max(0.,s.hp-damage)
        s.ns=ns
        if paid>0: self.last_spend=self.time+dt
        used=[False]*3
        work=distance=precision=hold=peak_force=carry_work=carry_distance=0.
        for key,i in chosen.items():
            r,_,_,_,_,bl_rate,weights=info[key]
            output,_,q,_=rows[key]
            load=bl_rate*i**1.5*math.sqrt(max(0,q))*dt
            s.bl[0]+=.4*load
            for j,w in enumerate(weights):
                s.bl[j+1]+=.6*w*load
            for j,mask in enumerate((3,4,24)): used[j]|=bool(r.channels&mask)
            if r.kind in MOVEMENT: distance+=output*dt
            elif r.kind=="carry":
                travelled=functional_speed*i*dt
                carry_distance+=travelled
                carry_work+=output*travelled
            elif r.kind=="aim": precision+=output*dt
            elif r.kind in ("hold","block"): hold+=output*dt
            else:
                work+=output*dt
                peak_force=max(peak_force,output)
        recovered=0.
        if s.hp>0:
            rest=not rows
            slow=bool(rows) and all(info[key][0].kind=="walk" for key in rows)
            health_recovery=max(.25,math.sqrt(s.hp/c.hpmax))
            if rest or slow:
                s.ft=max(0.,s.ft-.5*con**.4*health_recovery*dt*(1. if rest else .2))
                cap=c.stmax/(1+s.ft/200)
                eligible=max(0.,self.time+dt-max(self.time,self.last_spend+2))
                rate=5*con**.4*wis**.1*health_recovery*(.75 if s.unconscious else 1.5 if rest else .25)
                recovered=min(max(0.,cap-s.st),rate*eligible)
                s.st+=recovered
            bl_recovery=1.5*health*(.5+.5*st_fraction)/(1+s.ft/200)*dt
            if rest: s.bl[0]=max(0.,s.bl[0]-.4*bl_recovery)
            for j in range(3):
                if not used[j]: s.bl[j+1]=max(0.,s.bl[j+1]-.2*bl_recovery)
        cap=c.stmax/(1+s.ft/200)
        final_clamp=max(0.,s.st-cap)
        s.st-=final_clamp
        nfs=s.ft*(1-.65*s.ns)
        if s.hp<=0:
            self.reservations.clear()
            s.unconscious=s.protected=s.recovering=False
        elif not s.unconscious:
            x=clamp((nfs-120*will)/(90*will))
            p=x*x*(a*a if s.protected else 1.)
            self.hazard-=(-math.log1p(-p)*dt if p<1 else math.inf)
            if nfs>=210*will or self.hazard<=0: self.transition("UNCONSCIOUS")
        if self.label()==start_state: s.elapsed+=dt
        if s.unconscious and nfs<=180*will and s.elapsed>=3+7*(1-s.hp/c.hpmax):
            self.transition("PROTECTED")
        elif s.protected and s.ft<=80*will*(.5+.5*math.sqrt(s.hp/c.hpmax)) and nfs<120*will and s.st>=.1*cap and a<=.1:
            self.transition("RECOVERING")
        elif s.recovering and s.elapsed>=self.recovery_duration and nfs<120*will and s.st>=.25*cap:
            self.transition("CONSCIOUS")
        elif s.recovering and s.ft>=120*will: self.transition("PROTECTED")
        self.time=round(self.time+dt,12)
        crossed=[t for t in (120,180,210) if min(nfs_before,nfs)<t*will<=max(nfs_before,nfs)]
        restricted=mode_power["natural"]+mode_power["forced"]
        allowed=1.25*budget if mode_power["forced"]>0 else budget
        budget_excess=max(0.,mode_power["natural"]-budget,restricted-allowed) if limited else 0.
        row=dict(time=self.time,dt=dt,before=before,paid=paid,recovered=recovered,
                 clamp=initial_clamp+final_clamp,after=s.st,power=power,budget=allowed if limited else power,
                 budget_excess=budget_excess,burst=burst,sustainable=sustainable,
                 natural_power=mode_power["natural"],forced_power=mode_power["forced"],maximum_power=mode_power["maximum"],
                 intentional_excess=max(0.,power-allowed) if limited else 0.,
                 ft_gained=fatigue,ft_recovered=max(0.,ft_before+fatigue-s.ft),
                 theoretical_force=force,carry_work=carry_work,carry_distance=carry_distance,
                 nfs_crossings=len(crossed),crossing_width=dt if crossed else 0.,
                 nfs_violation=int(s.hp>0 and nfs>=210*will and not s.unconscious),
                 ft=s.ft,nfs=nfs,hp=s.hp,damage=hp_before-s.hp,work=work,distance=distance,
                 precision=precision,hold=hold,peak_force=peak_force,max_q=max([0.]+[v[2] for v in rows.values()]),
                 strain=strain,requested_seconds=len(active)*dt,
                 fulfilled_seconds=sum(dt for i in chosen.values() if i>=1-1e-8),
                 rejected=len(active)-len(chosen),bl=max(s.bl),start_state=start_state,state=self.label(),
                 unconscious=s.unconscious,protected=s.protected,recovering=s.recovering)
        assert abs(before-paid+recovered-row["clamp"]-s.st)<1e-7
        assert 0<=s.st<=cap+1e-8 and 0<=s.ns<=1 and 0<=s.hp<=c.hpmax and s.ft>=0
        assert budget_excess<=1e-8
        assert abs(ft_before+fatigue-row["ft_recovered"]-s.ft)<1e-7
        self.last=row
        if self.keep_ledger: self.ledger.append(row)
        return {key:(i,rows[key][1],active[key].duration) for key,i in chosen.items()}
