"""Descriptive Pareto fronts, separately for each race, level, version and task.

Only compare identical scenario/dt/duration and equal seed sets.
Output metrics are not interchangeable units. No universal build score.
"""
import argparse,csv,math
from collections import defaultdict
from statistics import mean

OUTPUTS=("work","distance","precision","hold","peak_force","carry_work","carry_distance")
COSTS=("damage","paid","ft_gained")
KEY=("race","level","version","scenario","dt","duration")

def dominates(a,b,epsilon=1e-8):
    return all(x>=y-epsilon for x,y in zip(a,b)) and any(x>y+epsilon for x,y in zip(a,b))

def fronts(rows,min_fraction=.5):
    if not 0<=min_fraction<=1: raise ValueError("min_fraction")
    groups=defaultdict(lambda:defaultdict(dict))
    for row in rows:
        key=tuple(row[k] for k in KEY)
        seeds=groups[key][row["build"]]
        if row["seed"] in seeds: raise ValueError("duplicate simulation")
        seeds[row["seed"]]=row
    for key,builds in sorted(groups.items()):
        seed_sets=[set(rows) for rows in builds.values()]
        if any(s!=seed_sets[0] for s in seed_sets): raise ValueError("unmatched seeds")
        avg={name:{k:mean(float(row.get(k,row.get("ft",0) if k=="ft_gained" else 0)) for row in seeds.values()) for k in OUTPUTS+COSTS}
             for name,seeds in builds.items()}
        outputs=[k for k in OUTPUTS if any(v[k]>1e-8 for v in avg.values())]
        # Candidate task-specific floor relative to best observed output in this matched group.
        # Require every relevant output; rest-only groups are not ranked.
        floors={k:min_fraction*max(v[k] for v in avg.values()) for k in outputs}
        eligible={n for n,v in avg.items() if outputs and all(v[k]>=floor-1e-8 for k,floor in floors.items())}
        metrics=outputs+list(COSTS)
        vec={name:tuple(v[k] if k in outputs else -v[k] for k in metrics) for name,v in avg.items()}
        for name,values in sorted(avg.items()):
            others=[n for n in eligible if n!=name and dominates(vec[n],vec[name])] if name in eligible else []
            yield dict(zip(KEY,key),build=name,repeats=len(seed_sets[0]),compared_builds=len(builds),
                       output_metrics=";".join(outputs),eligible=int(name in eligible),min_fraction=min_fraction,
                       task_floors=";".join(f"{k}={v:.9g}" for k,v in floors.items()),
                       pareto="" if not outputs else int(name in eligible and not others),
                       dominated_by=";".join(sorted(others)) if outputs else "",**values)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("input")
    p.add_argument("--output",default="pareto_v4.csv")
    p.add_argument("--min-fraction",type=float,default=.5)
    args=p.parse_args()
    with open(args.input,newline="",encoding="utf-8") as f:
        rows=list(fronts(csv.DictReader(f),args.min_fraction))
    fields=KEY+("build","repeats","compared_builds","output_metrics","eligible","min_fraction","task_floors","pareto","dominated_by")+OUTPUTS+COSTS
    with open(args.output,"w",newline="",encoding="utf-8") as f:
        out=csv.DictWriter(f,fieldnames=fields)
        out.writeheader()
        out.writerows(rows)
    print(f"pareto_rows={len(rows)}")

if __name__=="__main__": main()
