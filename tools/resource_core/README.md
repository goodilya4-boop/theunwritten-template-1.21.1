# Resource Core Pilot V4

Experimental Python-only game model for Minecraft 1.21.1 NeoForge; not connected to Java gameplay. No balance coefficients are approved by this implementation. Pilot V4 is a generation of the test harness; V4–V7 remain the four compared model variants.

## Verification

Run from tools/resource_core, on feature/resource-core:

    python -m unittest discover -v
    python run_pilot.py --seconds 5 --dt 0.05 --output pilot_v4.csv
    python run_pilot.py --seconds 5 --dt 0.025 --output pilot_v4_dt025.csv
    python run_pilot.py --seconds 5 --dt 0.1 --output pilot_v4_dt100.csv
    python sensitivity.py pilot_v4.csv pilot_v4_dt025.csv pilot_v4_dt100.csv
    python pareto.py pilot_v4.csv --min-fraction 0.5
    python run_pilot.py --races all --levels 1,30,100 --builds equal,STR,CON,DEX,STR_CON,STR75_CON25 --scenarios max_single_effort,fixed_absolute,carry_distance,hold,sprint_series,coordination,attack_defense,single_burst --seconds 5 --output racial_v4.csv
    python run_pilot.py --scenarios wake,critical_wake,two_phase,protected_walk,relapse --seconds 180 --output recovery_v4.csv --events-output events_v4.csv
    python run_pilot.py --scenarios fixed_absolute,sustained,carry_distance,hold,tactical,long_cycle --output endurance_v4.csv
    python acceptance.py pilot_v4.csv --racial racial_v4.csv --endurance endurance_v4.csv --recovery recovery_v4.csv --sensitivity sensitivity_v4.csv --pareto pareto_v4.csv --run-tests

Expected case counts, not measured here: 2880 per short pilot, 6912 racial, 240 recovery, 288 endurance. Actual integration step count includes event boundaries and adaptive refinement. --full selects all 420 configs and 10 repetitions by default; do not launch the million-case experiment until model acceptance.

## Changes and decisions

- No changes to race coefficients or base attribute formulas in matrix.py. V4 square-root and V5+ dual energy-cost formulas remain the existing candidates. V6 uses shared throughput; V7 adds priority allocation.
- Natural actions have burst throughput; forced actions may use 125%; maximum-only groups may exceed throughput but still respect explicit per-action local_limit. Higher-priority spending consumes shared throughput even if maximum. Mixed same-priority groups conservatively share the restricted limit. All spending contributes to fatigue. Protected actions use sustainable throughput.
- Adaptive integration halves proposed intervals before commit on threshold crossings, impending hazard exhaustion or death, or rapid fatigue/damage/near-risk active load. Candidate min_slice=0.001 s; crossing brackets generally no wider than 0.002 s when refinement is enabled. The bracket is the observation interval, not a mathematically exact root. --fixed-step disables refinement but not event-boundary splits. Time estimates are linear interpolation inside brackets.
- initial_ft + ft_gained - ft_recovered = final ft; earned fatigue is not net fatigue. Intentional maximum-mode excess is separate from unauthorized restricted budget excess.
- Theoretical force is the base derived statistic; peak_force is realized force proxy. Distinguish the two when evaluating STR specialization; no change to the criterion without approval.
- carry_work is supported-load output multiplied by distance proxy; carry_distance uses functional speed and achieved action intensity. It is not SI work or a fully modeled mass/velocity interaction. Separate movement, aim, hold and strike metrics remain game proxies.
- Task eligibility currently requires each relevant output to reach 50% of the best observed output within the matched context. This is a provisional relative screen, not an approved absolute task threshold. Rest-only groups are unranked. Use --min-fraction for sensitivity.
- Recovery and state transitions still occur at integration boundaries. No offline progression, HP regeneration, external blockers or Minecraft action integration. Replayed completed event IDs cannot restart. Preemption cancels the action; partial discrete output is a fractional proxy.
- Acceptance outputs 24 criteria with PASS_PILOT, PARTIAL, CONFLICT, FAIL, NOT_TESTED. Missing evidence is not a pass. Unit-test evidence is explicit; criteria with design disagreements remain unresolved. Provisional 5% mean sensitivity screen excludes near-zero denominators and is not final numerical acceptance. Reports deduplicate identical runs across files. The analysis scripts load input in memory; shard or stream the full campaign before scaling.

GitHub Actions runs a shorter endurance subset (four 120-second cases), three short pilots, racial/recovery pilot, sensitivity, Pareto and acceptance reports; artifacts are uploaded even on failure. Local long endurance adds tactical and long_cycle. Passing this pipeline is not final game balance certification.
