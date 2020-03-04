# Stardog Archetypes

This repository contains a set of [database archetypes](https://www.stardog.com/docs/#_database_archetypes) 
to be used with the [Stardog](http://stardog.com) Knowledge Graph platform. 
Please read the [docs](https://www.stardog.com/docs/#_database_archetypes) to
learn the details of archetypes. The purpose of this repository is to be central
location for commonly used archetypes as a convenience for Stardog users.

## Using Archetypes

Check out or download the contents of this repository to the 
`${STARDOG_HOME}/.archetypes` folder. You can then create a new database using 
the following command:

```
$ stardog-admin db create -o database.archetypes="comma,separated,archetype,names" -n db
```

The archetypes are defined in the subfolders where the folder name is the 
archetype name passed to the above command. So if you would like to create a 
new database with the CIM archetype you would run the command:


```
$ stardog-admin db create -o database.archetypes="cim" -n db
```

The archetype definitions can be stored in a different location other than the 
`${STARDOG_HOME}/.archetypes` folder. In that case the `archetypes.dir` property 
should be set in `${STARDOG_HOME}/.stardog.properties` to point to that folder. 
Note that, changes to `${STARDOG_HOME}/.stardog.properties`  take effect after 
a restart.


## Archetype Definitions

An archetype definition is composed of

* A unique short name identifying the archetype
* A unique IRI identifying the archetype
* A configuration file
* Zero or more namespaces
* Zero or more schema files
* Zero or more constraint files definition

The archetype definition is provided using the following folder structure:

```
archetype-name
|-- archetype.properties
|-- namespaces.ttl
|-- schema
    |-- zero or more 
    `-- schema files
`-- constraints
    |-- zero or more 
    `-- constraint files
```

The name of the folder becomes the short name identifying the archetype. The IRI of the
archetype ia either defined in the configuration file `archetype.properties` or the namespace
declared in `namespaces.ttl` for the archetype name is used. The archetype IRI is used as the
named graph for loading the schema contents if the schema is defined to be inline.

## Archetype configuration

The following configuration options can be set in the `archetype.properties` file:

* `iri`: This sets the IRI for the archetype. If this value is not defined then the namespace
declaration from `namespaces.ttl` will be used or an error will occur.
* `schema.inline`: Boolean value specifying if the schema contents will be loaded in
the database. The default value is true.
* `schema.graph`: The target named graph for storing the inline schema. This option
has no effect if the `schema.inline` option is false. If this option is not set, by default,
inline schema contents will be stored under the archetype IRI.
* `constraints.inline`: Boolean value specifying if the constraints contents will be loaded in
the database. The default value is true. Only SHACL constraints can be loaded inline so for OWL
constraints this property should be set to `false`.
* `constraints.graph`: The target named graph for storing the inline constraints. This option
has no effect if the `constraints.inline` option is false. If this option is not set, by default,
the constraints will be loaded to the `schema.graph` target.

## Releases and Versioning

The releases for this repository are named `YYYY.MM.N` based on the year and the month of the
release date where `N` is a 0-based counter incremented for each subsequent release done during
the month. There are no formal backward-compatability guarantees with respect to schemas and
constraints in these releases.
