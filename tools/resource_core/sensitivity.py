"""Matched sensitivity comparison: same scenarios, seeds and physical duration."""
import argparse,csv,math
from collections import defaultdict
from statistics import mean

KEY=("race","level","build","version","scenario","seed","duration")
METRICS=("work","distance","precision","hold","peak_force","fulfilled_seconds","paid","damage","ft","hp_fraction","st_fraction","ko_seconds","protected_seconds","recovering_seconds","carry_work","carry_distance","ft_gained","ft_recovered","strain","active_seconds","max_active_nfs_overshoot","peak_active_ft_delta")

def load(path):
    with open(path,newline="",encoding="utf-8") as f:
        rows={}
        for row in csv.DictReader(f):
            key=tuple(row[k] for k in KEY)
            if key in rows: raise ValueError(f"duplicate key: {key}")
            rows[key]=row
    return rows

def compare(base,other):
    if base.keys()!=other.keys(): raise ValueError("unmatched simulation keys")
    groups=defaultdict(list)
    for key in base:
        a,b=base[key],other[key]
        for metric in METRICS:
            x,y=float(a[metric]),float(b[metric])
            if not math.isfinite(x) or not math.isfinite(y): raise ValueError("nonfinite metric")
            groups[(a["version"],a["scenario"],a["dt"],b["dt"],metric)].append((x,y))
    for (version,scenario,dt_base,dt_other,metric),pairs in sorted(groups.items()):
        x=mean(a for a,b in pairs)
        y=mean(b for a,b in pairs)
        yield dict(version=version,scenario=scenario,dt_base=dt_base,dt_other=dt_other,metric=metric,
                   count=len(pairs),base_mean=x,other_mean=y,mean_abs_delta=mean(abs(a-b) for a,b in pairs),
                   max_abs_delta=max(abs(a-b) for a,b in pairs),relative_mean_delta="" if abs(x)<1e-9 else (y-x)/abs(x))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("baseline")
    p.add_argument("other",nargs="+")
    p.add_argument("--output",default="sensitivity_v5.csv")
    args=p.parse_args()
    base=load(args.baseline)
    with open(args.output,"w",newline="",encoding="utf-8") as f:
        out=csv.DictWriter(f,fieldnames=("version","scenario","dt_base","dt_other","metric","count","base_mean","other_mean","mean_abs_delta","max_abs_delta","relative_mean_delta"))
        out.writeheader()
        for path in args.other: out.writerows(compare(base,load(path)))

if __name__=="__main__": main()
