# PROV Archetype

This archetype includes the [PROV](http://www.w3.org/TR/prov-overview/) ontology
and thw OWL encoding of the inference rules from the [PROV semantics](https://www.w3.org/TR/prov-sem/)
document. The [PROV constraints](https://www.w3.org/TR/prov-constraints/) that
are expressed in natural language have been encoded as OWL constraints.

This archetype is named `prov-inline` to avoid the name clash with the built-in
`prov` archetype that is distributed with Stardog. The built-in archetypes in
Stardog are deprecated as of version 7.2.0 and will be removed at a later time
and a `prov` archetype wil lbe added to this repository. The schema for this
archetype is configured to be inline which is different than how the built-in
archetype is defined.