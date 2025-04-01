
**********************************
An Overview of the STELAR KLMS
**********************************

In order to descibe the functions of the client, we will first provide an overview of the STELAR KLMS.
The STELAR KLMS is a system that provides a unified interface for managing and accessing data, tools, and workflows.
It is designed to support the entire data lifecycle, from data ingestion and storage to analysis and visualization.
The STELAR KLMS is built on a microservices architecture, which allows for flexibility and scalability.
It is designed to support a wide range of use cases, including data science, machine learning, and artificial intelligence.

If we were to describe the main functions of the STELAR KLMS, we would say that it is a system for:

1. **Storing and managing data**, mainly in the form of files (images, tabular data, etc.) 
#. **Applying data analysis tools**, via which data is transformed and analyzed. Tools are executed as **tasks** or **workflow processes**. Workflows are defined as a series of tasks that can be executed in parallel or sequentially (e.g., data processing, machine learning, etc.).
#. **Collecting and managing metadata** pertaining to the datasets, tasks and processes in the system. Metadata is automatically collected and searchable in several ways, including spatial search and ad-hoc SparQL queries.


Our overview will examine the STELAR KLMS from three perspectives:

1. The concepts that underpin the STELAR KLMS in its three main functions.
2. The architecture of the STELAR KLMS, including the microservices that implement the functions.
3. The STELAR authorization scheme, which controls access to the system and its operations.

Important parts of the STELAR KLMS that are not covered fully in this document include:

- The STELAR Knowledge Graph, which is a graph-based representation of the data and metadata in the system.
- The STELAR deployment framework, which is a set of tools and libraries for deploying and managing the STELAR KLMS in a cloud environment.
- The STELAR tools, a suite of sophisticated data analysis tools that are available in the STELAR KLMS. Each of these tools is quite sophisticated and has its own documentation.
- The STELAR extensibility guidelines, which allow users to extend the functionality of the STELAR KLMS by adding custom tools and extension APIs.

All of the above topics are covered in various STELAR project documents, which is available at `the STELAR site <https://stelar-project.eu>`_.


.. note:: The STELAR KLMS is a complex system, and this overview is intended to provide a high-level understanding of its components and functions. For more detailed information, please refer to the STELAR documentation and the STELAR project site.

.. note:: The STELAR KLMS is a complex system, and this overview is intended to provide a high-level understanding of its components and functions. For more detailed information, please refer to the STELAR documentation and the STELAR project site.


The Main Concepts of the STELAR KLMS
========================================

Working with STELAR, the main function that you will be performing is to manage data and metadata.
As far as data is concerned, the STELAR data lake provides access to its data via the Amazon S3 API.
The data is stored in a distributed file system, which allows for high availability and scalability.

Concepts of the S3 Data Store
-------------------------------

For an in-depth desciption of the S3 data store, please refer to the `Amazon S3 documentation <https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html>`_. In addition, the Minio documentation provides a good overview of the S3 API and its features. The Minio documentation is available at `the Minio site <https://docs.min.io/docs/minio-overview.html>`_.


The data is organized into **buckets**, which are similar to *volumes* (or partitions) in a file system.
The creation and configuration of buckets is done by the STELAR system administrator.
Then, client applications can access the buckets and their contents via some S3 SDK.

The data is stored in **objects**, which can be like of any type (e.g., images, tabular data, etc.).
From the point of view of the system, an object is a binary large object (BLOB) that is stored in a bucket.
The size of an object can be from a few bytes up to 5 TB, and the maximum number of objects in a bucket is unlimited
(although the total size of all objects in a bucket is limited by the size of the bucket).
Objects are identified by a unique key, which is a combination of the bucket name and the object name.

There is no proper folder structure in the S3 data store. However, the object names can be split into
parts using the slash (/) character, which can be used to create a pseudo-folder structure.

Objects are accessed via a URL, which is a combination of the bucket name and the object name.
Suppose that we have a bucket named ``mybucket`` and an object named ``myfolder/myfile.txt``.
To access the object name we would combine the bucket name and the object name into URL, as follows:
```
s3://mybucket/myfolder/myfile.txt
```

There is a special category of objects called **directory objects**. These are objects of size 0 bytes, whose name ends in a slash (/).
Directory objects are used to create a pseudo-folder structure in the S3 data store.


STELAR entities
----------------------------

Outside of the S3 data store, the STELAR KLMS comprises a number of entities that are used to represent data, metadata, users, execution tasks, etc. All entities share some common characteristics, and are managed via the STELAR API, a ReSTful API implemented over http.
The entities in the STELAR KLMS can be categorized into the following groups:

- Entities to describe data and metadata:
  - **Datasets**, which describe collections of data.
  - **Resources**, which are members of datasets and represent actual data files or metadata files.
  - **Tags**, which are labels attached to a dataset.
  - **Vocabularies** of tags, which create namespaces for tags.

- Entities to organize the whole catalog of Entities:
  - **Organizations**, which are top-level entities that are collections of other entities.
  - **Groups**, which are similar to organizations but are more suited for organizing ad-hoc collections of entities.

