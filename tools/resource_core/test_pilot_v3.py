import unittest
from dataclasses import replace
from allocator import Request
from engine import Engine, Character, dual_cost, exhaustion_damage
from scenarios import SCENARIOS, Action, S
from run_pilot import simulate

class PilotV3Tests(unittest.TestCase):
    def test_reference_cost(self):
        for omega in (.25,.5,.85):
            self.assertAlmostEqual(dual_cost(10,omega,1,1),10)

    def test_cost_scales_with_actual_output(self):
        self.assertAlmostEqual(dual_cost(10,.6,.5,.5),4)

    def test_integral_damage_crossing(self):
        self.assertAlmostEqual(exhaustion_damage(45,10,10),.025)
        self.assertAlmostEqual(exhaustion_damage(45,5,5)+exhaustion_damage(50,5,5),.025)

    def test_mechanical_damage(self):
        e=Engine(Character(),4)
        e.step([Request("a",2,10,.001,1,.05,1000,load=4)])
        self.assertGreater(e.last["max_q"],1.5)
        self.assertGreater(e.last["damage"],0)

    def test_natural_mechanical_cap(self):
        e=Engine(Character(),4)
        e.step([Request("a",2,10,.001,1,.05,1000,mode="natural",load=4)])
        self.assertLessEqual(e.last["max_q"],1+1e-8)

    def test_reservation_ends_inside_step(self):
        e=Engine(Character())
        e.step([Request("a",2,5,.01,1,.025,1000)],.1)
        self.assertEqual(len(e.ledger),2)
        self.assertAlmostEqual(e.ledger[0]["dt"],.025)
        self.assertEqual(e.ledger[1]["power"],0)

    def test_reservation_no_extension(self):
        e=Engine(Character())
        r=Request("a",2,5,.01,1,.1,1000)
        e.step([r],.05)
        e.step([r],.05)
        e.step([], .05)
        self.assertEqual(e.last["power"],0)

    def test_conflicting_payload(self):
        e=Engine(Character())
        r=Request("a",2,5,.01,1,.2,1000)
        e.step([r])
        with self.assertRaises(ValueError): e.step([replace(r,power=6)])

    def test_priority_preemption(self):
        e=Engine(Character())
        e.step([Request("a",3,5,.01,1,.5,1000)])
        result=e.step([Request("b",0,5,.01,1,.1,1000)])
        self.assertEqual(set(result),{"b"})
        self.assertNotIn("a",e.reservations)

    def test_absolute_precheck(self):
        e=Engine(Character())
        e.state.ft=210
        e.step([Request("a",2,10,.01,1,.1,1000)])
        self.assertEqual(e.label(),"UNCONSCIOUS")
        self.assertEqual(e.last["work"],0)

    def test_protected_blocks_heavy(self):
        e=Engine(Character(),4)
        e.state.ft=150
        e.transition("PROTECTED")
        e.step([Request("a",2,10,.01,1,.1,1000)])
        self.assertEqual(e.last["work"],0)

    def test_wake_at_critical_hp(self):
        e=Engine(Character())
        e.state.hp=1
        e.state.ft=210
        e.state.st=0
        e.transition("UNCONSCIOUS")
        for _ in range(300):
            e.step([], .05)
            if e.label()=="PROTECTED": break
        self.assertEqual(e.label(),"PROTECTED")
        self.assertLessEqual(e.time,15)

    def test_recovering_chain(self):
        e=Engine(Character())
        e.transition("UNCONSCIOUS")
        labels=set()
        for _ in range(300):
            e.step([], .05)
            labels.add(e.label())
        self.assertTrue({"PROTECTED","RECOVERING","CONSCIOUS"}<=labels)

    def test_dead_no_recovery(self):
        e=Engine(Character())
        e.state.hp=0
        e.state.st=0
        e.step([],1)
        self.assertEqual(e.state.st,0)
        self.assertEqual(e.label(),"DEAD")

    def test_schedule_independent_of_dt(self):
        case=S("walk_test",1,Action("walk",5,.2,.125,24))
        self.assertEqual([t for t,_ in case.events()],[0,.2,.4,.6,.8])
        a=simulate(Character(),7,0,case,.025)
        b=simulate(Character(),7,0,case,.1)
        self.assertAlmostEqual(a["distance"],b["distance"],places=7)

    def test_reverse_order(self):
        case=next(s for s in SCENARIOS if s.name=="request_order")
        a=simulate(Character(),7,1,case,.05,2)
        b=simulate(Character(),7,1,case,.05,2,True)
        self.assertEqual(a,b)

    def test_dexterity_affects_movement(self):
        case=S("run_test",1,Action("run",100,channels=24))
        a=simulate(Character(),4,0,case,.05)
        b=simulate(Character(dexterity=40),4,0,case,.05)
        self.assertGreater(b["distance"],a["distance"])

    def test_distinct_named_scenarios(self):
        self.assertEqual(len(SCENARIOS),60)
        self.assertEqual(len({s.name for s in SCENARIOS}),60)
        self.assertTrue(all(s.duration>0 for s in SCENARIOS))

    def test_rest_no_free_transition_resources(self):
        e=Engine(Character())
        e.state.ft=180
        e.state.st=0
        e.transition("UNCONSCIOUS")
        before=(e.state.hp,e.state.st,e.state.ft,e.state.ns,tuple(e.state.bl))
        e.transition("PROTECTED")
        self.assertEqual(before,(e.state.hp,e.state.st,e.state.ft,e.state.ns,tuple(e.state.bl)))

    def test_st_recovery_delay(self):
        e=Engine(Character())
        e.step([Request("a",2,5,.01,1,.05,1000)],.05)
        e.step([],1)
        self.assertEqual(e.last["recovered"],0)

    def test_completed_event_not_replayed(self):
        e=Engine(Character())
        r=Request("once",2,5,.01,1,.05,1000)
        e.step([r],.05)
        e.step([r],.05)
        self.assertEqual(e.last["power"],0)

    def test_efficiency_bound(self):
        e=Engine(Character())
        with self.assertRaises(ValueError):
            e.step([Request("a",2,10,.01,1,.05,1000,efficiency=1000)])
