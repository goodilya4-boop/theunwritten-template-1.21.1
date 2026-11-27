import unittest
from dataclasses import replace
from allocator import Request
from engine import Engine, Character
from matrix import configurations, RACES
from scenarios import S, Action
from run_pilot import simulate

class PilotV4Tests(unittest.TestCase):
    def test_mode_budgets(self):
        for version in (6,7):
            rows={}
            for mode in ("natural","forced","maximum"):
                e=Engine(Character(),version,adaptive=False)
                e.step([Request("a",2,10,.001,1,.05,1e9,mode=mode,base=100)],.05)
                rows[mode]=e.last
            self.assertLessEqual(rows["natural"]["power"],rows["natural"]["burst"]+1e-8)
            self.assertLessEqual(rows["forced"]["power"],1.25*rows["forced"]["burst"]+1e-8)
            self.assertGreater(rows["maximum"]["intentional_excess"],0)
            self.assertGreater(rows["forced"]["power"],rows["natural"]["power"])
            self.assertTrue(all(r["budget_excess"]<1e-8 for r in rows.values()))

    def test_critical_refinement(self):
        e=Engine(Character(),7)
        e.state.ft=209
        e.state.st=0
        e.step([Request("a",2,10,.001,1,.1,1e9,base=1e5)],.1)
        self.assertGreater(e.refinements,0)
        self.assertAlmostEqual(e.time,.1)
        self.assertTrue(all(r["nfs_violation"]==0 for r in e.ledger))
        self.assertLessEqual(max(r["crossing_width"] for r in e.ledger),.002000001)

    def test_fatigue_ledger(self):
        e=Engine(Character(),4)
        e.state.ft=20
        e.step([Request("a",2,10,.001,1,.05,1e9)],.05)
        e.step([],1)
        self.assertAlmostEqual(20+sum(r["ft_gained"]-r["ft_recovered"] for r in e.ledger),e.state.ft)

    def test_carry_separate(self):
        case=S("carry_test",1,Action("carry",5,channels=31))
        row=simulate(Character(),7,0,case,.05)
        self.assertGreater(row["carry_work"],0)
        self.assertGreater(row["carry_distance"],0)
        self.assertEqual(row["work"],0)
        self.assertEqual(row["peak_force"],0)

    def test_theoretical_force(self):
        case=S("force_test",1,Action("force",1000,mode="maximum"))
        c=Character(strength=40)
        row=simulate(c,7,0,case,.05)
        self.assertAlmostEqual(row["theoretical_force"],10*4**.9)
        self.assertLessEqual(row["peak_force"],row["theoretical_force"]+1e-8)

    def test_racial_matrix(self):
        configs=list(configurations())
        self.assertEqual(len(configs),420)
        self.assertEqual({r for r,*_ in configs},set(RACES))
        for race in RACES:
            self.assertEqual(sum(r==race for r,*_ in configs),70)

    def test_adaptive_rest_threshold(self):
        e=Engine(Character(),7)
        e.state.ft=210
        e.state.st=0
        e.transition("UNCONSCIOUS")
        e.step([],1)
        crossings=[r for r in e.ledger if r["nfs_crossings"]]
        self.assertTrue(crossings)
        self.assertLessEqual(max(r["crossing_width"] for r in crossings),.002000001)

    def test_splitting_continuous_action(self):
        a=S("whole",1,Action("hold",5,1,1,3))
        b=S("split",1,Action("hold",5,.25,.25,3))
        x=simulate(Character(),7,0,a,.05)
        y=simulate(Character(),7,0,b,.05)
        for k in ("paid","hold","ft_gained","ft"):
            self.assertAlmostEqual(x[k],y[k],places=7)

    def test_bl_persists_on_switch(self):
        e=Engine(Character(),4)
        e.step([Request("left",2,5,.001,1,.05,1e9)],.05)
        before=e.state.bl[0]
        self.assertGreater(before,0)
        e.step([Request("right",2,5,.001,2,.05,1e9)],.05)
        self.assertGreater(e.state.bl[0],before)

    def test_maximum_consumes_priority_pool(self):
        e=Engine(Character(),7,adaptive=False)
        high=Request("high",0,10,.001,1,.05,1e9,base=100)
        low=Request("low",3,10,.01,2,.05,1e9,mode="natural")
        result=e.step([low,high],.05)
        self.assertIn("high",result)
        self.assertNotIn("low",result)
        self.assertGreater(e.last["intentional_excess"],0)

    def test_crossing_event_log(self):
        case=S("wake_test",1,ft=210,st=0,state="UNCONSCIOUS")
        events=[]
        row=simulate(Character(),7,0,case,.1,event_sink=events.append)
        crossings=[r for r in events if r["kind"]=="NFS"]
        self.assertTrue(crossings)
        for r in crossings:
            self.assertLessEqual(r["time_lo"]-1e-10,r["estimate"])
            self.assertLessEqual(r["estimate"],r["time_hi"]+1e-10)
        self.assertEqual(len(crossings),row["nfs_crossings"])
