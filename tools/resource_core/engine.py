"""Experimental dynamic V4–V7 kernel. Standard library only."""
from dataclasses import dataclass, field
import math
import random
from allocator import Request, allocate

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

@dataclass(frozen=True)
class Character:
    strength: float = 10
    constitution: float = 10
    wisdom: float = 10
    will: float = 10
    hpmax: float = 100
    stmax: float = 100

class Engine:
    def __init__(self, character, version=7, seed=0):
        if version not in (4,5,6,7):
            raise ValueError("version")
        self.c = character
        self.version = version
        self.state = State(character.hpmax, character.stmax)
        self.rng = random.Random(seed)
        self.reservations = {}
        self.ledger = []
        self.time = 0

    def step(self, requests=(), dt=.05):
        if not math.isfinite(dt) or dt <= 0:
            raise ValueError("dt")
        c, s = self.c, self.state
        before = s.st
        h = max(0., s.hp/c.hpmax)
        k = (.5+.5*math.sqrt(h))/(1+s.ft/300)
        sustainable = 10*(c.constitution/10)**.65*(c.strength/10)**.15*k
        burst = sustainable+20*(c.strength/10)**.65*(c.constitution/10)**.15*k*math.exp(-s.bl[0]/5)
        will = (c.will/10)**.4
        if s.ft*(1-.65*s.ns)>=210*will:
            s.unconscious = True
            s.protected = False
        if s.unconscious or s.hp<=0:
            self.reservations.clear()
            requests = ()
        active = {r.id:r for r in requests}
        for key,(r,end) in list(self.reservations.items()):
            if end > self.time+1e-9:
                active[key] = r
            else:
                del self.reservations[key]
        budget = sustainable if s.protected else burst
        if self.version<6:
            budget = sum(r.power for r in active.values())
        if self.version==7:
            result = allocate(active.values(),budget)
        else:
            result = {r.id: (min(1.,budget/max(r.power,1e-12)),min(r.power,budget),r.duration) for r in active.values()}
        for key in result:
            if key not in self.reservations:
                r=active[key]
                self.reservations[key]=(r,self.time+r.duration)
        power = sum(v[1] for v in result.values())
        demand = power*dt
        paid = min(s.st,demand)
        s.st -= paid
        deficit = demand-paid
        strain = .05*paid*max(0.,power/max(sustainable,1e-12)-1)**2 if self.version>=6 else 0.
        fatigue = .5*deficit/(c.constitution/10)**.2+.03*paid+strain
        s.ft += fatigue
        for key,(intensity,_,_) in result.items():
            load=intensity**1.5*dt
            s.bl[0]+=.4*load
            mask=active[key].channels
            weights=[bool(mask&3),bool(mask&4),bool(mask&24)]
            n=sum(weights) or 1
            for i,w in enumerate(weights):
                s.bl[i+1]+=.6*load*w/n
        recovered=0.
        if not result:
            s.ft=max(0.,s.ft-.5*(c.constitution/10)**.4*dt)
            s.bl=[max(0.,x-1.5*dt/4) for x in s.bl]
            available=c.stmax/(1+s.ft/200)
            recovered=min(max(0.,available-s.st),5*(c.constitution/10)**.4*(c.wisdom/10)**.1*dt*(.75 if s.unconscious else 1))
            s.st+=recovered
        cap=c.stmax/(1+s.ft/200)
        clamp=max(0.,s.st-cap)
        s.st-=clamp
        a=min(1.,power/max(burst,1e-12))
        ks=.2*(.5+.5*math.sqrt(h)) if not result else 0.
        kd=.8*a*a
        if ks+kd:
            eq=ks/(ks+kd)
            s.ns=eq+(s.ns-eq)*math.exp(-(ks+kd)*dt)
        nfs=s.ft*(1-.65*s.ns)
        x=max(0.,min(1.,(nfs-120*will)/(90*will)))
        p=x*x*(a*a if s.protected else 1.)
        if not s.unconscious and (nfs>=210*will or self.rng.random()<1-(1-p)**dt):
            s.unconscious=True
            s.protected=False
            s.elapsed=0
        if s.unconscious:
            s.elapsed+=dt
            if s.hp>0 and nfs<=180*will and s.elapsed>=3+7*(1-h):
                s.unconscious=False
                s.protected=True
                s.elapsed=0
        elif s.protected and s.ft<=80*will*(.5+.5*math.sqrt(h)) and s.st>=.1*cap:
            s.protected=False
        self.time+=dt
        row=dict(time=self.time,before=before,paid=paid,recovered=recovered,clamp=clamp,after=s.st,power=power,budget=budget,ft=s.ft,nfs=nfs)
        assert abs(before-paid+recovered-clamp-s.st)<1e-8
        assert 0<=s.st<=cap+1e-8
        if self.version==7:
            assert power<=budget+1e-8
        self.ledger.append(row)
        return result
