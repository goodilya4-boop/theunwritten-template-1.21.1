"""Streaming matched sensitivity between two campaign checkpoints."""
import argparse,csv,json,math,sqlite3
from itertools import zip_longest
from pathlib import Path
from sensitivity import KEY,METRICS

FIELDS=("version","scenario","dt_base","dt_other","metric","count","base_mean","other_mean","mean_abs_delta","max_abs_delta","relative_mean_delta")

def compare_databases(base,other,output):
    if Path(output).resolve() in (Path(base).resolve(),Path(other).resolve()): raise ValueError("output must differ from inputs")
    a,b=sqlite3.connect(base),sqlite3.connect(other)
    try:
        for db in (a,b): db.execute("PRAGMA query_only=ON")
        ma,mb=[json.loads(db.execute("SELECT manifest FROM meta WHERE id=1").fetchone()[0]) for db in (a,b)]
        if {k:v for k,v in ma.items() if k!="dt"}!={k:v for k,v in mb.items() if k!="dt"}:
            raise ValueError("unmatched experiment manifests")
        groups={}
        count=0
        for left,right in zip_longest(a.execute("SELECT id,payload FROM results ORDER BY id"),b.execute("SELECT id,payload FROM results ORDER BY id")):
            if left is None or right is None or left[0]!=right[0]: raise ValueError("unmatched committed ids")
            x,y=json.loads(left[1]),json.loads(right[1])
            if any(x[k]!=y[k] for k in KEY): raise ValueError("unmatched simulation keys")
            count+=1
            for m in METRICS:
                v,w=float(x[m]),float(y[m])
                if not math.isfinite(v) or not math.isfinite(w): raise ValueError("nonfinite metric")
                g=(x["version"],x["scenario"],x["dt"],y["dt"],m)
                acc=groups.setdefault(g,[0,0.,0.,0.,0.])
                acc[0]+=1
                n=acc[0]
                acc[1]+=(v-acc[1])/n
                acc[2]+=(w-acc[2])/n
                acc[3]+=(abs(v-w)-acc[3])/n
                acc[4]=max(acc[4],abs(v-w))
        with open(output,"w",newline="",encoding="utf-8") as f:
            writer=csv.DictWriter(f,fieldnames=FIELDS)
            writer.writeheader()
            for g,(n,x,y,abs_mean,abs_max) in sorted(groups.items()):
                writer.writerow(dict(zip(FIELDS[:5],g),count=n,base_mean=x,other_mean=y,mean_abs_delta=abs_mean,max_abs_delta=abs_max,
                                     relative_mean_delta="" if abs(x)<1e-9 else (y-x)/abs(x)))
        return count
    finally:
        a.close()
        b.close()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("baseline")
    p.add_argument("other")
    p.add_argument("--output",default="campaign_sensitivity_v5.csv")
    args=p.parse_args()
    print(f"matched_runs={compare_databases(args.baseline,args.other,args.output)}")

if __name__=="__main__": main()
