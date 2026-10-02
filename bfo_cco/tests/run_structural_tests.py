"""Structural tests for the bfo_cco archetype.

Usage:
    python run_structural_tests.py DB [--endpoint URL] [--user USER] [--password PASS] [--load]

DB must have been created with `-o database.archetypes=bfo_cco` (or loaded as described in
the archetype README under "Adding BFO/CCO to an existing database"). --load adds
structural_fixture.ttl to the database's default graph first; do this once, on a test
database. Needs only the Python standard library.

Every query runs with reasoning on and binds its rdf:type object to a constant IRI, which
keeps reasoning queries fast (see "Known issues" in the archetype README).
"""
import argparse, base64, json, re, sys, urllib.parse, urllib.request
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("db")
ap.add_argument("--endpoint", default="http://localhost:5820")
ap.add_argument("--user", default="admin")
ap.add_argument("--password", default="admin")
ap.add_argument("--load", action="store_true", help="add structural_fixture.ttl to the database first")
args = ap.parse_args()

E, DB = args.endpoint.rstrip("/"), args.db
AUTH = "Basic " + base64.b64encode(f"{args.user}:{args.password}".encode()).decode()
PFX = """PREFIX obo: <http://purl.obolibrary.org/obo/>
PREFIX cco: <https://www.commoncoreontologies.org/>
PREFIX bfo_cco: <urn:stardog:archetype:bfo_cco#>
PREFIX ex: <urn:bfo_cco:test:>
"""


