"""Run every query in queries/ against both example databases and print the results side by side.

Usage: python3 compare.py [--endpoint URL] [--user USER] [--password PASS]
                          [--plain-db NAME] [--arch-db NAME] [--rows N]
Databases default to the names load_example.sh creates. Standard library only.
"""
import argparse, base64, json, urllib.parse, urllib.request
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--endpoint", default="http://localhost:5820")
ap.add_argument("--user", default="admin")
ap.add_argument("--password", default="admin")
ap.add_argument("--plain-db", default="bfo_cco_example_plain")
ap.add_argument("--arch-db", default="bfo_cco_example")
ap.add_argument("--rows", type=int, default=6, help="rows to print per side")
args = ap.parse_args()
AUTH = "Basic " + base64.b64encode(f"{args.user}:{args.password}".encode()).decode()


def run(db, sparql):
    body = urllib.parse.urlencode({"query": sparql, "reasoning": "true"}).encode()
    req = urllib.request.Request(f"{args.endpoint.rstrip('/')}/{db}/query", data=body,
                                 headers={"Authorization": AUTH, "Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        res = json.loads(r.read().decode())
    cols = res["head"]["vars"]
    return [" | ".join(b.get(c, {}).get("value", "") for c in cols) for b in res["results"]["bindings"]]


for f in sorted((Path(__file__).parent / "queries").glob("*.rq")):
    text = f.read_text()
    meta = {l[2:].split(":", 1)[0].strip(): l.split(":", 1)[1].strip()
            for l in text.splitlines() if l.startswith("# ") and ":" in l}
    print(f"\n### {f.stem}: {text.splitlines()[0][2:]}")
    for label, db, key in (("without archetype", args.plain_db, "expected without archetype"),
                           ("with bfo_cco     ", args.arch_db, "expected with bfo_cco")):
        try:
            rows = run(db, text)
            shown = "; ".join(rows[: args.rows]) + (" ..." if len(rows) > args.rows else "")
            print(f"  {label} {len(rows):3} rows  {shown or '-'}")
        except Exception as e:  # noqa: BLE001
            print(f"  {label} ERROR {e}")
        print(f"  {'':17}   expected: {meta.get(key, '?')}")