- **Users**, entities that represent the users of the STELAR KLMS.

- Entities related to the execution of tasks and processes:
  - **Tasks**, which are the execution of a tool on datasets.
  - **Processes**, which are the execution of a workflow (a series of tasks).
  - **Workflows**, which represent metadata about processes. Each process may be related to a workflow entity.
  - **Tools**, which represent the data analysis tools available in the STELAR KLMS.


All of these entities are stored in a Knowledge Graph (KG) and can be searched using SPARQL queries.

Entities can be thought as JSON objects, and each has a number of fields, depending on its type.
Some fields are common to all entities, while others are specific to the type of entity.
Some fields are set and maintained by the STELAR KLMS, while others are set and maintained by the user.
The fields set and maintained by the system are marked as (system), which means that they are read-only and 
cannot be modified by the user. 
Fields may be updatable, while others are **immutable** (cannot be changed after they are created).
Also, some fields are **mandatory** (cannot be null), while others are optional (can be null).

Finally, some types of entities support **extras**, which are custom fields set by the user.

The fields common to all entities are:

id (system)
    The unique identifier of the entity. This is a UUID (Universally Unique Identifier) that is generated 
    by the STELAR KLMS when the entity is created. The UUID is a 128-bit integer that is used to identify 
    the entity in the system.

type (system)
    The type of the entity. This is a string that indicates the type of the entity, such as "dataset", 
    "resource", "user", etc.


Datasets
----------

The main metadata entities in the STELAR KLMS are **datasets** and **resources**. They are both types of **entities** of the STELAR Data Catalog.

A **dataset** is a collection of data. A dataset can be a single object or a collection of objects that are related to each other.
Note that the data in a dataset need not be stored in the STELAR data lake. It can be stored in any other data store, such as a relational database or a NoSQL database, or even to be provided by a service online.

A dataset has several fields, which include the following:

name (immutable)
    The name of the dataset. The name is a string containing only alphanumeric characters, underscores (_), and hyphens (-).
    The name must be unique within the STELAR KLMS and cannot be changed after the dataset is created.
    The name can be used to identify the dataset in the system (similar to the dataset id) but is human-readable.

state (system)
    Whether the dataset entity is `active` or `deleted`. STELAR supports "soft delete" semantics, where a deleted dataset
    is not actually removed from the system, but instead its state is set to `deleted`. This allows for easy recovery of deleted datasets.
    If it is desired to actually remove a dataset, the delete operation must be designated as a **purge**.


metadata_created (system)
    The date and time when the dataset was created. This field is set by the STELAR KLMS when the dataset is created.
    The date and time is in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).

metadata_modified (system)
    The date and time when the dataset was last modified. This field is set by the STELAR KLMS when the dataset is modified.
    The date and time is in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).

creator (system)
    The creator of the dataset. This field is a UUID that describes the creator of the dataset and is used to identify it in the system.

private (mandatory)
    A boolean field that indicates whether the dataset is private or public. This field is used to control access to the dataset.
    More details will be provided in the section on the STELAR authorization scheme.

owner_org (mandatory)
    The organization that owns the dataset. This field is a UUID that identifies the organization which owns the dataset.

groups
    The groups this dataset is a member of.


Apart from the above fields, a dataset entity has many fields that describe the actual dataset.
These fields are:

title
    The title of the dataset. This is a string that describes the dataset and is used to identify it in the system.

author:
    The author of the dataset. 
author_email
    The email of the author of the dataset.

maintainer
    The maintainer of the dataset.

maintainer_email
    The email of the maintainer of the dataset.

notes
    A string containing free-text information about this dataset.

tags
    The tags of the dataset. This is a list of strings that label the dataset.

url
    The URL of the dataset. If not null, this is a string that describes the location of the dataset and is used to access it in the system.

version
    The version of the dataset. This is a string that describes the version of the dataset and is used to identify it in the system.

spatial
    The spatial extent of the dataset. This field, if not null, must be a GeoJSON object that describes the spatial extent of the dataset.

resources (system)
    The list of resources that are part of the dataset. Resources are described in the next section.


Resources
----------

A dataset may contain a list of **resources**, which represent actual data files that are part of the dataset, or metadata files that describe 
the dataset. One such prominent metadata file is the **profile** of the dataset, which is a file that contains metadata about the dataset itself. The profile is a JSON file whose format depends on the type of the dataset (i.e., whether the data is tabular, image, etc.). The profile is used to describe the dataset and its contents, and it is used by the STELAR KLMS to generate metadata about the dataset.
Each resource contains some standard fields, which include the following:

dataset (system)
    The dataset that this resource is part of. This field is a UUID that identifies the dataset in the system.
    The dataset is the parent of the resource.

position (system)
    An integer specifying the rank of the resource in the dataset's resource list. 
    This field is managed by the STELAR KLMS and cannot be set directly by the user.

