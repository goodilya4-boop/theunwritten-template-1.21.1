"""Pilot V5 / full matrix runner with fixed physical events and streaming CSV."""
import argparse,csv,time,math
from contextlib import ExitStack
from dataclasses import replace
from engine import Engine
from matrix import configurations
from scenarios import scenarios

SUMS=("work","distance","precision","hold","damage","paid","recovered","clamp","strain","requested_seconds","fulfilled_seconds","ft_gained","ft_recovered","carry_work","carry_distance","nfs_crossings","nfs_violation","active_seconds")
PEAKS=("bl","nfs","ft","peak_force","max_q")
FIELDS=("race","level","build","version","scenario","seed","dt","duration","hp","st","ft","ns","state","steps",
        *SUMS,*("peak_"+x if x!="peak_force" else x for x in PEAKS),
        "hpmax","stmax","will_factor","max_crossing_width","max_active_nfs_overshoot","max_cutoff_width","cutoffs","preview_calls","initial_ft","theoretical_force","refinements","peak_intentional_excess","peak_natural_power","peak_forced_power","peak_maximum_power","peak_active_ft_delta","scheduled_seconds","rejected_seconds","ko_seconds","protected_seconds","recovering_seconds","ko_events","wake_seconds","max_budget_excess","st_fraction","hp_fraction")

