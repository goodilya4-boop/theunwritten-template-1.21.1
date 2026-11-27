import csv
import tempfile
import unittest
from pathlib import Path
from allocator import Request
from engine import Engine, Character
from matrix import configurations
from scenarios import S, Action, SCENARIOS
from run_pilot import simulate
from campaign import connect,execute,tasks,export
from campaign_analysis import analyze,core_check
from distribution import summarize,METRICS,KEY
from pareto import fronts
from task_requirements import floors_for
from acceptance import evaluate

class PilotV5Tests(unittest.TestCase):
    def test_instant_repeat_str(self):
        c=next(x[3] for x in configurations() if x[:3]==("human",100,"STR"))
        case=next(s for s in SCENARIOS if s.name=="instant_repeat")
        for version in (6,7):
            for dt in (.025,.05,.1):
                row=simulate(c,version,0,case,dt,5)
                self.assertGreater(row["cutoffs"],0)
                self.assertLessEqual(row["max_active_nfs_overshoot"],1e-6*row["will_factor"])
                self.assertLessEqual(row["peak_nfs"],210*row["will_factor"]+1e-5)
                self.assertLess(row["ft_gained"],220)
                self.assertEqual(row["nfs_violation"],0)

    def test_terminal_submillisecond(self):
        e=Engine(Character(),7,adaptive=False)
        e.step([Request("max",2,10,.001,1,.1,1e9,base=1000)],.1)
        active=[r for r in e.ledger if r["active_seconds"]>0]
        self.assertEqual(len(active),1)
        self.assertEqual(active[0]["terminal_cutoff"],"UNCONSCIOUS")
        self.assertLess(active[0]["dt"],.001)
        self.assertLessEqual(active[0]["active_nfs_overshoot"],1e-6)
        self.assertAlmostEqual(e.time,.1)
        self.assertEqual(e.label(),"UNCONSCIOUS")
        self.assertFalse(e.reservations)

    def test_terminal_cost_uses_only_executed_time(self):
        e=Engine(Character(),7,adaptive=False)
        e.step([Request("max",2,10,.001,1,.1,1e9,base=1000)],.1)
        row=e.ledger[0]
        self.assertAlmostEqual(row["paid"],row["power"]*row["dt"])
        self.assertAlmostEqual(row["work"],10*row["dt"])
        self.assertAlmostEqual(row["strain"],.05*row["paid"]*max(0,row["power"]/row["sustainable"]-1)**2)
        self.assertTrue(all(r["paid"]==0 and r["work"]==0 for r in e.ledger[1:]))

    def test_terminal_even_with_fixed_step(self):
        case=S("extreme",.1,Action("strike",100,.1,.025,1,mode="maximum"))
        c=Character(strength=307)
        a=simulate(c,7,0,case,.1,adaptive=False)
        b=simulate(c,7,0,case,.025,adaptive=False)
        self.assertLessEqual(a["max_active_nfs_overshoot"],1e-6)
        self.assertAlmostEqual(a["work"],b["work"],places=7)

    def test_discrete_cost_not_recharged_on_substeps(self):
        case=S("strike",.25,Action("strike",5,1,.25,1))
        a=simulate(Character(),5,0,case,.025,adaptive=False)
        b=simulate(Character(),5,0,case,.05,adaptive=False)
        self.assertAlmostEqual(a["scheduled_seconds"],b["scheduled_seconds"])
        self.assertAlmostEqual(a["paid"],b["paid"],delta=.02)

    def test_absolute_task_floor(self):
        r=dict(race="human",level="1",version="7",scenario="fixed_absolute",dt=".05",duration="1",seed="0",
               work="7",distance="0",precision="0",hold="0",peak_force="7",carry_work="0",carry_distance="0",damage="0",paid="0",ft_gained="0",build="a")
        result=list(fronts([r],requirements={"fixed_absolute":{"work":{"per_second":8}}}))[0]
        self.assertEqual(result["eligible"],0)
        self.assertEqual(result["pareto"],0)
        self.assertEqual(floors_for({"fixed_absolute":{"work":{"per_second":8}}},"fixed_absolute",2),{"work":16})

    def test_overshoot_report_failure(self):
        c=Character()
        row=simulate(c,7,0,S("rest",.1),.05)
        row.update(race="human",level="1",build="equal",version="7",scenario="rest",seed="0")
        row["max_active_nfs_overshoot"]=1.
        self.assertIn("nfs",core_check(row))
        report=evaluate([row])
        self.assertEqual(report[20]["status"],"FAIL")

    def test_checkpoint_resume_and_parallel(self):
        configs=[next(x for x in configurations() if x[:3]==("human",1,"equal"))]
        cases=[S("rest",.1)]
        manifest=dict(total=4,configs=[x[:3] for x in configs],repeats=1)
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)
            a=connect(p/"a.db",manifest)
            self.assertEqual(execute(a,tasks(configs,cases,1,.05,None),1,2),2)
            a.close()
            a=connect(p/"a.db",manifest)
            self.assertEqual(execute(a,tasks(configs,cases,1,.05,None),2),2)
            self.assertEqual(execute(a,tasks(configs,cases,1,.05,None),1),0)
            export(a,p/"a.csv")
            a.close()
            b=connect(p/"b.db",manifest)
            self.assertEqual(execute(b,tasks(configs,cases,1,.05,None),1),4)
            export(b,p/"b.csv")
            b.close()
            self.assertEqual((p/"a.csv").read_bytes(),(p/"b.csv").read_bytes())
            with self.assertRaises(ValueError): connect(p/"a.db",dict(manifest,total=5))
            result=analyze(p/"a.db",p/"core.json",p/"pareto.csv")
            self.assertTrue(result["complete"])
            self.assertEqual(result["core_failures"],0)

    def test_distribution_quantiles(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)
            with (p/"in.csv").open("w",newline="",encoding="utf-8") as f:
                out=csv.DictWriter(f,fieldnames=KEY+METRICS)
                out.writeheader()
                for x in (0,10,20):
                    out.writerow(dict({k:"a" for k in KEY},**{m:x for m in METRICS}))
            self.assertEqual(summarize(p/"in.csv",p/"out.csv"),3)
            with (p/"out.csv").open(newline="",encoding="utf-8") as f:
                row=next(csv.DictReader(f))
            self.assertEqual(float(row["p50"]),10)
            self.assertAlmostEqual(float(row["p95"]),19)
