import unittest
from engine import Engine, Character
from allocator import Request

class RegressionTests(unittest.TestCase):
    def test_version_cost(self):
        a,b=Engine(Character(),4),Engine(Character(),5)
        r=Request("a",2,40,.1,1,.05,1000)
        a.step([r])
        b.step([r])
        self.assertNotEqual(a.ledger[-1]["paid"],b.ledger[-1]["paid"])

    def test_shared_budget(self):
        for version in (6,7):
            e=Engine(Character(),version)
            e.step([Request(str(i),2,80,.01,1<<i,.05,1000) for i in range(3)])
            row=e.ledger[-1]
            self.assertLessEqual(row["power"],row["budget"]+1e-8)

    def test_damage(self):
        e=Engine(Character(),4)
        e.state.ft=100
        e.state.st=0
        e.step([Request("a",2,100,.1,1,.05,1000)])
        self.assertLess(e.state.hp,100)

    def test_duplicate(self):
        e=Engine(Character())
        r=Request("a",2,10,.1,1,.05,1000)
        with self.assertRaises(ValueError):
            e.step([r,r])

    def test_work(self):
        e=Engine(Character())
        e.step([Request("a",2,10,.1,1,.05,1000)])
        self.assertGreater(e.ledger[-1]["work"],0)
