"""Profile a representative short pilot with standard-library cProfile."""
import argparse,cProfile,pstats,time
from pathlib import Path
from matrix import configurations
from scenarios import SCENARIOS
from run_pilot import simulate

def workload(seconds,repeats):
    cases=[s for s in SCENARIOS if s.name in ("instant_repeat","fixed_absolute","attack_defense","wake","single_burst","carry_distance","tactical")]
    configs=[x for x in configurations() if x[0]=="human" and x[1]==100 and x[2] in ("STR","CON","DEX","STR_CON")]
    runs=steps=previews=cutoffs=0
    for _,_,_,c,_ in configs:
        for version in (4,5,6,7):
            for case in cases:
                for seed in range(repeats):
                    row=simulate(c,version,seed,case,.05,seconds)
                    runs+=1
                    steps+=row["steps"]
                    previews+=row["preview_calls"]
                    cutoffs+=row["cutoffs"]
    return runs,steps,previews,cutoffs

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seconds",type=float,default=5)
    p.add_argument("--repeats",type=int,default=1)
    p.add_argument("--output",default="profile_v5")
    args=p.parse_args()
    if args.seconds<=0 or args.repeats<1: p.error("positive options required")
    start=time.perf_counter()
    expected=workload(args.seconds,args.repeats)
    unprofiled=time.perf_counter()-start
    profiler=cProfile.Profile()
    actual=profiler.runcall(workload,args.seconds,args.repeats)
    if actual!=expected: raise AssertionError("profiled counters differ")
    profiler.dump_stats(args.output+".prof")
    with open(args.output+".txt","w",encoding="utf-8") as f:
        f.write(f"runs={actual[0]} steps={actual[1]} previews={actual[2]} cutoffs={actual[3]} unprofiled_seconds={unprofiled:.6f} steps_per_second={actual[1]/max(unprofiled,1e-12):.2f}\n\n")
        for order in ("cumulative","tottime"):
            pstats.Stats(profiler,stream=f).strip_dirs().sort_stats(order).print_stats(30)
    print(f"runs={actual[0]} steps={actual[1]} seconds={unprofiled:.3f}")

if __name__=="__main__": main()
