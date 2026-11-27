"""Bounded-memory core verification and Pareto evaluation of campaign DB.

Reads committed records only. SQLite performs grouping on disk; Python holds
one matched context (at most builds * repetitions), not the full matrix.
"""
import argparse,csv,json,math,sqlite3
from itertools import groupby
from pathlib import Path
from pareto import fronts,KEY,OUTPUTS,COSTS
from task_requirements import load_requirements

def core_check(r):
    vals=[float(r[k]) for k in ("hp","st","ft","ns","hpmax","stmax","will_factor","initial_ft","ft_gained","ft_recovered","max_budget_excess","max_active_nfs_overshoot","nfs_violation")]
    if not all(math.isfinite(x) for x in vals): return ["nonfinite"]
    hp,st,ft,ns,hm,sm,w,initial,gained,recovered,budget,overshoot,nfs=vals
    failures=[]
    if hm<=0 or sm<=0 or w<=0 or not (0<=hp<=hm+1e-8 and ft>=0 and 0<=ns<=1 and 0<=st<=sm/(1+ft/200)+1e-8):
        failures.append("resource_bounds")
    if min(initial,gained,recovered,budget,overshoot,nfs)<0: failures.append("negative_ledger")
    if abs(initial+gained-recovered-ft)>1e-6: failures.append("fatigue_ledger")
    if budget>1e-8: failures.append("budget")
    if nfs or overshoot>1e-6*w: failures.append("nfs")
    return failures

def analyze(path,output,pareto_output,requirements=None):
    if len({Path(p).resolve() for p in (path,output,pareto_output)})!=3:
        raise ValueError("input and outputs must be distinct")
    db=sqlite3.connect(path)
    try:
        db.execute("PRAGMA query_only=ON")
        db.execute("PRAGMA temp_store=FILE")
        manifest=json.loads(db.execute("SELECT manifest FROM meta WHERE id=1").fetchone()[0])
        count=steps=bad=0
        errors={}
        examples=[]
        overshoot=0.
        for i,payload in db.execute("SELECT id,payload FROM results ORDER BY id"):
            r=json.loads(payload)
            count+=1
            steps+=r["steps"]
            reasons=core_check(r)
            if not 0<=i<manifest["total"]: reasons.append("id_range")
            elif "scenarios" in manifest:
                config_i,rest=divmod(i,4*len(manifest["scenarios"])*manifest["repeats"])
                version_i,rest=divmod(rest,len(manifest["scenarios"])*manifest["repeats"])
                case_i,seed=divmod(rest,manifest["repeats"])
                expected=tuple(manifest["configs"][config_i])+(4+version_i,manifest["scenarios"][case_i],seed)
                actual=tuple(r[k] for k in ("race","level","build","version","scenario","seed"))
                if actual!=expected or r["dt"]!=manifest["dt"]: reasons.append("identity")
            overshoot=max(overshoot,float(r["max_active_nfs_overshoot"]))
            if reasons:
                bad+=1
                for reason in reasons: errors[reason]=errors.get(reason,0)+1
                if len(examples)<20: examples.append({"id":i,"reasons":reasons})
        expressions=[f"json_extract(payload,'$.{k}')" for k in KEY]
        sql="SELECT payload FROM results ORDER BY "+",".join(expressions)+",id"
        def records():
            for (p,) in db.execute(sql):
                r=json.loads(p)
                yield {k:str(v) for k,v in r.items()}
        group_count=0
        incomplete=0
        pareto_count=0
        fields=KEY+("build","repeats","compared_builds","output_metrics","eligible","min_fraction","requirement_mode","task_floors","pareto","dominated_by")+OUTPUTS+COSTS
        with open(pareto_output,"w",newline="",encoding="utf-8") as f:
            writer=csv.DictWriter(f,fieldnames=fields)
            writer.writeheader()
            for key,group in groupby(records(),lambda r:tuple(r[k] for k in KEY)):
                g=list(group)
                expected={b for race,level,b in manifest["configs"] if race==key[0] and str(level)==key[1]}
                actual={}
                for r in g: actual.setdefault(r["build"],set()).add(int(r["seed"]))
                if set(actual)!=expected or any(v!=set(range(manifest["repeats"])) for v in actual.values()) or len(g)!=len(expected)*manifest["repeats"]:
                    incomplete+=1
                    continue
                group_count+=1
                for r in fronts(g,requirements=requirements):
                    writer.writerow(r)
                    pareto_count+=1
        data=dict(expected=manifest["total"],completed=count,complete=count==manifest["total"] and incomplete==0 and not errors.get("id_range") and not errors.get("identity"),steps=steps,
                  core_failures=bad,errors=errors,examples=examples,max_active_nfs_overshoot=overshoot,
                  matched_groups=group_count,incomplete_groups=incomplete,pareto_rows=pareto_count,
                  scope="Core invariants and matched task Pareto only; not full 24-criterion balance acceptance.")
        Path(output).write_text(json.dumps(data,indent=2),encoding="utf-8")
        return data
    finally:
        db.close()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("database")
    p.add_argument("--output",default="campaign_core_v5.json")
    p.add_argument("--pareto-output",default="campaign_pareto_v5.csv")
    p.add_argument("--requirements")
    a=p.parse_args()
    result=analyze(a.database,a.output,a.pareto_output,load_requirements(a.requirements))
    print(json.dumps(result,indent=2))
    if result["core_failures"]: raise SystemExit(1)

if __name__=="__main__": main()