def http(path, data=None, accept="application/sparql-results+json", ctype=None, method=None):
    headers = {"Authorization": AUTH, "Accept": accept}
    if ctype:
        headers["Content-Type"] = ctype
    req = urllib.request.Request(f"{E}/{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode()


def load_fixture():
    tx = http(f"{DB}/transaction/begin", b"", accept="text/plain", method="POST")
    http(f"{DB}/{tx}/add", (Path(__file__).parent / "structural_fixture.ttl").read_bytes(),
         accept="text/plain", ctype="text/turtle", method="POST")
    http(f"{DB}/transaction/commit/{tx}", b"", accept="text/plain", method="POST")


def query(q, reasoning=True):
    body = urllib.parse.urlencode({"query": PFX + q, "reasoning": str(reasoning).lower()}).encode()
    return json.loads(http(f"{DB}/query", body, ctype="application/x-www-form-urlencoded"))


def ask(q, reasoning=True):
    return query(f"ASK {{ {q} }}", reasoning)["boolean"]


def select_set(var, q, reasoning=True):
    res = query(f"SELECT DISTINCT ?{var} WHERE {{ {q} }}", reasoning)
    return {b[var]["value"].replace("urn:bfo_cco:test:", "ex:") for b in res["results"]["bindings"]}


def count(q, reasoning=False):
    res = query(f"SELECT (COUNT(*) AS ?n) WHERE {{ {q} }}", reasoning)
    return int(res["results"]["bindings"][0]["n"]["value"])


def shacl_report():
    """POST /{db}/icv/report; return {(focus node, shape)} from the SHACL validation report."""
    # No request body: an empty form-encoded body makes this endpoint fail (HTTP 500) on 12.1.1.
    out = http(f"{DB}/icv/report", None, accept="application/n-triples", method="POST")
    res = {}
    for s, p, o in re.findall(r"^(\S+) <http://www.w3.org/ns/shacl#(focusNode|sourceShape)> <([^>]+)>", out, re.M):
        res.setdefault(s, {})[p] = o.replace("urn:bfo_cco:test:", "ex:").replace("urn:stardog:archetype:bfo_cco#", "")
    return {(r["focusNode"], r["sourceShape"]) for r in res.values()}


TESTS = [
    # (name, fn, expected)
    ("part-of chain, forward: blade1 part of aircraft1 (transitive closure)",
     lambda: ask("ex:blade1 bfo_cco:continuantPartOfTransitive ex:aircraft1"), True),
    ("part-of chain, inverse-only data: fan2 part of aircraft2 (transitive closure)",
     lambda: ask("ex:fan2 bfo_cco:continuantPartOfTransitive ex:aircraft2"), True),
    ("all parts of aircraft1 at any depth",
     lambda: select_set("p", "ex:aircraft1 bfo_cco:hasContinuantPartTransitive ?p"), {"ex:jet1", "ex:fan1", "ex:blade1"}),
    ("BFO continuant part of itself stays NON-transitive (BFO meaning preserved)",
     lambda: ask("ex:blade1 obo:BFO_0000176 ex:aircraft1"), False),
    ("location chain: aircraft1 located in base1 (transitive closure)",
     lambda: ask("ex:aircraft1 bfo_cco:locatedInTransitive ex:base1"), True),
    ("location closure, inverse direction: base1 location of aircraft1",
     lambda: ask("ex:base1 bfo_cco:locationOfTransitive ex:aircraft1"), True),
    ("sub-property spatial part of feeds the closure (wingroot1 part of aircraft2)",
     lambda: ask("ex:wingroot1 bfo_cco:continuantPartOfTransitive ex:aircraft2"), True),
    ("sub-property member part of feeds the closure (member1 part of crew1)",
     lambda: ask("ex:member1 bfo_cco:continuantPartOfTransitive ex:crew1"), True),
    ("BFO located in itself stays NON-transitive",
     lambda: ask("ex:aircraft1 obo:BFO_0000171 ex:base1"), False),
    ("parthood does not imply location (blade1 not located in base1)",
     lambda: ask("ex:blade1 bfo_cco:locatedInTransitive ex:base1"), False),
    ("Sensor classification (function, inverse inheres-in, role; not imaging function)",
     lambda: select_set("x", "?x a cco:ont00000569"), {"ex:cam1", "ex:cam2", "ex:sat1"}),
    ("Sensor Platform classification (both branches)",
     lambda: select_set("x", "?x a cco:ont00000021"), {"ex:aircraft1", "ex:mast1"}),
    ("Sensing Process classification (both branches)",
     lambda: select_set("x", "?x a cco:ont00002075"), {"ex:proc1", "ex:proc2"}),
    ("Planned Act classification (3-hop chain, role and disposition branches)",
     lambda: select_set("x", "?x a cco:ont00000228"), {"ex:act1", "ex:act3"}),
    ("Geospatial Location classification (all four branches)",
     lambda: select_set("x", "?x a cco:ont00000487"), {"ex:geo1", "ex:geo2", "ex:geo4", "ex:geo5"}),
    ("hierarchy: Aircraft rolls up to BFO material entity (open query)",
     lambda: "ex:aircraft1" in select_set("x", "?x a obo:BFO_0000040"), True),
    ("hierarchy: Aircraft rolls up to BFO independent continuant (join-bound)",
     lambda: select_set("x", "?x a cco:ont00001043 . ?x a obo:BFO_0000004"), {"ex:aircraft1", "ex:aircraft2", "ex:bad1"}),
    ("hierarchy: Turbofan rolls up to CCO Engine",
     lambda: ask("ex:jet1 a cco:ont00000210"), True),
    ("classified Sensor inherits Sensor's superclass (material entity, open query)",
     lambda: "ex:sat1" in select_set("x", "?x a obo:BFO_0000040"), True),
    ("disjointness probe: individuals typed continuant AND occurrent",
     lambda: select_set("x", "?x a obo:BFO_0000002 . ?x a obo:BFO_0000003"), {"ex:bad1"}),
    ("SHACL report: exactly bad1 and bad2 violate, via the expected shapes",
     lambda: shacl_report(), {("ex:bad1", "Disjoint_BFO_0000002_BFO_0000003"), ("ex:bad2", "Disjoint_ont00000003_ont00000649")}),
    ("reasoning OFF: no Sensor instances asserted (classification is inferred)",
     lambda: select_set("x", "?x a cco:ont00000569", reasoning=False), set()),
]

if __name__ == "__main__":
    if args.load:
        load_fixture()
    ns = json.loads(http(f"{DB}/namespaces", accept="application/json")).get("namespaces", [])
    ns = {n["prefix"]: n["name"] for n in ns}
    print(f"== {DB} @ {E}: namespaces cco={ns.get('cco')} obo={ns.get('obo')} bfo_cco={ns.get('bfo_cco')}")
    print(f"   triples: schema={count('GRAPH <tag:stardog:api:context:schema> {?s ?p ?o}')} "
          f"constraints={count('GRAPH <urn:stardog:archetype:bfo_cco:constraints> {?s ?p ?o}')}")
    fails = 0
    for name, fn, want in TESTS:
        try:
            got = fn()
        except Exception as e:  # noqa: BLE001 - report and continue
            got = f"ERROR {e}"
        ok = got == want
        fails += not ok
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"\n        want {want}\n        got  {got}"))
    print(f"== {len(TESTS) - fails}/{len(TESTS)} passed")
    sys.exit(1 if fails else 0)
