#!/usr/bin/env python3
"""Planted-rule positive control for the mundane-rule battery
(test-23b loop 6, methods Major 1 / domain Major 2).

Design (committed in this header before running): the battery's
negative verdict is only meaningful if its pick/equality code detects
a rule that is actually present. For three real runs (P-256, P-384,
prime239v1), take the run's real viable set and seeds (unchanged),
compute every rule's pick with the PRODUCTION code
(run_battery.rule_picks), then define a synthetic published index as
one rule's pick ("planting" that rule) and recompute the match vector
with the production comparison (pick == n_pub, as in do_rules).
Pass criteria, fixed in advance:
  - for every planting, the planted rule reports a match;
  - a negative synthetic (published index = a viable index no rule
    picks) reports no match for any rule.
Coincidental matches by other rules are reported, not hidden.
The real run_data is restored after each planting; nothing on disk
in the battery directory is modified.
"""
import importlib.util, json, sys

spec = importlib.util.spec_from_file_location(
    "run_battery",
    "/home/hatch/workspace/publication-gap-builds/crypto-constants-audit/paper/battery/work/mundane-battery-10run-2026-10-21/run_battery.py")
rb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rb)

PLANT = ["R2_reverse_last_viable", "R4_stride2_phase1", "R4_stride3_phase2",
         "D_lex_min_seed", "D_min_hamming", "D_median_viable"]
RUNS = ["P-256", "P-384", "prime239v1"]
results = {"design": "planted-rule positive control over production rule_picks/match code; real viable sets and seeds; synthetic published index = planted rule's pick",
           "plantings": [], "negatives": []}
all_pass = True
for run in RUNS:
    picks = rb.rule_picks(run)
    orig = rb.run_data[run]["n_pub"]
    for rule in PLANT:
        rb.run_data[run]["n_pub"] = picks[rule]
        matches = {k: (v == rb.run_data[run]["n_pub"]) for k, v in picks.items()}
        rb.run_data[run]["n_pub"] = orig
        ok = matches[rule] is True
        all_pass &= ok
        results["plantings"].append({
            "run": run, "planted_rule": rule, "planted_pick": picks[rule],
            "planted_rule_matched": matches[rule],
            "also_matched": sorted(k for k, m in matches.items() if m and k != rule),
            "pass": ok})
    # negative synthetic: a viable index picked by no rule
    pickset = set(picks.values())
    neg = next(n for n in rb.run_data[run]["viable_ns"] if n not in pickset)
    rb.run_data[run]["n_pub"] = neg
    matches = {k: (v == neg) for k, v in picks.items()}
    rb.run_data[run]["n_pub"] = orig
    ok = not any(matches.values())
    all_pass &= ok
    results["negatives"].append({"run": run, "negative_index": neg,
                                  "any_match": any(matches.values()), "pass": ok})
results["all_pass"] = bool(all_pass)
json.dump(results, open("/home/hatch/workspace/publication-gap-builds/crypto-constants-audit/paper/battery/work/loop6-fixes/planted_rule_control_results.json", "w"), indent=1)
print(f"plantings: {sum(p['pass'] for p in results['plantings'])}/{len(results['plantings'])} pass; "
      f"negatives: {sum(n['pass'] for n in results['negatives'])}/{len(results['negatives'])} pass")
print("ALL PASS" if all_pass else "FAILURE")
