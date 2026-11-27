import unittest
from matrix import configurations
from run_pilot import scenarios

class MatrixTests(unittest.TestCase):
    def test_configurations(self):
        rows=list(configurations())
        self.assertEqual(len(rows),420)
        self.assertEqual(len({x[:3] for x in rows}),420)
        self.assertTrue(all(x[3].hpmax>0 and x[3].stmax>0 for x in rows))
    def test_scenarios(self):
        rows=list(scenarios())
        self.assertEqual(len(rows),60)
        self.assertEqual(len(set(rows)),60)
