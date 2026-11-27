"""Named, physical-time scenarios. Durations are seconds, not ticks."""
from dataclasses import dataclass
from allocator import Request

@dataclass(frozen=True)
class Action:
    kind: str
    power: float
    period: float = 1.
    duration: float = 1.
    channels: int = 7
    priority: int = 2
    mode: str = "natural"
    load: float = 1.
    support: float = 1.
    efficiency: float = 1.

    def request(self,key,duration):
        base,omega,gamma,minimum={
            "force":(10,.5,2,.01),"strike":(12,.6,2,.01),"lift":(10,.7,2,.01),
            "hold":(2,.4,2.5,.01),"carry":(6,.85,2,.01),"run":(3,.65,2,.01),
            "sprint":(6,.65,2,.01),"walk":(0,.65,2,.01),"jump":(4,.5,2,.01),
            "aim":(2,.25,1.5,.01),"block":(3,.4,2.5,.01),
            "swim":(3,.65,2,.01),"climb":(4,.65,2,.01)}[self.kind]
        # Discrete action base is per completed event; convert to a rate once.
        if self.kind=="strike" and self.power<=10: base=5.
        if self.kind in ("strike","jump","lift") or (self.kind=="force" and self.duration<1):
            base/=self.duration
        return Request(key,self.priority,self.power,minimum,self.channels,duration,1e9,
                       omega,self.kind,self.mode,base,gamma,self.efficiency,self.load,self.support)

@dataclass(frozen=True)
class Scenario:
    name: str
    phases: tuple
    hp: float = 1.
    st: float = 1.
    ft: float = 0.  # multiples of will factor
    ns: float = 0.
    state: str = "CONSCIOUS"
    bl: tuple = (0.,0.,0.,0.)

    @property
    def duration(self): return sum(p[0] for p in self.phases)

    def initialize(self,e):
        s=e.state
        s.hp=e.c.hpmax*self.hp
        s.ft=self.ft*(e.c.will/10)**.4
        s.st=self.st*e.c.stmax/(1+s.ft/200)
        s.ns=self.ns
        s.bl=list(self.bl)
        e.transition(self.state)

    def events(self,limit=None):
        """Stable action starts and end times independent of integrator dt."""
        offset=0.
        end=self.duration if limit is None else min(limit,self.duration)
        events={}
        for pi,(length,actions) in enumerate(self.phases):
            for ai,a in enumerate(actions):
                n=0
                while n*a.period<length-1e-9 and offset+n*a.period<end-1e-9:
                    t=round(offset+n*a.period,9)
                    duration=min(a.duration,length-n*a.period)
                    events.setdefault(t,[]).append(a.request(f"{pi}:{ai}:{n}",duration))
                    n+=1
            offset+=length
            if offset>=end-1e-9: break
        return sorted((t,tuple(req)) for t,req in events.items())

def P(seconds,*actions): return seconds,actions
def S(name,seconds,*actions,**kw): return Scenario(name,(P(seconds,*actions),),**kw)

