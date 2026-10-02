#!/usr/bin/env bash
# Create the two example databases: the same fleet data, one database WITHOUT and one WITH
# the bfo_cco archetype. Then compare them with compare.py.
#
# Usage: load_example.sh [endpoint] [user:pass]      (default http://localhost:5820 admin:admin)
# Environment:
#   PLAIN_DB=bfo_cco_example_plain  ARCH_DB=bfo_cco_example   database names
#   VOICEBOX=1   also enable Voicebox/semantic search and rebuild the index (needed for tests/voicebox)
#   RECREATE=1   drop the two databases first if they exist (otherwise the script refuses)
#
# Needs curl and python3, and the bfo_cco archetype installed on the server (see ../README.md).
set -euo pipefail
cd "$(dirname "$0")"
E="${1:-http://localhost:5820}"; U="${2:-admin:admin}"
PLAIN_DB="${PLAIN_DB:-bfo_cco_example_plain}"; ARCH_DB="${ARCH_DB:-bfo_cco_example}"
SCHEMA="tag:stardog:api:context:schema"
c() { curl -sS -u "$U" "$@"; }

exists() { c "$E/admin/databases" | python3 -c "import json,sys; sys.exit(0 if '$1' in json.load(sys.stdin)['databases'] else 1)"; }

create() { # db archetype(0/1)
  local opts='"query.timeout":"60s"'
  [ "$2" = 1 ] && opts="$opts,\"database.archetypes\":[\"bfo_cco\"]"
  [ "${VOICEBOX:-0}" = 1 ] && opts="$opts,\"voicebox.enabled\":true,\"search.enabled\":true,\"search.semantic.enabled\":true"
  c -X POST "$E/admin/databases" -F "root={\"dbname\":\"$1\",\"options\":{$opts},\"files\":[]}" >/dev/null
  echo "  created $1"
}

register_namespaces() { # db — one options POST that merges into the existing list
  local body; body=$(c "$E/admin/databases/$1/options" | python3 -c "
import json,sys; o=json.load(sys.stdin)
ns=[n for n in o['database.namespaces'] if not n.startswith('=')]+['=https://example.org/fleet#','d=https://example.org/fleet/data/']
print(json.dumps({'database.namespaces': ns}))")
  c -X POST "$E/admin/databases/$1/options" -H 'Content-Type: application/json' -d "$body" >/dev/null
}

load() { # db file graph
  local tx; tx=$(c -X POST "$E/$1/transaction/begin")
  c -f -X POST "$E/$1/$tx/add?graph-uri=$3" -H 'Content-Type: text/turtle' --data-binary @"$2" >/dev/null \
    || { c -X POST "$E/$1/transaction/rollback/$tx" >/dev/null; echo "  load failed: $2"; exit 1; }
  c -X POST "$E/$1/transaction/commit/$tx" >/dev/null
  echo "  $2 -> <$3>"
}

for DB in "$PLAIN_DB" "$ARCH_DB"; do
  if exists "$DB"; then
    [ "${RECREATE:-0}" = 1 ] || { echo "$DB already exists; set RECREATE=1 to drop and recreate it"; exit 1; }
    c -X DELETE "$E/admin/databases/$DB" >/dev/null
  fi
done

for DB in "$PLAIN_DB" "$ARCH_DB"; do
  echo "== $DB"
  create "$DB" "$([ "$DB" = "$ARCH_DB" ] && echo 1 || echo 0)"
  register_namespaces "$DB"
  # The ontology goes into the reasoning schema graph AND into urn:fleet:kg, the single graph
  # that queries (and Voicebox) are scoped to.
  load "$DB" fleet_ontology.ttl "$SCHEMA"
  load "$DB" fleet_ontology.ttl urn:fleet:kg
  if [ "$DB" = "$ARCH_DB" ]; then
    load "$DB" fleet_cco_alignment.ttl "$SCHEMA"
    load "$DB" fleet_cco_alignment.ttl urn:fleet:kg
  fi
  load "$DB" fleet_data.ttl urn:fleet:kg
  load "$DB" incoming_batch.ttl urn:fleet:incoming
  if [ "${VOICEBOX:-0}" = 1 ]; then
    echo "  rebuilding the semantic index (about 80 s with CCO)..."
    c -X PUT "$E/admin/databases/$DB/optimize" >/dev/null
  fi
done
echo "== done. Next: python3 compare.py --endpoint $E"