state (system)
    The state of the resource. This field is managed by the STELAR KLMS and cannot be set directly by the user.
    The state can be `active` or `deleted`. STELAR supports "soft delete" semantics, where a deleted resource
    is not actually removed from the system, but instead its state is set to `deleted`. This allows for easy recovery of deleted resources.
    If it is desired to actually remove a resource, the delete operation must be designated as a **purge**.

created (system)
    The date and time when the resource was created. This field is set by the STELAR KLMS when the resource is created.
    The date and time is in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).

metadata_modified (system)
    The date and time when the resource was last modified. This field is set by the STELAR KLMS when the resource is modified.
    The date and time is in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).

Also, the resource entity has many fields that describe the actual resource.
These fields are:

name
    The name of the resource. Unlike the dataset name, the resource name is not unique in the system, or even
    within the dataset, and it can be null.

url
    The URL of the resource. This is a string that describes the location of the resource and is used to access it in the system.
    If the URL scheme is `s3`, the URL designates an object stored in the STELAR data lake.

format
    The format of the resource. This is a string that describes the data format of the resource and is used to identify it in the
    system. The format can be `csv`, `json`, `excel`, `xml`, `png`, `parquet` etc.

relation
    The relation of the resource to the dataset. This is a string that describes the relation of the resource to the dataset
    and is used to identify it in the system. The relation can be `owned` or `profile`.

resource_type
    The type of the resource.

description
    A string containing free-text information about this resource.

size
    The size of the resource. This is an integer that describes the size of the resource in bytes.

hash
    A string that somehow represents a hash value for the contents of the resource. Nominally, when this value
    changes, it indicates that the contents of the resource have changed. It is custom to use the SHA-256 hash algorithm to compute this value.
    However, this is not enforced by the STELAR KLMS, and the user can set this value to any string.

last_modified
    The date and time when the data of this resource was last modified. This field is maintained by the user, not by
    the STELAR KLMS. The date and time is in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).

mimetype
    The MIME type of the resource. This is a string that describes the MIME type of the resource and is used to identify it in the system.
    The MIME type can be `text/csv`, `application/json`, `application/vnd.ms-excel`, `image/png`, `application/x-parquet` etc.

cache_url
    A url designating a cached copy of the resource. The caching is user-defined and is not managed by the STELAR KLMS.

cache_last_updated
    The date and time when the cache was last updated. This field is maintained by the user, not by the STELAR KLMS.
    The date and time is in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).    



Organizations and groups
----------------------------

Organizations and groups are used to organize other types of entities in the STELAR KLMS.
These two types of entities are very similar, as they support the same attributes. The 
only difference is that organizations are "top-level" entities that *partition* datasets 
(and some other types of entitites). 

Organizations are meant to represent collections of datasets, processes and workflows that
are somehow semantically related. Also, organization membership can be used provide
authorization to users for certain operations (more on this issue will be provided in the
section on the STELAR authorization scheme).

One use case for organizations is to implement data lake **zones**, which are used to separate
data in the data lake into different areas. For example, a data lake may have a **raw zone**
where data is ingested, a **clean zone** where data is cleaned and transformed,
and a **analysis zone** where data is used for analysis and reporting. In general, zones
partition datasets depending on the data lifecycle stage they are in.
Another use case for organizations is to implement **data governance** policies, which are used to
control access to data and ensure that data is used in a compliant manner. For example, an organization may have a policy that requires
data to be encrypted at rest and in transit, or that requires data to be anonymized before it is shared with third parties.
Another use case for organizations is to implement **data stewardship** policies, which are used to ensure that data is
managed in a consistent and compliant manner. For example, an organization may have a policy that requires data to be
classified according to its sensitivity level, or that requires data to be retained for a certain period of time.
Groups are used to organize other types of entities in the STELAR KLMS. Groups are similar to organizations, but they are not top-level entities and do not partition datasets. Groups are used to organize users and other entities in the system, and they can be used to control access to data and tools.

Groups can be used to implement **data sharing** policies, which are used to control access to data and ensure that data is shared in a compliant manner. For example, a group may have a policy that requires data to be updated only by certain user roles, or that requires 
data to be shared only for certain purposes. 

Groups can also be used to implement **dataset cataloging**, where datasets organized in the same group can be related as to
their contents, or some application-specific criteria.

Members of organizations and groups
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The entities associated with an organization or group are called its **members**. The following entities can be members of an organization or group:

- datasets
- processes
- workflows
- tools
- users (users can belong to multiple organizations and groups)
- groups (groups that are members of a group are called its **subgroups**)

Each member of a group has joined the group under a specific **capacity**. Capacities are strings whose semantics are user-defined.
The STELAR KLMS will add members to a group or organization with a specific capacity, but it will not enforce any semantics on the capacity.

Owner organization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Every dataset, process, workflow, tool and user in the STELAR KLMS is owned by an organization.
The owner organization is the organization that created the entity, and it is used to control access to the entity.
The owner organization is set when the entity is created, but it can be changed later.







Architecture of the STELAR KLMS
========================================

blah


The STELAR KLMS authorization scheme
========================================

blah