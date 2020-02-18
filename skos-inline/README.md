# SKOS Archetype

The SKOS archetype is for databases that will contain [SKOS](http://www.w3.org/2004/02/skos/) 
data, and includes the SKOS schema and SKOS constraints expressed in SHACL. Note that,
this archetype is different than the (now deprecated) SKOS archetype that is 
bundled with Stardog:

* The schema and constraints in this archetype are [inline](https://www.stardog.com/docs/#_inline_archetypes) 
so they will be loaded into the database.
* SHACL constraints in this archetype include the property domain and range 
constraints which are not included in the bundled archetype.