# Resource Core Pilot V5

Experimental Python-only game model for Minecraft 1.21.1 NeoForge; no Java gameplay integration. Pilot V5 is the harness generation; V4–V7 remain the four compared variants. No final balance coefficients are approved by this implementation.

## Critical cutoff

Race coefficients, base stats and the mathematical energy-fatigue formula remain unchanged. Active time is shortened at the earliest terminal NFS or HP boundary before committing resources. This applies even to fixed-step runs. Frozen-rate FT is piecewise linear at stamina exhaustion; internal stationary points of NFS are checked, and walking recovery uses a conservative interval bracket. Adaptive mode also subdivides extreme active fatigue changes to approximately 2.5 FT or less per local interval, including submillisecond intervals. This is a local integration tolerance, not a cap on FT. The target active NFS overshoot tolerance is 1e-6 times the will factor; the engine raises on unresolved terminal numerical error. Nonterminal thresholds and stochastic hazard remain numerical approximations; this is not an exact solution of the coupled nonlinear physiology. Initial extreme FT is not clipped.

The V4/V5 square-root/dual cost, V6 shared power, V7 priority allocation, mechanical overload, state recovery and protected restrictions remain the preceding candidates. Maximum-only groups can exceed throughput. Mixed same-priority groups conservatively share restricted limits. Explicit local_limit still applies. No offline progression, HP regeneration, mastery subsystem or external blockers.

CSV now includes active_seconds, peak_active_ft_delta, max_active_nfs_overshoot, max_cutoff_width, cutoffs, preview_calls. Criterion 21 includes active overshoot as well as post-step NFS violations; missing overshoot evidence is partial. NFS event output reports the terminal bracket for upward 210 crossing. For other thresholds interpolation is approximate.

## Verify from tools/resource_core

    python -m unittest discover -v
    python run_pilot.py --scenarios instant_repeat,max_single_effort,single_burst --seconds 5 --output extreme_v5.csv --events-output events_extreme_v5.csv
    python run_pilot.py --scenarios instant_repeat,max_single_effort,single_burst --seconds 5 --dt 0.025 --output extreme_v5_dt025.csv
    python run_pilot.py --scenarios instant_repeat,max_single_effort,single_burst --seconds 5 --dt 0.1 --output extreme_v5_dt100.csv
    python sensitivity.py extreme_v5.csv extreme_v5_dt025.csv extreme_v5_dt100.csv --output sensitivity_extreme_v5.csv

Then full short pilot (2880 runs per step size), racial (6912), recovery (240) and endurance (288):

    python run_pilot.py --seconds 5 --output pilot_v5.csv
    python run_pilot.py --seconds 5 --dt 0.025 --output pilot_v5_dt025.csv
    python run_pilot.py --seconds 5 --dt 0.1 --output pilot_v5_dt100.csv
    python sensitivity.py pilot_v5.csv pilot_v5_dt025.csv pilot_v5_dt100.csv
    python pareto.py pilot_v5.csv --absolute
    python distribution.py pilot_v5.csv --group version,scenario,dt
    python run_pilot.py --races all --levels 1,30,100 --builds equal,STR,CON,DEX,STR_CON,STR75_CON25 --scenarios max_single_effort,fixed_absolute,carry_distance,hold,sprint_series,coordination,attack_defense,single_burst --seconds 5 --output racial_v5.csv
    python run_pilot.py --scenarios wake,critical_wake,two_phase,protected_walk,relapse --seconds 180 --output recovery_v5.csv --events-output events_v5.csv
    python run_pilot.py --scenarios fixed_absolute,sustained,carry_distance,hold,tactical,long_cycle --output endurance_v5.csv
    python acceptance.py pilot_v5.csv --racial racial_v5.csv --endurance endurance_v5.csv --recovery recovery_v5.csv --sensitivity sensitivity_v5.csv --pareto pareto_v5.csv --run-tests
    python profile_pilot.py --seconds 5

The 24-criterion report is still a pilot-scale evidence report, not final balance certification. Profile script compares counters across profiled/unprofiled passes, reports elapsed unprofiled workload and writes pstats. No speedup is assumed. Caches cover immutable character-derived stats, frozen preview rates and scenario events. Actual runtime must be measured.

Absolute task requirements are provisional game-unit floors for 12 representative output tasks, independently of other builds; rates apply to scenario observation duration. Other tasks are unranked in absolute mode. Override via --requirements JSON (metric: {minimum, per_second}). Relative mode remains available for historical comparison. Integrated force, distance, carry_work, precision and hold remain distinct game proxies, not SI units.

## Parallel and resumable campaign

SQLite WAL database is the source of truth. Only the parent writes; each completed run is committed individually. Stable integer IDs encode config/version/scenario/seed. The manifest includes code fingerprint, Python version, ordered matrix, scenarios, dt, duration and repeats. Resume with identical scientific options; worker count, limit and CSV path may differ. Use one runner per database. Interrupted in-flight jobs may be recomputed, committed jobs are skipped. A changed scientific manifest or source fingerprint requires a new DB. --no-export avoids re-exporting all prior rows; --limit 0 exports existing rows. Keep DB and WAL/SHM together if copying a live database; preferably close the runner first.

Small reproducibility example (32 total runs, first 11, then 21):

    python campaign.py --db resume_v5.sqlite --output resume_v5.csv --workers 2 --builds STR,CON --scenarios instant_repeat,fixed_absolute --seconds 5 --repeats 2 --limit 11
    python campaign.py --db resume_v5.sqlite --output resume_v5.csv --workers 2 --builds STR,CON --scenarios instant_repeat,fixed_absolute --seconds 5 --repeats 2
    python campaign.py --db serial_v5.sqlite --output serial_v5.csv --workers 1 --builds STR,CON --scenarios instant_repeat,fixed_absolute --seconds 5 --repeats 2
    python campaign_analysis.py resume_v5.sqlite
    python campaign_sensitivity.py resume_v5.sqlite serial_v5.sqlite

Compare the exported CSV hashes. Reuse an existing DB only if its manifest matches; the small example assumes new databases.

After accepting the model, not before:

    python campaign.py --full --workers 4 --db campaign_v5.sqlite --output campaign_v5.csv --dt 0.05 --no-export
    python campaign.py --full --workers 4 --db campaign_v5.sqlite --output campaign_v5.csv --dt 0.05 --limit 0
    python campaign_analysis.py campaign_v5.sqlite
    python distribution.py campaign_v5.csv --group version,scenario,dt

Full matrix = 420 configs * 60 scenarios * 4 variants * 10 repeats = 1,008,000 runs. No such campaign has been executed by adding this code.

Campaign analysis streams core invariants and matched task Pareto using disk sorting and one context at a time; incomplete groups are not ranked. Campaign sensitivity streams pairs from two databases. Distribution uses a temporary SQLite index for exact interpolated percentiles and extrema; it requires significant scratch disk space (roughly 12 metric rows per simulation plus index). Use --scratch to choose location. Pilot acceptance.py, pareto.py and sensitivity.py still load inputs into memory; do not pass million-row inputs to those pilot-only commands. Streaming core report is not a full streaming implementation of every qualitative 24-criterion judgment.

GitHub Actions runs targeted six-scenario smoke tests, three time steps, distribution, parallel resume, serial CSV equality, core/sensitivity reports, profiling and the pilot acceptance report. It does not execute the full campaign. The wider racial/endurance/recovery matrix remains the local verification protocol.
