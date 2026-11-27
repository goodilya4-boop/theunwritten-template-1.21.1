"""Experimental V7 allocation kernel; not integrated into Minecraft."""
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class Request:
    id: str
    priority: int
    power: float
    minimum: float
    channels: int
    duration: float
    local_limit: float
    omega: float = .6

def cost(r, intensity):
    return r.power * (r.omega * intensity + (1-r.omega)*intensity**2)

def allocate(requests, budget):
    if not math.isfinite(budget) or budget < 0:
        raise ValueError("invalid budget")
    requests = sorted(requests, key=lambda r: (r.priority, r.id))
    if len({r.id for r in requests}) != len(requests):
        raise ValueError("duplicate action id")
    for r in requests:
        if not all(math.isfinite(x) for x in (r.power,r.minimum,r.duration,r.local_limit,r.omega)) or not (r.power>=0 and 0<=r.minimum<=1 and r.duration>0 and r.local_limit>=0 and 0<=r.omega<=1 and 0<=r.priority<=4 and r.channels>=0):
            raise ValueError("invalid request")
    result = {}
    occupied = 0
    for priority in range(5):
        group = [r for r in requests if r.priority == priority]
        while group:
            compatible = []
            mask = occupied
            for r in group:
                if not mask & r.channels:
                    compatible.append(r)
                    mask |= r.channels
            lo, hi = 0., 1.
            for _ in range(48):
                mid = (lo+hi)/2
                if sum(cost(r,mid) for r in compatible)<=budget and all(cost(r,mid)<=r.local_limit for r in compatible):
                    lo=mid
                else:
                    hi=mid
            rejected = {r.id for r in compatible if lo<r.minimum or lo<=1e-12}
            if rejected:
                group = [r for r in group if r.id not in rejected]
                continue
            for r in compatible:
                result[r.id]=(lo,cost(r,lo),r.duration)
                budget=max(0.,budget-cost(r,lo))
                occupied |= r.channels
            break
    return result
