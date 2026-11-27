import unittest
from allocator import Request, allocate
from engine import Engine, Character

def request(key="a", priority=2, channels=1, power=20):
    return Request(key, priority, power, .1, channels, .4, 100)

class ResourceTests(unittest.TestCase):
    def test_order(self):
        a,b=request(),request("b",3,2)
        self.assertEqual(allocate([a,b],25),allocate([b,a],25))

    def test_budget(self):
        result=allocate([request(),request("b",2,2)],25)
        self.assertLessEqual(sum(x[1] for x in result.values()),25+1e-8)

    def test_conflict(self):
        self.assertEqual(len(allocate([request(),request("b")],100)),1)

    def test_reservation(self):
        e=Engine(Character())
        e.step([request()])
        self.assertIn("a",e.step())

    def test_ledger(self):
        e=Engine(Character())
        for _ in range(100):
            e.step([request()])
        for r in e.ledger:
            self.assertAlmostEqual(r["before"]-r["paid"]+r["recovered"]-r["clamp"],r["after"])

    def test_seed(self):
        a,b=Engine(Character(),seed=42),Engine(Character(),seed=42)
        for _ in range(100):
            a.step([request()])
            b.step([request()])
        self.assertEqual(a.ledger,b.ledger)

if __name__=="__main__":
    unittest.main()
