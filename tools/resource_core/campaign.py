"""Resumable deterministic campaign; SQLite is the durable source of truth.
Windows spawn safe. Each completed simulation is committed by the parent only.
"""
import argparse,csv,hashlib,json,math,os,sqlite3,time,platform
from concurrent.futures import ProcessPoolExecutor,wait,FIRST_COMPLETED
from dataclasses import replace
from pathlib import Path
from matrix import configurations
from scenarios import scenarios
from run_pilot import simulate,FIELDS

def fingerprint():
    root=Path(__file__).parent
    h=hashlib.sha256()
    for name in ("engine.py","allocator.py","matrix.py","scenarios.py","run_pilot.py","campaign.py"):
        h.update(name.encode())
        h.update((root/name).read_bytes())
    return h.hexdigest()

def tasks(configs,cases,repeats,dt,seconds):
    i=0
    for race,level,build,c,dex in configs:
        for version in (4,5,6,7):
            for case in cases:
                for seed in range(repeats):
                    yield i,(race,level,build,replace(c,dexterity=dex),version,case,seed,dt,seconds)
                    i+=1

def worker(job):
    i,(race,level,build,c,version,case,seed,dt,seconds)=job
    row=simulate(c,version,seed,case,dt,seconds)
    return i,dict(race=race,level=level,build=build,version=version,scenario=case.name,seed=seed,**row)

def connect(path,manifest):
    db=sqlite3.connect(path,timeout=30)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=FULL")
    db.execute("CREATE TABLE IF NOT EXISTS meta (id INTEGER PRIMARY KEY CHECK(id=1), manifest TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY, payload TEXT NOT NULL)")
    value=json.dumps(manifest,sort_keys=True,separators=(",",":"))
    with db:
        db.execute("INSERT OR IGNORE INTO meta VALUES (1,?)",(value,))
    if db.execute("SELECT manifest FROM meta WHERE id=1").fetchone()[0]!=value:
        db.close()
        raise ValueError("checkpoint manifest mismatch; choose a new database")
    return db

def unfinished(db,jobs):
    # Read a bounded ID window before writing to the same connection.
    block=-1
    done=set()
    for job in jobs:
        i=job[0]
        if i//1024!=block:
            block=i//1024
            done={r[0] for r in db.execute("SELECT id FROM results WHERE id>=? AND id<?",(block*1024,(block+1)*1024))}
        if i not in done: yield job

def save(db,result):
    i,row=result
    payload=json.dumps(row,allow_nan=False,separators=(",",":"),sort_keys=True)
    with db:
        db.execute("INSERT INTO results VALUES (?,?)",(i,payload))

def execute(db,jobs,workers,limit=None):
    if workers<1 or (limit is not None and limit<0): raise ValueError("invalid worker count or limit")
    from itertools import islice
    pending_jobs=unfinished(db,jobs)
    if limit is not None: pending_jobs=islice(pending_jobs,limit)
    count=0
    if workers==1:
        for job in pending_jobs:
            save(db,worker(job))
            count+=1
        return count
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures=set()
        exhausted=False
        while futures or not exhausted:
            while not exhausted and len(futures)<2*workers:
                job=next(pending_jobs,None)
                if job is None: exhausted=True
                else: futures.add(pool.submit(worker,job))
            if not futures: break
            done,futures=wait(futures,return_when=FIRST_COMPLETED)
            for future in done:
                save(db,future.result())
                count+=1
    return count

def export(db,path):
    path=Path(path)
    tmp=path.with_name(path.name+".tmp")
    with tmp.open("w",newline="",encoding="utf-8") as f:
        out=csv.DictWriter(f,fieldnames=FIELDS)
        out.writeheader()
        for (payload,) in db.execute("SELECT payload FROM results ORDER BY id"):
            out.writerow(json.loads(payload))
    os.replace(tmp,path)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--db",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--workers",type=int,default=1)
    p.add_argument("--full",action="store_true")
    p.add_argument("--races",default="human")
    p.add_argument("--levels",default="100")
    p.add_argument("--builds",default="STR,CON,DEX,STR_CON,STR75_CON25,equal")
    p.add_argument("--scenarios")
    p.add_argument("--seconds",type=float)
    p.add_argument("--dt",type=float,default=.05)
    p.add_argument("--repeats",type=int)
    p.add_argument("--limit",type=int,help="stop after this many additional results, for resume tests")
    args=p.parse_args()
    repeats=args.repeats if args.repeats is not None else (10 if args.full else 2)
    if repeats<1 or args.workers<1 or not math.isfinite(args.dt) or args.dt<=0 or (args.seconds is not None and (not math.isfinite(args.seconds) or args.seconds<=0)) or (args.limit is not None and args.limit<0):
        p.error("invalid run options")
    if Path(args.db).resolve()==Path(args.output).resolve(): p.error("database and CSV must differ")
    configs=list(configurations())
    if not args.full:
        configs=[x for x in configs if (args.races=="all" or x[0] in args.races.split(",")) and str(x[1]) in args.levels.split(",") and (args.builds=="all" or x[2] in args.builds.split(","))]
    cases=list(scenarios())
    if args.scenarios:
        names=set(args.scenarios.split(","))
        cases=[s for s in cases if s.name in names]
        if {s.name for s in cases}!=names: p.error("unknown scenarios")
    if not configs or not cases: p.error("empty selection")
    total=len(configs)*len(cases)*4*repeats
    manifest=dict(code=fingerprint(),python=platform.python_version(),configs=[x[:3] for x in configs],scenarios=[s.name for s in cases],repeats=repeats,dt=args.dt,seconds=args.seconds,total=total)
    db=connect(args.db,manifest)
    start=time.perf_counter()
    try:
        count=execute(db,tasks(configs,cases,repeats,args.dt,args.seconds),args.workers,args.limit)
        export(db,args.output)
        done=db.execute("SELECT count(*) FROM results").fetchone()[0]
        print(f"new={count} completed={done}/{total} seconds={time.perf_counter()-start:.3f}")
    finally:
        db.close()

if __name__=="__main__": main()
