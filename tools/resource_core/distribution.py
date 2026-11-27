"""Disk-backed exact descriptive quantiles for a large campaign CSV.

Memory is bounded by the insert batch and one aggregate group; SQLite sorts
values on disk. Quantiles use linear interpolation of order statistics.
"""
import argparse,csv,math,sqlite3,tempfile
from pathlib import Path
from statistics import mean

METRICS=("ft_gained","strain","damage","work","distance","precision","hold","carry_work","paid",
         "peak_force","max_active_nfs_overshoot","active_seconds")
KEY=("race","level","version","scenario","build","dt","duration")

def summarize(input_path,output_path,scratch=None,group_keys=KEY):
    if not group_keys or len(set(group_keys))!=len(group_keys) or any(k not in KEY for k in group_keys):
        raise ValueError("invalid grouping keys")
    if Path(input_path).resolve()==Path(output_path).resolve(): raise ValueError("input and output must differ")
    with tempfile.TemporaryDirectory(dir=scratch) as root:
        db=sqlite3.connect(str(Path(root)/"stats.db"))
        try:
            db.execute("PRAGMA temp_store=FILE")
            db.execute("CREATE TABLE vals (g TEXT NOT NULL, metric TEXT NOT NULL, value REAL NOT NULL)")
            import json
            batch=[]
            count=0
            with open(input_path,newline="",encoding="utf-8-sig") as f:
                for r in csv.DictReader(f):
                    g=json.dumps([r[k] for k in group_keys],separators=(",",":"))
                    for m in METRICS:
                        v=float(r[m])
                        if not math.isfinite(v): raise ValueError(f"nonfinite {m}")
                        batch.append((g,m,v))
                    count+=1
                    if len(batch)>=12000:
                        with db: db.executemany("INSERT INTO vals VALUES (?,?,?)",batch)
                        batch.clear()
            if batch:
                with db: db.executemany("INSERT INTO vals VALUES (?,?,?)",batch)
            db.execute("CREATE INDEX metric_order ON vals(g,metric,value)")
            with open(output_path,"w",newline="",encoding="utf-8") as f:
                out=csv.DictWriter(f,fieldnames=tuple(group_keys)+("metric","n","mean","min","p50","p90","p95","p99","max"))
                out.writeheader()
                for g,m,n,avg,minimum,maximum in db.execute("SELECT g,metric,count(*),avg(value),min(value),max(value) FROM vals GROUP BY g,metric"):
                    def quantile(p):
                        pos=(n-1)*p
                        lo=int(pos)
                        rows=list(db.execute("SELECT value FROM vals WHERE g=? AND metric=? ORDER BY value LIMIT 2 OFFSET ?",(g,m,lo)))
                        a=rows[0][0]
                        b=rows[-1][0]
                        return a+(b-a)*(pos-lo)
                    out.writerow(dict(zip(group_keys,json.loads(g)),metric=m,n=n,mean=avg,min=minimum,max=maximum,
                                      **{f"p{int(p*100)}":quantile(p) for p in (.5,.9,.95,.99)}))
            return count
        finally:
            db.close()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("input")
    p.add_argument("--output",default="distribution_v5.csv")
    p.add_argument("--scratch",help="directory for temporary SQLite storage")
    p.add_argument("--group",default=",".join(KEY),help="comma-separated grouping keys")
    args=p.parse_args()
    print(f"input_rows={summarize(args.input,args.output,args.scratch,tuple(args.group.split(",")))}")

if __name__=="__main__": main()
