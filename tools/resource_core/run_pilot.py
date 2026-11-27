"""Smoke benchmark of the existing kernel, not acceptance validation."""
import argparse,csv,time
from engine import Engine
from allocator import Request
from matrix import configurations

def scenarios():
    # Factorial workload screen: 5 powers x 4 channel patterns x 3 duty cycles.
    for power in (5,10,20,40,80):
        for pattern in ((1,),(1,2),(1,1),(4,16)):
            for duty in (1,2,4):
                yield power,pattern,duty

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="pilot.csv")
    p.add_argument("--seconds",type=float,default=5)
    p.add_argument("--dt",type=float,default=.05)
    args=p.parse_args()
    if args.seconds<=0 or args.dt<=0: p.error("positive time required")
    configs=[x for x in configurations() if x[0]=="human" and x[1]==100 and x[2] in ("STR","CON","DEX","STR_CON","STR75_CON25","equal")]
    start=time.perf_counter()
    count=steps=0
    with open(args.output,"w",newline="",encoding="utf-8") as f:
        out=csv.writer(f)
        out.writerow(["race","level","build","version","scenario","seed","hp","st","ft","ns","steps","work","damage","rejected","peak_bl","peak_nfs","ko_steps","protected_steps","recovering_steps","max_budget_excess"])
        for race,level,build,c,dex in configs:
            for version in (4,5,6,7):
                for sid,(power,pattern,duty) in enumerate(scenarios()):
                    for seed in (0,1):
                        e=Engine(c,version,seed)
                        n=round(args.seconds/args.dt)
                        for tick in range(n):
                            req=[Request(str(j),j+1,power,.1,ch,args.dt,1000) for j,ch in enumerate(pattern)] if tick%duty==0 else []
                            e.step(req,args.dt)
                        s=e.state
                        out.writerow([race,level,build,version,sid,seed,s.hp,s.st,s.ft,s.ns,n,sum(x["work"] for x in e.ledger),sum(x["damage"] for x in e.ledger),sum(x["rejected"] for x in e.ledger),max((x["bl"] for x in e.ledger),default=0),max((x["nfs"] for x in e.ledger),default=0),sum(x["unconscious"] for x in e.ledger),sum(x["protected"] for x in e.ledger),sum(x["recovering"] for x in e.ledger),max((max(0,x["power"]-x["budget"]) for x in e.ledger),default=0)])
                        count+=1
                        steps+=n
    elapsed=time.perf_counter()-start
    print(f"runs={count} steps={steps} seconds={elapsed:.3f} steps_per_second={steps/max(elapsed,1e-9):.1f}")

if __name__=="__main__": main()
