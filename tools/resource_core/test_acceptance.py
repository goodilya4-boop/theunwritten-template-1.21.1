import unittest
from acceptance import evaluate

class AcceptanceTests(unittest.TestCase):
    def test_missing_evidence(self):
        rows=evaluate([])
        self.assertEqual(len(rows),24)
        self.assertEqual([r["id"] for r in rows],list(range(1,25)))
        self.assertTrue(all(r["status"]=="NOT_TESTED" for r in rows))

    def test_invariant_failure(self):
        r=dict(race="human",level="1",build="equal",version="7",scenario="sample",seed="0",dt=".05",duration="1",
               hp="100",hpmax="100",st="101",stmax="100",ft="0",ns="0",initial_ft="0",ft_gained="0",ft_recovered="0",
               max_budget_excess="0",nfs_violation="1")
        result={x["id"]:x for x in evaluate([r])}
        self.assertEqual(result[23]["status"],"FAIL")
        self.assertEqual(result[21]["status"],"FAIL")
        self.assertEqual(result[6]["status"],"NOT_TESTED")
