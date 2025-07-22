=========
Changelog
=========


Version 0.8.1
=============

- Fixed a bug in the encoding of ad-hoc extra attributes: they were encoded as strings
- The package PATCH operation returns 404 when a license is not found, instead of 400.
  This resulted in the client considering the dataset as purged, which was incorrect.

Version 0.8.0
=============

- Added support for execution profiles related to tools. Also, added comprehensive tests
  for the execution profiles and tool operations.

Version 0.7.0
=============

- Added support for License entities, which represent licenses for datasets.
- Added support for the resource lineage operations.
- Added the documentation for authorization, user management and policy management.
- Augmented the documentation for the Data Catalog with a section on licenses.

Version 0.6.0
=============

- Added support for relationships.
- Added better support for two new entity types:
  - Policy  represents authorization poplicy specs
  - ImageRegistryToken  represents tokens for accessing the image registry
  
Version 0.5.3
=============

- Added new documentation, an overview of the authorization system of STELAR.

Version 0.5.2
=============

- Project status was upgraded to 'Beta'. This was long overdue but somehow was neglected.
- Added comprehensive documentation for using the client (working with Data Catalog).
- Small enhancement to packages for working with tags.

Version 0.5.1
=============

- Added the `wait()` method to allow polling a task status

Version 0.5.0
=============

- Refactored the code related to tools and tasks, added several enancements.


Version 0.4.2
=============

- Fixed automatic proxy refresh when tasks change state.
- Implemented comprensive tests for task execution.

Version 0.4.1
=============

- Enhanced the support for task execution

Version 0.4.0
=============

- Added preliminary support for task execution.


Version 0.3.7
=============

- Fixed several bugs in the handling of users and tasks, that were due to the
  changes in the server API.
- The package 'author' property is now read-only, reflecting the change in the
  server API.
- Updated further the documentation.

Version 0.3.6
=============

- The start of a more complete documemtation, including a new section on A
  Quick Start Guide.
- Added support for the ``Dataset.add_dataframe()`` and
  ``Resource.read_dataframe()`` operations, which allows the
  client to access or store a dataset with the Storage server.

Version 0.3.5
=============
- Added support for the search operation, which allows the client to search for datasets
  and other entities using the Solr facility. The search operation is available in the
  cursor objects.
- An internal refactoring of the client removed redundant entity definitions.

Version 0.3.4
=============
- Added support for dataset spatial attribute, including validation. A new dependency
  was added to the project, 'geojson'.

Version 0.3.3
=============
- Changed the behabviour of a failed auto-sync operation; if the operation fails,
  the proxy will be reset. This avoids leaving proxies in a DIRTY state after a
  failed auto-sync operation.


Version 0.3.2
=============
- Added support for the client 'info' attribute, which returns information 
  related to the server URLs and the client version.


Version 0.3.1
=============

- Added mappings for all group member fields
- Client now supports a minio client created at initialization (cli.s3)
- Fixed various bugs