force=Action("force",10)
heavy=Action("strike",100,.5,.25,7,mode="forced",load=1.5)
maximum=Action("force",1000,mode="maximum",load=2.)
light=Action("strike",10,.5,.25,1)
run=Action("run",30,channels=24)
sprint=Action("sprint",100,channels=24,mode="forced")
walk=Action("walk",5,channels=24)
aim=Action("aim",20,channels=1)
block=Action("block",20,channels=2,priority=1)
hold=Action("hold",30,channels=3)
lift=Action("lift",30,2,1.5,7)
carry=Action("carry",30,channels=31)
jump=Action("jump",50,1,.25,24)
rest=P(120)
SCENARIOS=(
 S("short",5,light),
 S("natural",120,Action("force",100)),
 S("forced",120,Action("force",100,mode="forced")),
 S("maximum",120,maximum),
 S("work",120,force),
 S("efficiency",120,Action("force",10,efficiency=1.5)),
 S("recovery",600,st=0,ft=100),
 S("wake",1200,st=0,ft=210,state="UNCONSCIOUS"),
 S("critical_wake",1800,hp=.01,st=0,ft=210,state="UNCONSCIOUS"),
 S("support",120,Action("lift",100,support=2)),
 S("paid_fatigue",5,Action("hold",5,channels=3)),
 S("old_fatigue",120,force,ft=80),
 S("safety",120,Action("force",100,load=2),hp=.06,ft=80,st=.1),
 S("reserve",120,force,st=.02,ft=40),
 S("override",120,maximum,hp=.05,ft=100,st=0),
 S("two_phase",1800,hp=.5,st=0,ft=90,state="UNCONSCIOUS"),
 Scenario("relapse",(P(30),P(120,maximum),P(450)),st=0,ft=170,state="UNCONSCIOUS"),
 S("unconscious_rest",120,st=0,ft=180,state="UNCONSCIOUS"),
 Scenario("cycle",(P(20,heavy),P(10))*10),
 Scenario("long_cycle",(P(30,force),P(30))*10),
 S("single_burst",1,Action("force",1000,1,.25)),
 S("heavy_series",10,heavy),
 S("sustained",120,Action("carry",100)),
 Scenario("alternate",(P(5,heavy),P(5,jump))*12),
 S("attack_walk",120,light,walk),
 Scenario("local_recovery",(P(30,heavy),P(90,walk)),bl=(2.,6.,2.,0.)),
 Scenario("weapon_switch",(P(10,Action("strike",50,.5,.25,1)),P(110,Action("strike",50,.5,.25,2)))),
 S("specialists",120,Action("lift",100,2,1.5,7)),
 S("balanced",120,force,aim,run),
 Scenario("tactical",(P(10,heavy,run),P(10,walk,aim),P(10))*20),
 S("protected_full",60,st=0,ft=180,state="PROTECTED"),
 S("protected_low",60,hp=.01,st=0,ft=180,state="PROTECTED"),
 S("protected_zero_st",60,walk,st=0,ft=150,state="PROTECTED"),
 S("extreme_ft",600,hp=.01,st=0,ft=600,state="UNCONSCIOUS"),
 S("voluntary",60,st=0,ft=180,state="PROTECTED"),
 S("intentional_ko",60,st=0,ft=180,state="UNCONSCIOUS"),
 S("immediate_attack",120,heavy,st=0,ft=180,state="UNCONSCIOUS"),
 S("protected_walk",120,walk,st=.1,ft=140,state="PROTECTED"),
 S("ns_break",60,maximum,ft=200,ns=1),
 Scenario("long_neural_cycle",(P(15,maximum),P(45))*10),
 S("max_single_effort",1,Action("force",1000,1,.5,mode="maximum")),
 S("fixed_absolute",120,force),
 S("lift_fixed_mass",120,lift),
 S("hold",120,hold),
 S("carry_distance",120,carry),
 S("run",120,run),
 S("sprint_series",120,Action("sprint",100,2,.5,24,mode="forced")),
 S("coordination",120,aim),
 S("attack_moving",120,light,run),
 S("attack_defense",120,light,block),
 S("run_hold",120,run,hold),
 Scenario("sprint_heavy",(P(10,sprint),P(20,heavy),P(90))),
 Scenario("priority_switch",(P(10,heavy,block),P(10,Action("strike",100,.5,.25,7,1),block))),
 S("critical_defense",120,heavy,Action("block",20,channels=2,priority=0)),
 S("incompatible",120,light,Action("aim",20,channels=1)),
 S("splitting",120,Action("strike",10,.25,.125,1),Action("strike",10,.25,.125,1)),
 S("instant_repeat",60,Action("strike",100,.1,.025,1,mode="maximum")),
 S("request_order",120,block,light,run),
 S("critical_ft_combined",120,heavy,run,block,hp=.1,st=0,ft=170),
 Scenario("long_complex",(P(10,heavy,run),P(10,hold),P(20,walk),P(20))*10),
)

def scenarios(): return iter(SCENARIOS)
