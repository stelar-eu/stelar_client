=========
Changelog
=========

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
