# BFO / CCO Archetype

This archetype adds the [Basic Formal Ontology 2020](https://github.com/BFO-ontology/BFO-2020)
and the [Common Core Ontologies](https://github.com/CommonCoreOntology/CommonCoreOntologies)
(CCO) v2.2 to a new database, set up so that Stardog's reasoner actually uses them. It also
includes:

- **Stardog-specific inference supplements.** These restore inferences that Stardog's SL
  reasoner otherwise drops: part-of and located-in chains at any depth, and automatic
  classification into CCO's defined classes such as Sensor.
- **SHACL shapes** that catch BFO/CCO disjointness errors in your data, for example a record
  typed as both an aircraft and a maintenance event.

```
$ stardog-admin db create -o database.archetypes=bfo_cco -n db
```

**What the archetype does not do.** It does not connect *your* ontology to CCO. Until you
align your classes and properties with CCO and BFO (see
[Aligning your ontology](#aligning-your-ontology)), CCO is present but no data belongs to
it, and CCO-level queries return nothing. The alignment is usually a few dozen axioms, and
it is the part each team has to write.

## Requirements and tested environments

| | |
|---|---|
| Tested | Stardog **12.1.1** (Docker image `stardog/stardog:12.1.1`), `reasoning.type=SL`, default options |
| Other versions | Not yet tested with this archetype. |
| Server file access | The archetype mechanism reads the folder from the server's file system. Where you cannot place files on the server, for example on a managed service, use [Adding BFO/CCO to an existing database](#adding-bfocco-to-an-existing-database) instead. That procedure only needs normal data-loading rights. |

## Installation

Copy this `bfo_cco` folder into `${STARDOG_HOME}/.archetypes/` on the Stardog server, so
that `${STARDOG_HOME}/.archetypes/bfo_cco/archetype.properties` exists. You can also point
`archetypes.dir` in `stardog.properties` at a folder that contains it; changes to
`stardog.properties` need a restart.

- **Docker:** `STARDOG_HOME` is usually a mounted volume (`/var/opt/stardog`). Copy the
  folder into `<volume>/.archetypes/`. On 12.1.1 a new archetype folder was picked up
  without a restart.
- **Kubernetes / Helm:** mount the folder into the Stardog pod at
  `${STARDOG_HOME}/.archetypes/bfo_cco`, for example from a ConfigMap or a volume, or bake
  it into a custom image. The CCO file is about 2 MB, which is over the 1 MB ConfigMap
  limit, so use a volume or image for the `schema` folder.
- **Clusters:** every node needs the same folder.

## Creating a database

```
$ stardog-admin db create -o database.archetypes=bfo_cco -o query.timeout=60s -n db
```

Setting `query.timeout` is recommended; see [Known issues](#known-issues). The archetype
works together with other options in the same call, including the Voicebox options:

```
$ stardog-admin db create -o database.archetypes=bfo_cco \
    -o voicebox.enabled=true -o search.enabled=true -o search.semantic.enabled=true \
    -o reasoning.type=SL -o query.timeout=60s -n db
```

The archetype is applied **only when the database is created**. For an existing database,
use the procedure below.

## Adding BFO/CCO to an existing database

This loads the same content that the archetype loads at creation. It needs no server file
access, so it also works on managed deployments.

```
$ stardog data add --named-graph tag:stardog:api:context:schema db \
    schema/CommonCoreOntologiesMerged.ttl schema/bfo_cco-stardog-inferences.ttl
$ stardog data add --named-graph urn:stardog:archetype:bfo_cco:constraints db \
    constraints/bfo_cco-disjointness-shacl.ttl
$ stardog namespace add --prefix cco --uri https://www.commoncoreontologies.org/ db
$ stardog namespace add --prefix obo --uri http://purl.obolibrary.org/obo/ db
$ stardog namespace add --prefix bfo_cco --uri 'urn:stardog:archetype:bfo_cco#' db
```

The result is identical to creating the database with the archetype.

- Use `data add`, **never** `CLEAR` or replace `tag:stardog:api:context:schema`. That graph
  also holds your own ontology.
- Take a backup of the schema graph first (`stardog data export --named-graph
  tag:stardog:api:context:schema db`). You can then remove BFO/CCO later by restoring it.

### Making the reasoner and Voicebox use it

The reasoner only reads the graphs listed in `reasoning.schema.graphs`, and Voicebox only
indexes the graphs in `search.semantic.index.contexts.filter`. A database created normally
already has `tag:stardog:api:context:schema` in both, so there is nothing to do. A
database whose reasoning schema was pointed at a different graph, for example by a tool
that publishes its own model graph, does not. Check both settings, and fix them if needed,
in this order:

1. **Read the current settings.** Note `reasoning.schema.graphs`, `search.semantic.enabled`
   and `search.semantic.index.contexts.filter`.

   ```
   $ curl -u admin:admin http://localhost:5820/admin/databases/db/options
   ```

2. **If semantic search is on and the filter does not include
   `tag:stardog:api:context:schema`, add it.** Send the full list: the existing entries plus
   the new one. Change this option on its own, with the database offline. On 12.1.1,
   setting it together with other options, or while online, can leave it empty.

   ```
   $ curl -u admin:admin -X PUT http://localhost:5820/admin/databases/db/offline
   $ curl -u admin:admin -X POST http://localhost:5820/admin/databases/db/options \
       -H 'Content-Type: application/json' \
       -d '{"search.semantic.index.contexts.filter": ["<existing entries>", "tag:stardog:api:context:schema"]}'
   $ curl -u admin:admin -X PUT http://localhost:5820/admin/databases/db/online
   ```

   Do this step first. Stardog rejects a reasoning schema graph that is not in the semantic
   index filter, with HTTP `422`.

3. **Add `tag:stardog:api:context:schema` to the reasoning schema graphs.** Keep the
   existing graphs. The database can stay online for this step.

   ```
   $ curl -u admin:admin -X POST http://localhost:5820/admin/databases/db/options \
       -H 'Content-Type: application/json' \
       -d '{"reasoning.schema.graphs": ["<existing graphs>", "tag:stardog:api:context:schema"]}'
   ```

4. **Rebuild the semantic index** if semantic search is on. With CCO loaded this takes a
   minute or more.

   ```
   $ stardog-admin db optimize db
   ```

5. **Verify.** Read the options again, and confirm both lists contain
   `tag:stardog:api:context:schema`. Once aligned data exists, a reasoning query such as
   `SELECT (COUNT(*) AS ?n) { ?x a <http://purl.obolibrary.org/obo/BFO_0000001> }` returns
   more than 0.

## Aligning your ontology

Your data is typed with your own classes and linked with your own properties. For BFO/CCO
queries and the supplements to apply, add alignment axioms to
`tag:stardog:api:context:schema`:

- make each domain class `rdfs:subClassOf` its closest CCO (or BFO) class;
- make each relationship property `rdfs:subPropertyOf` the matching BFO relation.

```turtle
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix obo:  <http://purl.obolibrary.org/obo/> .
@prefix cco:  <https://www.commoncoreontologies.org/> .
@prefix ex:   <https://example.org/ops#> .

# Classes -> CCO classes
ex:Drone          rdfs:subClassOf cco:ont00001043 .   # Aircraft
ex:SupplyTruck    rdfs:subClassOf cco:ont00000053 .   # Ground Motor Vehicle
ex:Engine         rdfs:subClassOf cco:ont00000210 .   # Engine
ex:Camera         rdfs:subClassOf cco:ont00000199 .   # Camera
ex:Depot          rdfs:subClassOf cco:ont00000192 .   # Facility
ex:ImagingCapability rdfs:subClassOf cco:ont00001241 .  # Sensor Function
ex:RepairJob      rdfs:subClassOf cco:ont00000950 .   # Act of Maintenance

# Properties -> BFO relations
ex:installedOn    rdfs:subPropertyOf obo:BFO_0000176 .  # continuant part of
ex:componentOf    rdfs:subPropertyOf obo:BFO_0000176 .  # continuant part of
ex:stationedAt    rdfs:subPropertyOf obo:BFO_0000171 .  # located in
ex:hasCapability  rdfs:subPropertyOf obo:BFO_0000196 .  # bearer of
ex:performedOn    rdfs:subPropertyOf obo:BFO_0000057 .  # has participant
```

The supplements depend on these BFO relations. Map your properties to them to get the
corresponding behavior:

| BFO relation | Map your property here if it means… | Enables |
|---|---|---|
| `BFO_0000176` continuant part of (inverse `BFO_0000178` has continuant part) | component of, installed on, mounted on | `bfo_cco:continuantPartOfTransitive` / `hasContinuantPartTransitive`: parts at any depth |
| `BFO_0000171` located in (inverse `BFO_0000124` location of) | housed in, stationed at, located at | `bfo_cco:locatedInTransitive` / `locationOfTransitive`: everything at a place at any depth |
| `BFO_0000196` bearer of (inverse `BFO_0000197` inheres in) | has capability, has function, has role | Classification as CCO **Sensor** or **Sensor Platform** when the capability is a Sensor Function or Sensor Role (or a sub-class of one) |
| `BFO_0000055` realizes | an activity that uses a capability | Classification as **Sensing Process** or **Planned Act** |
| `BFO_0000059` concretizes | a role or disposition that carries out a plan or order | **Planned Act** (with realizes) |

Guidelines:

- **Check what CCO already asserts.** For example, CCO already makes every *Act of
  Maintenance* a *Planned Act*.
- **Don't align something that is a design or a specification to a physical-object class.**
  A platform *model* is an information content entity (for example CCO Artifact Model), not
  a Material Artifact.
- **Use `rdfs:subClassOf` / `rdfs:subPropertyOf`, not `owl:equivalentClass`.** Equivalence
  would also type CCO instances as your classes.
- **After aligning, run the verification queries below.** Also compare your domain class
  counts with reasoning on and off; they should not change.

### Verification queries

Run these with reasoning on. Each rdf:type object is a constant IRI, which keeps reasoning
queries fast (see [Known issues](#known-issues)).

```sparql
PREFIX cco: <https://www.commoncoreontologies.org/>
PREFIX obo: <http://purl.obolibrary.org/obo/>
PREFIX bfo_cco: <urn:stardog:archetype:bfo_cco#>

# Roll-up by CCO category
SELECT ?type (COUNT(DISTINCT ?x) AS ?n) WHERE {
  { ?x a cco:ont00001043 . BIND("Aircraft" AS ?type) }
  UNION { ?x a cco:ont00000618 . BIND("Ground Vehicle" AS ?type) }
  UNION { ?x a obo:BFO_0000040 . BIND("All material entities" AS ?type) }
} GROUP BY ?type

# Everything that is part of something, at any depth
SELECT ?whole ?part WHERE { ?whole bfo_cco:hasContinuantPartTransitive ?part }

# Sensors inferred from capabilities
SELECT ?sensor WHERE { ?sensor a cco:ont00000569 }

# Data quality: anything that is both a continuant and an occurrent
SELECT ?x WHERE { ?x a obo:BFO_0000002 ; a obo:BFO_0000003 }
```

## Contents

| File | Loaded into | What it is |
|---|---|---|
| `schema/CommonCoreOntologiesMerged.ttl` | `tag:stardog:api:context:schema` | CCO v2.2 merged file, which includes BFO 2020 core. Unmodified copy of CCO tag `v2.2`, `src/cco-merged/`. sha256 `a9453382b25b40781c181d6ba44981f228abb76d90d548846713adba9baadb42`. 13,875 triples. |
| `schema/bfo_cco-stardog-inferences.ttl` | `tag:stardog:api:context:schema` | Stardog supplements (160 triples, described below). |
| `constraints/bfo_cco-disjointness-shacl.ttl` | `urn:stardog:archetype:bfo_cco:constraints` | 42 SHACL shapes, one per disjoint class pair. |
| `tools/gen_disjointness_shacl.py` | not loaded | Regenerates the SHACL file from the CCO file (needs `rdflib`). |
| `example/` | not loaded | Worked example: the same fleet data with and without the archetype, seven comparison queries and a loader. See [example/README.md](example/README.md). |
| `tests/` | not loaded | Structural test suite (`run_structural_tests.py`) and a Voicebox A/B harness (`tests/voicebox/`). |
| `LICENSE-CCO` | not loaded | The CCO license (BSD 3-Clause), which must accompany the CCO file. |

Stardog loads only `schema/` and `constraints/`. The other folders are ignored by the
archetype loader.

Registered namespaces: `cco:` (`https://www.commoncoreontologies.org/`), `obo:`
(`http://purl.obolibrary.org/obo/`) and `bfo_cco:` (`urn:stardog:archetype:bfo_cco#`, the
archetype's own terms). The default `:` prefix is left for your domain ontology.

Do not use `AllCoreOntology.ttl` from the CCO repository. In v2.2 it is only an
`owl:imports` stub with no axioms.

### Why the schema goes into the default schema graph

`archetype.properties` sets `schema.graph = tag:stardog:api:context:schema`. Without that
setting, Stardog 12 loads an inline archetype schema into a named graph (the archetype
IRI). That graph is not in `reasoning.schema.graphs`, so the ontology would be present but
ignored by the reasoner. The same happens to the `skos-inline` archetype in this
repository: its `skos:broader` ⊑ `skos:semanticRelation` inference does not fire.

A separate named reasoning schema (`reasoning.schemas`) is not a good alternative either.
On a database with semantic search enabled, which includes any Voicebox database, Stardog
rejects it with `422 0DICC2` unless the graph is also added to
`search.semantic.index.contexts.filter`.

## Stardog inference supplements

Stardog's SL reasoner skips 38 axioms of the merged file as "Not a valid SL axiom". The
warnings are logged in `stardog.log` on the first reasoning query. The supplement file adds
no new warnings.

### 1. Transitive closures of parthood and location

BFO defines *continuant part of* (`BFO_0000176`) and *located in* (`BFO_0000171`) as
holding **at some time**. Relations defined that way are not transitive, and BFO correctly
does not declare them transitive. This archetype leaves the BFO relations unchanged and
adds archetype-owned transitive super-properties instead:

| Property | Closure of |
|---|---|
| `bfo_cco:continuantPartOfTransitive` | continuant part of, including its sub-properties (member part of, spatial part of, …) |
| `bfo_cco:hasContinuantPartTransitive` | has continuant part |
| `bfo_cco:locatedInTransitive` | located in |
| `bfo_cco:locationOfTransitive` | location of |

Query these properties for "directly or indirectly" roll-ups, such as every component of
an aircraft at any depth. Each link in a chain holds at some time. The chain does not claim
that all links hold at the same time.

### 2. Sufficient conditions for CCO's defined classes

CCO defines Sensor, Sensor Platform, Sensing Process, Planned Act and Geospatial Location
with `owl:equivalentClass` over a union. That is not valid in SL, so Stardog drops the
whole axiom and never classifies anything into these classes. The supplement splits each
union into SL-valid sufficient conditions, for example *material entity and bearer of some
Sensor Function* ⊑ *Sensor*. These classifications then work with the default
`reasoning.approximate=false`.

Geospatial Location's condition, "location of some (independent continuant and not spatial
region)", cannot be expressed in SL. It is under-approximated with material entity, site
and continuant fiat boundary. The result is sound but slightly incomplete.

### Not approximated

The other 33 skipped axioms are deliberately left out:

- 23 domain and range axioms over unions, for example on "participates in", "has
  participant" and "concretizes";
- 10 universal restrictions over unions.

Sound weakenings exist; for example, a union domain could be replaced by a common
superclass such as independent continuant. They were left out because they add little for
query answering.

## SHACL constraints

There is one `sh:NodeShape` per disjoint class pair: 21 pairs from `owl:disjointWith` and
21 more expanded from 5 `owl:AllDisjointClasses` axioms. Each has `sh:severity
sh:Violation`. The shapes flag, for example, anything that is both a continuant and an
occurrent. They are standard SHACL, and pyshacl gives the same report as Stardog.

`sh:targetClass` and `sh:class` follow `rdfs:subClassOf` in the data graph. Validate over
graphs that include `tag:stardog:api:context:schema`; the default `context:local` does. If
you validate only your own named data graph, violations that are visible only through the
CCO hierarchy are missed.

```
$ stardog icv report db        # add -r to validate with reasoning
```

Avoid `stardog reasoning consistency` on a CCO database. On 12.1.1 it hung for more than 2
minutes and left background processes running.

## Using it with Voicebox

- Create the database with the archetype and the Voicebox options in one call (see
  [Creating a database](#creating-a-database)). The default
  `search.semantic.index.contexts.filter` already includes `context:schema`, so Voicebox
  indexes CCO without any filter change.
- Register `:` for your domain ontology after creating the database, because
  `stardog-admin` cannot pass an empty prefix. Send one `database.namespaces` options POST
  that merges your prefixes into the current list, so that `cco`, `obo` and `bfo_cco` are
  kept.
- Add your domain ontology and alignment to `context:schema` with `data add`. Never `CLEAR`
  that graph: the archetype is not re-applied, so clearing it silently removes BFO/CCO.
- Plan for `optimize`, which rebuilds the semantic index, to take longer. In testing it
  took about 80 s with CCO loaded, compared with about 2 s without.
- CCO documents its classes with `skos:definition` rather than `rdfs:comment`. Voicebox
  found CCO classes such as Sensor by label without problems.
- Set `query.timeout`. Voicebox sometimes generates queries with a variable `rdf:type`
  object (see [Known issues](#known-issues)).

**Testing.** We ran an A/B test with a fleet-maintenance dataset: the same 13 questions,
asked 3 times each, against identical databases with and without the archetype.

| | With the archetype | Without |
|---|---|---|
| All questions | 38 of 38 answered correctly, plus one intermittent Voicebox error | 31 of 39 |
| Domain-only questions | 18 of 18 | 18 of 18 |

The gains were on sensors (the inferred defined class), "all physical objects" (BFO
material entity) and components at any depth (BFO parthood). Domain-only questions were
unaffected.

## Known issues

- **Variable-type reasoning queries are slow.** On a CCO database with very little data,
  `<x> a ?t` took about 12 s and `?s a ?c GROUP BY ?c` about 80 s. Binding the type through
  `VALUES` does not help; one query per class does. LLM-generated SPARQL produces these
  shapes, so set `query.timeout`: a 60 s timeout cancels them cleanly with HTTP 410.
- **The archetype is applied only at database creation.** Scripts that `CLEAR` or replace
  `tag:stardog:api:context:schema` remove BFO/CCO without warning.

## Example and tests

- **[example/](example/README.md)** loads a fleet-maintenance dataset into two databases,
  one without and one with the archetype. It then runs seven comparison queries side by
  side: CCO roll-ups, inferred sensors, parts and locations at any depth, and a bad record
  caught by BFO disjointness, plus a domain-only control. Start there to see what the
  archetype does and what an alignment looks like.
- **Structural tests** check every supplement axiom (including negative cases), the
  hierarchy and the SHACL shapes. They need only the Python standard
  library. Run them on a test database created with the archetype:

  ```
  $ python3 tests/run_structural_tests.py DB --endpoint http://localhost:5820 --load
  ```

  On 12.1.1: 22 of 22 pass. With plain
  CCO, without the supplements and shapes, 9 of 22 pass.
- **Voicebox A/B:** `tests/voicebox/voicebox_eval.py` asks the same 13 questions against
  both example databases; `analyze_results.py` summarizes the results. See the
  docstrings for options.

## Updating the CCO version

1. Replace `schema/CommonCoreOntologiesMerged.ttl` with the new release's
   `src/cco-merged/CommonCoreOntologiesMerged.ttl`, and update the sha256 above.
2. Run `python tools/gen_disjointness_shacl.py`.
3. Create a test database and run one reasoning query. Compare the "Not a valid SL axiom"
   warnings in `stardog.log` with section 2 of the supplement file. A defined class that
   has changed may need its sufficient conditions updated.
4. Run `tests/run_structural_tests.py` and `example/compare.py` against fresh test
   databases.

## Licenses

- **CCO** (`schema/CommonCoreOntologiesMerged.ttl`) is © CUBRC, Inc. and distributed
  under the BSD 3-Clause License. The full text is in `LICENSE-CCO`, and must be kept
  with any redistribution.
- **BFO 2020**, included in the CCO merged file, is licensed under
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Source:
  <https://github.com/BFO-ontology/BFO-2020>.
- The supplement, shapes, tools, example and tests in this folder are original to this
  archetype.
