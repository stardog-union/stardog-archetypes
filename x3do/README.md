# X3D Archetype

This archetype is for the [X3D](https://www.web3d.org/working-groups/x3d-semantic-web) vocabulary. No constraints are defined for this archetype at this time.

A good example set of instance data can be found in the X3D Examples Archive, for example [CAD Part No Transformation](https://www.web3d.org/x3d/content/examples/Basic/CAD/CADPartChildNoTransformationIndex.html).

# Example queries

From the X3D site, example queries of the ontology in the named graph:

 * `<http://www.web3d.org/specifications/X3dOntology4.0#>`

Example:

```
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
PREFIX x3d:  <http://www.web3d.org/specifications/x3d-4.0.xsd#>
PREFIX x3do: <http://www.web3d.org/specifications/X3dOntology4.0#>

# X3dOntologyQuery_02.rq
#   Metaquery to list nodes and statements (concrete owl:Class) that have
#   inherited node types and object types, as defined in X3D Ontology.

###############################################

SELECT distinct (?classes AS ?NodesAndStatements) ?nodeTypes # (str(?lab) AS ?label)
FROM <http://www.web3d.org/specifications/X3dOntology4.0#>
WHERE {
	?classes
        rdf:type         owl:Class ;
        rdfs:subClassOf* ?nodeTypes ;
	    rdfs:label       ?lab .
    FILTER ( !CONTAINS(str(?classes),"X3D") || STRENDS(str(?classes),"X3D") ) # no X3D node types
}
ORDER by ASC(?classes) # alphabetize

###############################################

```


Example with reasoning using the CAD Part example:

```
select * 
where {
    ?s a x3do:X3DNode .
} limit 15

```



