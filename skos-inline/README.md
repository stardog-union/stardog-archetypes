# SKOS Archetype

The SKOS archetype is for databases that will contain [SKOS](http://www.w3.org/2004/02/skos/) 
data, and includes the SKOS schema and SKOS constraints expressed in SHACL.

This archetype is named `skos-inline` to avoid the name clash with the built-in
`skos` archetype that is distributed with Stardog. The built-in archetypes in
Stardog are deprecated as of version 7.2.0 and will be removed at a later time
and a `skos` archetype wil lbe added to this repository.

Note that, this archetype is different than the built-in `skos` archetype:

* The schema and constraints in this archetype are [inline](https://www.stardog.com/docs/#_inline_archetypes) 
so they will be loaded into the database and wil lbe available for SPARQL queries.
* SHACL constraints in this archetype include the property domain and range 
constraints which are not included in the built-in archetype.