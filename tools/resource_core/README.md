# Resource Core Pilot V3

Experimental Python-only game model for Minecraft 1.21.1 NeoForge; not connected to Java gameplay. No balance coefficients are approved by this implementation.

## Run

From tools/resource_core:

    python -m unittest discover -v
    python run_pilot.py --seconds 5 --output pilot_v3.csv
    python run_pilot.py --seconds 5 --dt 0.025 --output pilot_v3_dt025.csv
    python run_pilot.py --seconds 5 --dt 0.1 --output pilot_v3_dt100.csv
    python sensitivity.py pilot_v3.csv pilot_v3_dt025.csv pilot_v3_dt100.csv
    python run_pilot.py --scenarios wake,critical_wake,two_phase,protected_walk,relapse --seconds 180 --output recovery_v3.csv
    python pareto.py pilot_v3.csv

Default pilot uses 6 human level-100 builds, 60 cases, 4 versions, 2 repeats. --seconds truncates each case, not extends short cases. Without --seconds, use each scenario's original duration. Actual step count includes boundary subdivisions. --full selects 420 configs and 10 repetitions by default; do not run the 1,008,000-case campaign before acceptance of the model.

## Design

- V4: square-root output cost; V5: absolute/relative cost; V6: global and local throughput; V7: priority allocation. All share revised physiology, compatibility, and reservation logic. V4 is a new controlled baseline, not bit-identical to the historical model.
- Requests are output demands, not power. Continuous rates use seconds; discrete profiles convert event cost into a rate over nominal duration. Partial event output is fractional game output, not a fully landed strike.
- IDs are one-shot events; repeated same active event is idempotent and completed IDs cannot restart. Preempted events are canceled, not automatically resumed. Event starts and reservation ends subdivide integration independently of dt. This is not a network replay security protocol.
- Fatigue, HP damage, reserve, BL and neural stabilization are separate. Overload Q uses candidate action tolerance. HP loss integrates a linear within-slice fatigue excess; other quantities still evolve numerically. State transitions happen at slice boundaries.
- Natural/forced previews protect HP and NFS; mixed-mode groups use conservative joint backoff. Maximum bypasses those previews, but all V6/V7 modes currently share the finite budget. This is a conservative pilot choice, not the previously proposed uncapped maximum or 1.25 forced-throughput rule. Efficiency is bounded 1..3 for the pilot. Movement/aim tolerance scaling, profile rates and cancellation minima are candidates.
- Protected state restricts actions to natural walk/aim; no inventory or external effect subsystem. RECOVERING uses time and reserve gates. No HP regeneration or offline progression. External blockers, support and actual in-game interactions are not fully modeled.
- work = integrated force proxy, not SI mechanical work. distance, precision, hold are separate game-unit proxies. fulfilled_seconds measures full requested intensity; scheduled_seconds includes all planned events. Rejected time only counts offered/active requests, not canceled future time. Wake seconds blank means no observed wake. State times integrate start-state durations; transitions quantized to slice boundaries.
- Sensitivity compares paired seeds and physical durations; relative differences near zero are blank. Pareto fronts compare identical task/race/level/version/dt/duration and matched seeds. Costs minimized are paid ST, damage, FT; output metrics are not combined. Fronts with no positive output are blank; a short pilot cannot establish universal balance or certify all 24 criteria.

## Remaining verification

Run the regression suite and CI, inspect wake and relapse trajectories, quantify timestep sensitivity, verify action splitting and priorities, then evaluate the 24 acceptance criteria. The named scenarios are experimental definitions, not independently validated acceptance tests. The analysis scripts load CSV into memory and are meant for pilot-sized data; shard/stream full-campaign analysis before scaling.
