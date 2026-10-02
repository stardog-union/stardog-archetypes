"""Summarize a voicebox_eval.py results file as a Markdown table.

Usage: python3 analyze_results.py OUT.jsonl      (the file voicebox_eval.py wrote)
Infrastructure errors (HTTP 5xx, exceptions) are counted separately from wrong answers.
"""
import json, re, statistics, sys
from collections import defaultdict

rows = [json.loads(l) for l in open(sys.argv[1])]
dbs = list(dict.fromkeys(r["db"] for r in rows))  # order of first appearance
qs = list(dict.fromkeys(r["id"] for r in rows))
by = defaultdict(list)
for r in rows:
    by[(r["id"], r["db"])].append(r)


def vocab(recs):
    used = set()
    for r in recs:
        for q in r.get("sparql") or []:
            used |= set(re.findall(r"\b(?:cco|obo|bfo_cco):[A-Za-z0-9_]+", q))
    return ", ".join(sorted(used)) or "-"


print("| Q | kind | " + " | ".join(f"{d} correct / answered (infra err)" for d in dbs) + " | BFO/CCO terms in generated SPARQL |")
print("|---|---|" + "---|" * len(dbs) + "---|")
tot = {d: [0, 0, 0] for d in dbs}
kind_tot = defaultdict(lambda: [0, 0])
for q in qs:
    cells = []
    for d in dbs:
        recs = by[(q, d)]
        ok = sum(r["correct"] for r in recs)
        infra = sum(r["status"] != "ok" for r in recs)
        answered = len(recs) - infra
        tot[d][0] += ok; tot[d][1] += answered; tot[d][2] += infra
        kind_tot[(recs[0]["kind"], d)][0] += ok; kind_tot[(recs[0]["kind"], d)][1] += answered
        cells.append(f"{ok}/{answered}" + (f" ({infra})" if infra else ""))
    print(f"| {q} | {by[(q, dbs[0])][0]['kind']} | " + " | ".join(cells) + f" | {vocab([r for d in dbs for r in by[(q, d)]])} |")
print()
for d in dbs:
    lat = [r["latency_s"] for r in rows if r["db"] == d and r["status"] == "ok"]
    print(f"- **{d}**: {tot[d][0]}/{tot[d][1]} correct of answered, {tot[d][2]} infra errors, median latency {statistics.median(lat):.1f}s")
for (k, d), (ok, n) in sorted(kind_tot.items()):
    print(f"  - {k} questions on {d}: {ok}/{n}")
