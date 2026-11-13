#!/usr/bin/env python3
"""metrics.py <experiments_dir>: check every run's scores.tsv, then print the result tables.
scores.tsv columns: run_id, claim, source (disk|ram|combined), status, evidence (step IDs, comma separated), note
Status: S supported, P partial, U examined and unsupported, NE not examined, TF tool failure."""
import csv, json, sys, pathlib, collections, datetime as dt
RANK = {"U": 0, "P": 1, "S": 2}
problems, rows = [], []
for run in sorted(pathlib.Path(sys.argv[1]).iterdir()):
    sc = run / "investigation" / "scores.tsv"
    if not sc.exists(): continue
    man = json.loads((run / "manifest.json").read_text())
    steps = {}                                       # last recorded row per step wins
    for r in csv.reader((run / "investigation/outputs/_steps.tsv").open(), delimiter="\t"):
        if r[0] != run.name: problems.append(f"{run.name}: outputs/_steps.tsv contains rows of run {r[0]}")
        steps[r[1]] = dt.datetime.fromisoformat(r[4].replace("Z", "+00:00")).timestamp()
    scored_at, seen = sc.stat().st_mtime, set()
    for r in csv.DictReader(sc.open(), delimiter="\t"):
        if r["run_id"] != run.name: problems.append(f"{run.name}: scores.tsv row belongs to run {r['run_id']}"); continue
        ev = [e for e in r["evidence"].split(",") if e]
        for e in ev:
            if e not in steps: problems.append(f"{run.name}: {r['claim']}/{r['source']} cites {e}, which this run never produced")
            elif steps[e] > scored_at + 1: problems.append(f"{run.name}: STALE {r['claim']}/{r['source']}: {e} was rerun after scoring")
        if r["status"] in RANK and not ev: problems.append(f"{run.name}: {r['claim']}/{r['source']} has no evidence reference")
        seen.add((r["claim"], r["source"])); rows.append({**r, "ev": ev, "distro": man["platform"]["distro_id"], "scenario": man["scenario"]})
    for c in man["claims"]:
        for s in ("disk", "ram"):
            if (c["id"], s) not in seen: problems.append(f"{run.name}: no score for {c['id']}/{s}")
if problems:
    print("PROBLEMS (fix before using any number):"); [print("  -", p) for p in problems]; sys.exit(1)

by = collections.defaultdict(dict)
for r in rows: by[(r["run_id"], r["claim"])][r["source"]] = r
print("run_id\tclaim\tdisk\tram\tcombined\tfound_by")
tot = collections.defaultdict(collections.Counter)
for (run, claim), s in sorted(by.items()):
    d, m = s["disk"]["status"], s["ram"]["status"]
    comb = s["combined"]["status"] if "combined" in s else max((x for x in (d, m) if x in RANK), key=RANK.get, default="NE")
    # found_by: 'sweep' if a supporting source cites a generic step, 'targeted' if only C_ steps
    sup = [x for x in (s["disk"], s["ram"]) if x["status"] == "S"]
    lead = "-" if not sup else ("sweep" if any(not e.startswith("C_") for x in sup for e in x["ev"]) else "targeted")
    print(f"{run}\t{claim}\t{d}\t{m}\t{comb}\t{lead}")
    t = tot[run]; t["n"] += 1
    t["disk_S"] += d == "S"; t["ram_S"] += m == "S"; t["comb_S"] += comb == "S"
    t["both_S"] += d == m == "S"; t["disk_only"] += d == "S" != m; t["ram_only"] += m == "S" != d
    t["joint"] += comb == "S" and "S" not in (d, m); t["sweep"] += lead == "sweep"
print("\nrun_id\tclaims\tdisk_S\tram_S\tcombined_S\tboth_S\tdisk_only\tram_only\tjointly\tgain_over_best_single\tfound_by_sweep")
for run, t in tot.items():
    print(f"{run}\t{t['n']}\t{t['disk_S']}\t{t['ram_S']}\t{t['comb_S']}\t{t['both_S']}\t{t['disk_only']}\t{t['ram_only']}\t{t['joint']}\t{t['comb_S']-max(t['disk_S'],t['ram_S'])}\t{t['sweep']}")
