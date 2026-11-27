import unittest
from pareto import dominates, fronts
from sensitivity import compare, METRICS

class AnalysisTests(unittest.TestCase):
    def test_pareto(self):
        self.assertTrue(dominates((2,1),(1,1)))
        self.assertFalse(dominates((2,0),(1,1)))
        self.assertFalse(dominates((1,1),(1,1)))

    def test_front_task(self):
        a=dict(race="human",level="1",version="7",scenario="force",dt=".05",duration="1",seed="0",
               work="2",distance="0",precision="0",hold="0",peak_force="2",damage="0",paid="1",ft="1",build="a")
        b=dict(a,build="b",work="1")
        result={r["build"]:r for r in fronts([a,b])}
        self.assertEqual(result["a"]["pareto"],1)
        self.assertEqual(result["b"]["pareto"],0)

    def test_sensitivity(self):
        a=dict.fromkeys(METRICS,"1")
        a.update(version="7",scenario="s",dt=".05")
        b=dict(a,dt=".025",work="2")
        out={r["metric"]:r for r in compare({("a",):a},{("a",):b})}
        self.assertEqual(out["work"]["mean_abs_delta"],1)
        with self.assertRaises(ValueError): list(compare({("a",):a},{}))
