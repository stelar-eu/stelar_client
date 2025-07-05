**********************************
Working with data in Storage
**********************************

.. The STELAR KKnowledge Lake Management System (KLMS) uses MinIO as its storage backend. MinIO is a high-performance, distributed object storage system that is compatible with the Amazon S3 API.
.. STELAR client provides a convenient way to interact with MinIO, allowing users to perform various operations such as uploading, downloading and managing data stored in MinIO.

.. MinIO Integration
.. =================

This client includes comprehensive support for accessing and interacting with
MinIO, an S3-compatible object storage solution. The integration allows users
to interact with MinIO using multiple interfaces, from low-level SDK access
to file system-style operations.

Core Features
-------------

**1. MinIO SDK Access (`Minio`)**

Provides direct access to the `Minio` Python SDK, enabling fine-grained control
over buckets and objects.

.. code-block:: python

    client.s3  # Returns a Minio client instance

Example usage:

.. code-block:: python

    client.s3.list_buckets()
    client.s3.fget_object("my-bucket", "object.txt", "local.txt")


**2. File System Interface via `s3fs`**

Exposes an S3-compatible file system interface using the `s3fs` library.

.. code-block:: python

    fs = client.s3fs()
    fs.ls("my-bucket")  # List contents of a bucket

**3. File Access with `s3fs_open()`**

Simplifies working with files in MinIO via `s3fs`, using file-like semantics.

.. code-block:: python

    with client.s3fs_open("my-bucket/data.csv", "rb") as f:
        data = f.read()

Supports common modes: `'r'`, `'rb'`, `'w'`, `'wb'`, `'a'`, `'ab'`.


**4. Access Credentials Retrieval**

Returns a dictionary of credentials and configuration details required to
interact with MinIO:

- Access key
- Secret key
- Session token
- Endpoint URL
- SSL configuration

.. code-block:: python

    creds = client.s3_access_data()

**5. AWS-Compatible `boto3` Client**

For users familiar with AWS tooling, the client can return a configured
`boto3` S3 client:

.. code-block:: python

    s3 = client._boto3_client()
    s3.list_buckets()

This allows you to use AWS-style APIs and SDKs with MinIO.

Authentication & Security
--------------------------

- Auth is handled using a **Web Identity Token**, refreshed automatically.
- TLS certificate verification is configurable (`self._tls_verify`).
- The token provider is integrated via `minio.credentials.providers.WebIdentityProvider`.

Summary of Interfaces
---------------------

.. list-table::
   :header-rows: 1
   :widths: 20 40 20

   * - Method
     - Description
     - Interface
   * - ``client.s3``
     - Raw MinIO client for SDK operations
     - ``Minio``
   * - ``client.s3fs()``
     - S3-compatible file system
     - ``s3fs.S3FileSystem``
   * - ``client.s3fs_open()``
     - File-like open for MinIO objects
     - File-like API
   * - ``client.s3_access_data()``
     - Retrieve access credentials/config
     - ``dict``
   * - ``client._boto3_client()``
     - AWS-compatible client for S3 API
     - ``boto3.client``

References
----------

- `MinIO Python SDK <https://min.io/docs/minio/linux/developers/python/API.html>`_
- `s3fs Documentation <https://s3fs.readthedocs.io>`_
- `boto3 Documentation <https://boto3.amazonaws.com/v1/documentation/api/latest/index.html>`_
- `MinIO Documentation <https://min.io/docs/minio/linux/developers/python/minio-py.html>`_