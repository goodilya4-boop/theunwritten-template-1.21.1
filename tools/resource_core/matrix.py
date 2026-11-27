"""Candidate experiment matrix; coefficients are not final balance."""
from engine import Character
RACES={
"human":(1,1,1,1,1,1,1,1,1),
"elf":(.9,1.1,.9,1.1,1.1,1,.95,.95,1.05),
"dwarf":(1,.9,1.1,1.1,1,.9,1,1,1),
"orc":(1.1,1,1.1,1,1,.9,1,1,.95),
"dragonborn":(1.1,.9,1.1,1,1,1.1,1.1,1.05,1.05),
"voidborn":(1,1,1,1,1,1,1,1,1)}
PROFILES=[(15,20,20,15,15,15),(5,15,10,30,25,15),(10,5,15,35,25,10),(30,20,25,5,15,5),(20,10,20,20,20,10),(1,1,1,1,1,1)]
BUILDS={"equal":(1,1,1,1,1,1),**{name:tuple(int(i==j) for i in range(6)) for j,name in enumerate(("STR","DEX","CON","INT","WIS","CHA"))},"STR_CON":(1,0,1,0,0,0),"STR75_CON25":(3,0,1,0,0,0),"STR25_CON75":(1,0,3,0,0,0),"STR_DEX":(1,1,0,0,0,0),"CON_DEX":(0,1,1,0,0,0),"STR_CON_DEX":(1,1,1,0,0,0)}
def configurations():
    for ri,(race,m) in enumerate(RACES.items()):
        for level in (1,10,30,60,100):
            for name,w in dict(BUILDS,profile=PROFILES[ri]).items():
                p=3*(level-1)
                raw=[p*x/sum(w) for x in w]
                a=[int(x) for x in raw]
                for j in sorted(range(6),key=lambda j:(-(raw[j]-a[j]),j))[:p-sum(a)]:
                    a[j]+=1
                s,d,c,i,w,h=[(10+x)*y for x,y in zip(a,m)]
                char=Character(s,c,w,10*(w/10)**.7*(h/10)**.3,100*(c/10)**.9*m[6],100*(c/10)**.8*(w/10)**.2*m[7])
                yield race,level,name,char,d
