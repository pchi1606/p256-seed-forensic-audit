#!/usr/bin/env python3
"""Enlarged dual-algorithm spot check (2026-10-22, panel-fix round 2).
Design (committed in this header before running): stratified sample of
NON-VIABLE candidates from ALL TEN runs of the merged section-4a
enumeration, allocation proportional to each run's non-viable count with
a minimum of 12 per run, drawn with random.Random(20261023) from rows
with viable==False and a numeric archived order. Each sampled candidate's
seed and b are regenerated with the track pipeline
(code/viability_pipeline.py) and its order recomputed with PARI/GP
ellsea (cypari2, PARI 2.15.4-compatible stack via the track venv) and
compared with the archived ellcard order. Usage: spotcheck_enlarged.py
<shard 0|1> — the sample list is split deterministically into 2 shards.
"""
import json, random, sys, time
sys.path.insert(0, "/home/hatch/workspace/publication-gap-builds/crypto-constants-audit/code")
import viability_pipeline as vp
from cypari2 import Pari

BASE = "/home/hatch/workspace/publication-gap-builds/crypto-constants-audit"
MERGED = f"{BASE}/paper/battery/work/mundane-battery-10run-2026-10-21/section4a_results_merged.json"
shard = int(sys.argv[1])
d = json.load(open(MERGED))
runs = list(vp.RUNS.keys())
pools = {}
for run in runs:
    pools[run] = [r for r in d[run] if r.get("viable") is False and str(r.get("order", "")).isdigit()]
total = sum(len(v) for v in pools.values())
rng = random.Random(20261023)
sample = []
for run in runs:
    k = max(12, round(300 * len(pools[run]) / total))
    pick = rng.sample(pools[run], min(k, len(pools[run])))
    for r in pick:
        sample.append((run, r["n"], str(r["order"])))
print(f"total sample: {len(sample)}", flush=True)
mine = [s for i, s in enumerate(sample) if i % 2 == shard]
pari = Pari(); pari.allocatemem(1 << 30)
results = []
t0 = time.time()
for run, n, archived in mine:
    ts_str, pub_n, p = vp.RUNS[run]
    t = vp.unix(ts_str)
    seed = vp.candidate_seed(t, n)
    b = vp.fips_b_from_seed(seed, p)
    a = p - 3
    try:
        E = pari(f"ellinit([0,0,0,{a % p},{b % p}]*Mod(1,{p}))")
        got = str(pari.ellsea(E))
        ok = (got == archived); err = ""
    except Exception as e:
        got, ok, err = "", False, repr(e)[:200]
    results.append({"run": run, "n": n, "archived_ellcard": archived, "ellsea": got, "match": ok, "error": err})
    print(run, n, "MATCH" if ok else "MISMATCH/ERR", f"{time.time()-t0:.0f}s", flush=True)
out = f"{BASE}/paper/battery/work/panel-fix-round/spotcheck_enlarged_shard{shard}.json"
json.dump({"seed": 20261023, "shard": shard, "count": len(results),
           "mismatches": sum(1 for r in results if not r["match"]), "results": results},
          open(out, "w"), indent=1)
print("shard done:", len(results), "mismatches:", sum(1 for r in results if not r["match"]), flush=True)
