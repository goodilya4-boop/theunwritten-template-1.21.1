"""Candidate absolute game-unit task floors, independent of competing builds.
Rates apply to the scenario observation duration, not completed action time.
Only explicitly specified tasks are ranked in absolute mode.
"""
import json
from pathlib import Path
DEFAULTS={
 "fixed_absolute":{"work": {"per_second":8}},
 "work":{"work":{"per_second":8}},
 "lift_fixed_mass":{"work":{"per_second":10}},
 "hold":{"hold":{"per_second":15}},
 "carry_distance":{"carry_work":{"per_second":50},"carry_distance":{"per_second":2}},
 "run":{"distance":{"per_second":8}},
 "sprint_series":{"distance":{"per_second":4}},
 "coordination":{"precision":{"per_second":8}},
 "max_single_effort":{"peak_force":{"minimum":10}},
 "single_burst":{"peak_force":{"minimum":10}},
 "attack_defense":{"work":{"per_second":1},"hold":{"per_second":4}},
 "run_hold":{"distance":{"per_second":4},"hold":{"per_second":8}},
}
def load_requirements(path=None):
    if path is None: return DEFAULTS
    return json.loads(Path(path).read_text(encoding="utf-8"))

def floors_for(requirements,scenario,duration):
    if scenario not in requirements: return None
    result={}
    for metric,spec in requirements[scenario].items():
        result[metric]=float(spec.get("minimum",0))+duration*float(spec.get("per_second",0))
    if not result or any(not 0<v<float("inf") for v in result.values()):
        raise ValueError("invalid task floors")
    return result
