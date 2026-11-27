"""Evidence-based 24-criterion screening, not final balance certification."""
import argparse,csv,json,math,unittest
from collections import defaultdict
from pathlib import Path
from statistics import mean

CRITERIA=(
"STR theoretical and realized peak","CON fixed-demand endurance","DEX movement and coordination",
"Hybrid specialization","No universally dominant build","Race balance","Absolute energy cost",
"High-level viability","Sustainable versus burst throughput","No duplicate strain","No free mastery energy",
"Shared power budget","Request order independence","Action splitting","Event replay","Channel compatibility",
"BL history","Target wake within 15 seconds","No safe-rest relapse","No intentional KO advantage",
"Absolute NFS limit","No free transition resources","Numerical invariants","Time-step convergence")

def load(path):
    with open(path,newline="",encoding="utf-8-sig") as f: return list(csv.DictReader(f))

def num(r,k): return float(r[k])
def groups(rows,keys):
    out=defaultdict(list)
    for r in rows: out[tuple(r[k] for k in keys)].append(r)
    return out

def evaluate(pilot,racial=(),endurance=(),recovery=(),sensitivity=(),pareto=(),passed_tests=()):
    rows=list(pilot)+list(racial)+list(endurance)+list(recovery)
    tests=set(passed_tests)
    report=[dict(id=i+1,criterion=name,status="NOT_TESTED",evidence="No sufficient evidence supplied") for i,name in enumerate(CRITERIA)]
    def set_(i,status,evidence): report[i-1].update(status=status,evidence=evidence)
    def test(i,name,explanation):
        if name in tests: set_(i,"PASS_PILOT",explanation+" (unit test only)")
    if rows:
        bad=[]
        for r in rows:
            hp,st,ft,ns=(num(r,k) for k in ("hp","st","ft","ns"))
            hmax,smax=num(r,"hpmax"),num(r,"stmax")
            if not all(math.isfinite(v) for v in (hp,st,ft,ns,hmax,smax)) or not (
                0<=hp<=hmax+1e-8 and 0<=st<=smax/(1+ft/200)+1e-8 and ft>=0 and 0<=ns<=1
                and abs(num(r,"initial_ft")+num(r,"ft_gained")-num(r,"ft_recovered")-ft)<=1e-6):
                bad.append(r)
        set_(23,"FAIL" if bad else "PASS_PILOT",f"{len(rows)} final-state and fatigue-ledger checks; {len(bad)} violations")
        bad=sum(num(r,"max_budget_excess")>1e-8 for r in rows)
        set_(12,"FAIL" if bad else "PASS_PILOT",f"{len(rows)} aggregate budget checks; {bad} unauthorized exceedances; maximum-mode excess separately allowed")
        bad=sum(num(r,"nfs_violation")>0 for r in rows)
        set_(21,"FAIL" if bad else "PASS_PILOT",f"{len(rows)} runs; {bad} runs with an absolute NFS post-step violation")
        wake=[r for r in recovery if r["scenario"] in ("wake","critical_wake","two_phase") and num(r,"duration")>=15]
        if wake:
            bad=sum(not r["wake_seconds"] or num(r,"wake_seconds")>15 for r in wake)
            set_(18,"FAIL" if bad else "PASS_PILOT",f"{len(wake)} eligible wake runs; {bad} exceeded 15 s or never woke")
            bad=sum(num(r,"ko_events")>0 for r in wake)
            set_(19,"FAIL" if bad else "PASS_PILOT",f"{len(wake)} safe-rest runs; {bad} with new KO events")
        pairs=groups([r for r in rows if r["scenario"]=="max_single_effort" and r["version"]=="7" and int(r["level"])>1],
                     ("race","level","seed","dt","duration"))
        checked=theory_conflict=actual_conflict=0
        for g in pairs.values():
            if len({r["build"] for r in g})<2: continue
            pure=next((r for r in g if r["build"]=="STR"),None)
            if pure is None: continue
            checked+=1
            theory_conflict+=any(num(r,"theoretical_force")>num(pure,"theoretical_force")+1e-8 for r in g)
            actual_conflict+=any(num(r,"peak_force")>num(pure,"peak_force")+1e-8 for r in g)
        if checked: set_(1,"FAIL" if theory_conflict else "CONFLICT" if actual_conflict else "PARTIAL",
                        f"{checked} matched groups; theoretical conflicts {theory_conflict}; realized conflicts {actual_conflict}; criterion distinction requires approval")
        fixed=[r for r in endurance if r["scenario"]=="fixed_absolute" and r["version"]=="7" and num(r,"duration")>=60]
        g=groups(fixed,("race","level","seed","dt","duration"))
        comparisons=[]
        for v in g.values():
            con=next((r for r in v if r["build"]=="CON"),None)
            other=[r for r in v if r["build"]!="CON"]
            if con and other: comparisons.append(num(con,"fulfilled_seconds")>=max(num(r,"fulfilled_seconds") for r in other)-1e-8)
        if comparisons: set_(2,"PARTIAL",f"CON matched or led full-demand time in {sum(comparisons)}/{len(comparisons)} matched long groups; inspect recovery and output")
        dex=[r for r in rows if r["scenario"] in ("sprint_series","coordination") and r["version"]=="7"]
        if dex: set_(3,"PARTIAL",f"{len(dex)} sprint/aim rows; coordination proxy is not dodge accuracy")
        if checked: set_(4,"PARTIAL",f"Hybrid realized force exceeds pure STR in {actual_conflict}/{checked} matched groups")
        if racial:
            races={r["race"] for r in racial}
            set_(6,"PARTIAL",f"{len(racial)} racial rows, {len(races)}/6 races; no approved balance bands")
        if endurance: set_(8,"PARTIAL",f"{len(endurance)} endurance rows; no approved viability targets")
        mode=[r for r in rows if r["version"] in ("6","7")]
        if mode and "test_mode_budgets" in tests:
            set_(9,"PARTIAL",f"Mode limits unit-tested; {sum(num(r,'peak_intentional_excess')>0 for r in mode)} runs with intentional excess; sustained output still requires assessment")
        if mode: set_(10,"PARTIAL","Strain ledger present; source attribution and overlap stress tests not exhaustive")
        pairs=groups([r for r in rows if r["scenario"] in ("voluntary","intentional_ko")],
                     ("race","level","build","version","seed","dt","duration"))
        compared=advantages=0
        for g in pairs.values():
            a=next((r for r in g if r["scenario"]=="voluntary"),None)
            b=next((r for r in g if r["scenario"]=="intentional_ko"),None)
            if a and b:
                compared+=1
                advantages+=num(b,"st")>num(a,"st")+1e-8 or num(b,"ft")<num(a,"ft")-1e-8 or num(b,"hp")>num(a,"hp")+1e-8
        if compared: set_(20,"PARTIAL",f"{compared} matched rest pairs; {advantages} show at least one KO advantage; long cycles still required")
    if pareto:
        eligible=[r for r in pareto if r.get("eligible")=="1"]
        set_(5,"PARTIAL",f"{len(eligible)} eligible task/build rows; no claim of universal non-dominance from finite pilot")
    if sensitivity:
        # Candidate screening tolerance on group means; absolute paired error is also reported.
        finite=[r for r in sensitivity if r.get("relative_mean_delta") not in ("",None) and abs(num(r,"base_mean"))>=1]
        bad=sum(abs(num(r,"relative_mean_delta"))>.05 for r in finite)
        width=max((num(r,"max_crossing_width") for r in rows),default=0.)
        set_(24,"PARTIAL",f"{len(finite)} group metrics with |baseline|>=1; {bad} above provisional 5% mean tolerance; max NFS crossing bracket {width:.6g}s; no final convergence proof")
    test(7,"test_cost_scales_with_actual_output","Absolute/relative cost changes with realized output")
    if "test_efficiency_bound" in tests: set_(11,"PARTIAL","Bounded efficiency unit-tested; mastery system not integrated")
    test(13,"test_reverse_order","Reversed request order reproduces result")
    test(14,"test_splitting_continuous_action","Equivalent continuous event subdivisions preserve cost and output")
    if "test_bl_persists_on_switch" in tests: set_(17,"PARTIAL","Global BL persists on channel switch; local persistence and long cycles still need verification")
    test(15,"test_completed_event_not_replayed","Completed event cannot replay")
    test(16,"test_priority_preemption","Conflicting channel preemption unit-tested")
    test(22,"test_rest_no_free_transition_resources","State transition does not alter resource tuple")
    return report