def simulate(c,version,seed,scenario,dt,seconds=None,reverse=False,adaptive=True,event_sink=None):
    e=Engine(c,version,seed,adaptive=adaptive)
    scenario.initialize(e)
    initial_ft=e.state.ft
    theoretical_force=10*(c.strength/10)**.9*(c.constitution/10)**.1
    extra_peaks={k:0. for k in ('intentional_excess','natural_power','forced_power','maximum_power','active_ft_delta')}
    end=scenario.duration if seconds is None else min(seconds,scenario.duration)
    events=scenario.events(end)
    j=steps=0
    sums={k:0. for k in SUMS}
    peaks={k:0. for k in PEAKS}
    peaks.update(bl=max(e.state.bl),ft=e.state.ft,nfs=e.state.ft*(1-.65*e.state.ns))
    scheduled=sum(min(r.duration,end-t) for t,req in events for r in req)
    times={k:0. for k in ("UNCONSCIOUS","PROTECTED","RECOVERING")}
    rejected=excess=cross_width=overshoot=cut_width=0.
    previous=e.label()
    kos=0
    wake=None
    ko_start=0. if previous=="UNCONSCIOUS" else None
    while e.time<end-1e-9:
        req=()
        if j<len(events) and abs(events[j][0]-e.time)<1e-8:
            req=events[j][1]
            j+=1
        next_event=events[j][0] if j<len(events) else end
        stop=min(end,e.time+dt,next_event)
        if stop<=e.time+1e-10: raise RuntimeError("event scheduler stalled")
        e.step(tuple(reversed(req)) if reverse else req,stop-e.time)
        for row in e.ledger:
            steps+=1
            for k in SUMS: sums[k]+=row[k]
            for k in PEAKS: peaks[k]=max(peaks[k],row[k])
            state=row["state"]
            if event_sink is not None:
                for threshold in row["crossed_thresholds"]:
                    actual=threshold*(c.will/10)**.4
                    fraction=(actual-row["nfs_start"])/(row["nfs"]-row["nfs_start"])
                    terminal=threshold==210 and row["terminal_cutoff"]=="UNCONSCIOUS" and row["nfs"]>=actual
                    event_sink(dict(kind="NFS",threshold=threshold,direction="up" if row["nfs"]>row["nfs_start"] else "down",
                                    time_lo=row["time"]-(row["cutoff_width"] if terminal else row["dt"]),time_hi=row["time"],estimate=row["time"] if terminal else row["time"]-row["dt"]+row["dt"]*fraction,
                                    state_from=row["start_state"],state_to=state))
                if previous!=state:
                    event_sink(dict(kind="STATE",threshold="",direction="",time_lo=row["time"]-row["dt"],time_hi=row["time"],estimate="",state_from=previous,state_to=state))
            if row["start_state"] in times: times[row["start_state"]]+=row["dt"]
            if state=="UNCONSCIOUS" and previous!="UNCONSCIOUS":
                kos+=1
                ko_start=row["time"]-row["dt"] if row["start_state"]=="UNCONSCIOUS" else row["time"]
            if previous=="UNCONSCIOUS" and state=="PROTECTED" and wake is None:
                wake=row["time"]-ko_start
            previous=state
            rejected+=row["rejected"]*row["dt"]
            excess=max(excess,row["budget_excess"])
            cross_width=max(cross_width,row["crossing_width"])
            overshoot=max(overshoot,row["active_nfs_overshoot"])
            cut_width=max(cut_width,row["cutoff_width"])
            for k in extra_peaks: extra_peaks[k]=max(extra_peaks[k],row[k])
        e.ledger.clear()
    s=e.state
    return dict(dt=dt,duration=end,hp=s.hp,st=s.st,ft=s.ft,ns=s.ns,state=e.label(),steps=steps,
                **sums,**{("peak_"+k if k!="peak_force" else k):v for k,v in peaks.items()},
                hpmax=c.hpmax,stmax=c.stmax,will_factor=(c.will/10)**.4,max_crossing_width=cross_width,
                initial_ft=initial_ft,theoretical_force=theoretical_force,refinements=e.refinements,
                max_active_nfs_overshoot=overshoot,max_cutoff_width=cut_width,cutoffs=e.cutoffs,preview_calls=e.preview_calls,
                **{"peak_"+k:v for k,v in extra_peaks.items()},scheduled_seconds=scheduled,rejected_seconds=rejected,ko_seconds=times["UNCONSCIOUS"],protected_seconds=times["PROTECTED"],
                recovering_seconds=times["RECOVERING"],ko_events=kos,wake_seconds="" if wake is None else wake,
                max_budget_excess=excess,st_fraction=s.st/c.stmax,hp_fraction=s.hp/c.hpmax)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="pilot_v5.csv")
    p.add_argument("--seconds",type=float,help="truncate each scenario; omit for full duration")
    p.add_argument("--dt",type=float,default=.05)
    p.add_argument("--full",action="store_true",help="all 420 configs, default 10 repetitions")
    p.add_argument("--repeats",type=int)
    p.add_argument("--races",help="comma-separated races or all; default human")
    p.add_argument("--levels",help="comma-separated levels; default 100")
    p.add_argument("--builds",help="comma-separated builds or all")
    p.add_argument("--events-output",help="optional NFS and consciousness event CSV")
    p.add_argument("--fixed-step",action="store_true",help="disable critical refinement")
    p.add_argument("--scenarios",help="comma-separated scenario names")
    p.add_argument("--reverse",action="store_true")
    args=p.parse_args()
    if not math.isfinite(args.dt) or args.dt<=0 or (args.seconds is not None and (not math.isfinite(args.seconds) or args.seconds<=0)):
        p.error("positive finite time required")
    repeats=args.repeats if args.repeats is not None else (10 if args.full else 2)
    if repeats<=0: p.error("positive repeats required")
    configs=list(configurations())
    if not args.full:
        races=None if args.races=="all" else set((args.races or "human").split(","))
        levels=set(map(int,(args.levels or "100").split(",")))
        builds=None if args.builds=="all" else set((args.builds or "STR,CON,DEX,STR_CON,STR75_CON25,equal").split(","))
        configs=[x for x in configs if (races is None or x[0] in races) and x[1] in levels and (builds is None or x[2] in builds)]
    if not configs: p.error("empty configuration selection")
    cases=list(scenarios())
    if args.scenarios:
        names=set(args.scenarios.split(","))
        cases=[s for s in cases if s.name in names]
        if {s.name for s in cases}!=names: p.error("unknown scenario")
    start=time.perf_counter()
    count=steps=0
    with ExitStack() as stack:
        f=stack.enter_context(open(args.output,"w",newline="",encoding="utf-8"))
        event_writer=None
        if args.events_output:
            ef=stack.enter_context(open(args.events_output,"w",newline="",encoding="utf-8"))
            event_writer=csv.DictWriter(ef,fieldnames=("race","level","build","version","scenario","seed","dt","kind","threshold","direction","time_lo","time_hi","estimate","state_from","state_to"))
            event_writer.writeheader()
        out=csv.DictWriter(f,fieldnames=FIELDS)
        out.writeheader()
        for race,level,build,c,dex in configs:
            c=replace(c,dexterity=dex)
            for version in (4,5,6,7):
                for scenario in cases:
                    for seed in range(repeats):
                        key=dict(race=race,level=level,build=build,version=version,scenario=scenario.name,seed=seed)
                        sink=(lambda event:event_writer.writerow(dict(**key,dt=args.dt,**event))) if event_writer else None
                        row=simulate(c,version,seed,scenario,args.dt,args.seconds,args.reverse,not args.fixed_step,sink)
                        out.writerow(dict(**key,**row))
                        count+=1
                        steps+=row["steps"]
            f.flush()
    elapsed=time.perf_counter()-start
    print(f"runs={count} steps={steps} seconds={elapsed:.3f} steps_per_second={steps/max(elapsed,1e-9):.1f}")

if __name__=="__main__": main()
