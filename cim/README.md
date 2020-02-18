# CIM Archetype

This archetype is for the [Cloud Information Model (CIM)](https://cloudinformationmodel.org) version 0.1.1
as released on the [CIM repository](https://github.com/cloudinformationmodel/cloudinformationmodel). The
CIM data model is under active development and this archetype will be updated as new versions of the CIM
model are released.

Note that, this archetype does not have a separate constraints folder but the CIM SHACL constraints are
defined in the same file as the schema. Loading the schema and the constraints into the same named graph
is fine and Integrity Constraint Validation functionality will still detect the SHACL constraints and
use them for validation.

The following changes have been made to version 0.1.1 CIM data model:

* The `rdfs:domain` and `rdfs:range` restrictions have been removed due to a [known issue](https://github.com/cloudinformationmodel/cloudinformationmodel/issues/8)
* The resulting RDF file has been serialized in Turtle syntax instead of JSON-LD.