class RecordingResult(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.passed=[]
    def addSuccess(self,test):
        super().addSuccess(test)
        self.passed.append(test.id().rsplit(".",1)[-1])

def main():
    p=argparse.ArgumentParser()
    p.add_argument("pilot")
    for option in ("racial","endurance","recovery","sensitivity","pareto"): p.add_argument("--"+option)
    p.add_argument("--run-tests",action="store_true")
    p.add_argument("--output",default="acceptance_v4")
    a=p.parse_args()
    passed=[]
    test_ok=None
    if a.run_tests:
        suite=unittest.defaultTestLoader.discover(str(Path(__file__).parent))
        result=unittest.TextTestRunner(verbosity=1,resultclass=RecordingResult).run(suite)
        passed=result.passed
        test_ok=result.wasSuccessful()
    kwargs={k:load(getattr(a,k)) if getattr(a,k) else [] for k in ("racial","endurance","recovery","sensitivity","pareto")}
    report=evaluate(load(a.pilot),passed_tests=passed,**kwargs)
    counts={s:sum(r["status"]==s for r in report) for s in ("PASS_PILOT","PARTIAL","CONFLICT","FAIL","NOT_TESTED")}
    data=dict(scope="Pilot V4 evidence only; not production acceptance",counts=counts,tests_ok=test_ok,criteria=report)
    Path(a.output+".json").write_text(json.dumps(data,indent=2),encoding="utf-8")
    lines=["# Resource Core — Pilot V4 acceptance","",data["scope"],"",str(counts),"","| # | Criterion | Status | Evidence |","|---:|---|---|---|"]
    lines.extend(f"| {r['id']} | {r['criterion']} | {r['status']} | {r['evidence'].replace('|','/')} |" for r in report)
    Path(a.output+".md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(counts)
    if test_ok is False or counts["FAIL"]: raise SystemExit(1)

if __name__=="__main__": main()
