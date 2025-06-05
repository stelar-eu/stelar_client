**********************************
Working with the Data Catalog
**********************************

The STELAR Client provides Python bindings for all entities of the STELAR API.
This section provides an overview of the Data Catalog and how to work with it 
using the STELAR Client. In order to fully follow this guide, you should be familiar
with the examples and steps of the :ref:`quickstart-guide`.

Overview of the Data Catalog
============================

The Data Catalog is a central repository in the STELAR KLMS where entities such as datasets, 
resources, groups, processes, and other entities are stored and searched. 
It allows users to create, update, and search for entities, as well as manage custom fields 
and tags associated with those entities


Basic types of entities
--------------------------

Packages
    These hold the metadata for datasets, workflow processes, tools and workflows. They
    can be searched, tagged, they have resources and can be related semantically to each other.
    They can also be grouped together.

Resources
    They represent actual digital artifacts (data files, hyperlinks, etc). They can be searched and
    tagged freely.

Organizations and Groups
    These are used to organize collections of packages, users and other groups.

Other entities
    The Data Catalog also contains other entities such as Users, Tasks, Vocabularies and Tags.
    These entities are auxilliary to the management and organization of the data catalog,
    and will be examined separately.


Organizations
---------------------------

In general, the Data Catalog is organized around Organizations. Every Dataset, Process, Worklow or Tool
belongs to an Organization. Organizations are important because they are used in assigning access 
permissions to their contents. 

A user can be a member of several organizations, and can have a different role in each organization.
When working with the STELAR Client, you can specify the organization you want to work with when creating 
or updating entities.


Entities and proxies
============================

Working with the Data Catalog entities in the STELAR Client is done through *Proxies*.
A proxy to an entity is a Python object which represents the entity and allows update operations
on it. 

Every Data Catalog entity is identified by a UUID (Universally Unique Identifier).
To create a proxy on an entity, all that is needed is the UUID of the entity.

Proxies are **unique**: for a given entity, there is only one proxy
for it in the STELAR Client at any given time. In order to guarantee this, 
**you never create proxies directly**. Instead, you **look up** a proxy in the
client, using its UUID. A proxy for this UUID will be returned to you if it exists, 
or a new one will be created for you if it does not exist yet. 
This way, you can always be sure that you are working with the unique proxy
for a given entity.

Of course, there are better ways to get a proxy than looking it up by UUID.
For example, you can get a proxy for an entity by its name, or by searching for it.
All these operations can be performed using the *cursor* for the entity type.
Suppose that you have created a Client.

.. code-block:: python

    from stelar import Client

    client = Client()
    # This will create a client that connects to the STELAR KLMS

You can then get a cursor for, e.g., datasets, and use it to get the proxy for
a dataset, by name:

.. code-block:: python

    dset = client.datasets['iris']

assuming that the KLMS has a dataset with the name 'iris'.

If the dataset does not exist, an exception will be raised.
You can check if the dataset exists by

.. code-block:: python

    'iris' in client.datasets
    # Returns True if the dataset exists, False otherwise

or you can use the `get` method to get the dataset, which will return None if it does not exist:

.. code-block:: python

    dset = client.datasets.get('iris')
    # Returns the dataset proxy if it exists, None otherwise

Often, you want to see a list of all datasets that exist in the KLMS (and you are authorized to see).
A fast way to do this is to use the `[]` access with a python slice:

.. code-block:: python

    client.datasets[:]
    # Returns the first 1000 datasets in the KLMS

Since there can be many datasets, you can define smaller (or larger) slices, e.g.:

.. code-block:: python

    client.datasets[:10]  # Returns the first 10 datasets
    client.datasets[10:20]  # Returns datasets 11 to 20
    client.datasets[1000:]  # Returns all datasets starting from the 1001st

Proxy and cursor types
-----------------------------

For each entity type in the Data Catalog, there is a corresponding *proxy type* and 
a *cursor* in the client. For example, for datasets, the proxies are instances of class 
`Dataset` (technically, `stelar.client.Dataset`), and the cursor is accessible via the 
`client.datasets` attribute.

The follwing table provides the proxy type and cursor atribute for each entity type:

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Entity Type
     - Proxy Type and Cursor Attribute
   * - Dataset
     - `Dataset` proxy type, accessible via `client.datasets`
   * - Process
     - `Process` proxy type, accessible via `client.processes`
   * - Workflow
     - `Workflow` proxy type, accessible via `client.workflows`
   * - Tool
     - `Tool` proxy type, accessible via `client.tools`
   * - Resource
     - `Resource` proxy type, accessible via `client.resources`
   * - Organization
     - `Organization` proxy type, accessible via `client.organizations`
   * - Group
     - `Group` proxy type, accessible via `client.groups`
   * - User
     - `User` proxy type, accessible via `client.users`
   * - Task
     - `Task` proxy type, accessible via `client.tasks`
   * - Vocabulary
     - `Vocabulary` proxy type, accessible via `client.vocabularies`
   * - Tag
     - `Tag` proxy type, accessible via `client.tags`


The state of a proxy
------------------------------

Proxies strive to be high-performance, without the user being aware all the time
of their state. In fact, a proxy can be in one of four states. The Python *enum* type
`ProxyState` defines these states:

`ProxyState.EMPTY`
    The proxy has does not contain any attribute information about the entity it represents. 
    This is the initial state of a proxy, when it is created, when only the entity ID is given.
    An empty proxy will be synced automatically, when any attribute of the proxy is accessed.
`ProxyState.CLEAN`
    The proxy has all the attributes of the entity it represents, and they are up-to-date to
    the latest proxy sync. This is the state of a proxy after its entity has been loaded 
    from the KLMS.
`ProxyState.DIRTY`
    The proxy has been modified, but the changes have not been saved to the KLMS yet.
    Normally, a proxy update is transferred to the KLMS automatically, but sometimes
    this is delayed, e.g. when the proxy is being used in a batch operation.
`ProxyState.ERROR`
    The proxy object does not represent a valid entity any more. This can happen, for example,
    right after an entity is deleted from the KLMS, or if a proxy is created with an invalid UUID.


The state of a proxy can be checked using the `proxy_state` attribute of the proxy:

.. code-block:: python

    dset = client.datasets['iris']
    if dset.proxy_state is ProxyState.CLEAN:
        print("The dataset proxy is in a clean state.")

Several methods manipulate the state of a proxy.


Syncing
^^^^^^^^^^^^^^^

The `dset.proxy_sync()` call will synchronize the proxy with the KLMS, rendering it `CLEAN`.
In particular, if the proxy was `EMPTY`, it will be populated with the attributes of the entity.
If the proxy was `DIRTY`, the updates held by the proxy will be sent to the KLMS, and the proxy will
be refreshed with the latest attribute values from the KLMS.


Invalidation
^^^^^^^^^^^^^^^^^

Sometimes, you want to invalidate a `CLEAN` proxy, so that it becomes `EMPTY` again.
You can do this by calling the `dset.proxy_invalidate()` method. This is useful when you know or
suspect (e.g., because of a timeout) that the values of the proxy are stale, but you do not actually
need to update the proxy immediately. 

Resetting
^^^^^^^^^^^^^^^^

Sometimes, an updated (`DIRTY`) proxy is updated with an illegal value. In this case, the 
*sync* operation will fail, leaving the proxy in the `DIRTY` state. The typical response
is then to restore the proxy attributes to the last known good state. This is done by calling
the `dset.proxy_reset()` method. This will reset the proxy to the last known good state,
which is the state it was in before the last update operation. The proxy will then be in 
the `CLEAN` state, and the last update operation will be discarded.


Type-safety operations
^^^^^^^^^^^^^^^^^^^^^^^^^

A proxy has attributes that provide consistency checking and type-safety.
For example, if you try to set an attribute of a proxy to a value of the wrong type,
you will get a `TypeError` exception. This is useful to ensure that the data you are working with
is of the correct type, and to avoid errors when updating the the KLMS.

However, sometimes you want to bypass this high-level API and work with JSON objects directly.
To do this, you can use the following attributes and operations:

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Attribute/Operation
     - Description
   * - `dset.proxy_attr`
     - A dict that contains the attributes of the proxy.
   * - `dset.proxy_changed`
     - A dict that contains the original values of updated attributes.
   * - `dset.proxy_from_entity(json)`
     - Update attributes from a JSON object.
   * - `dset.proxy_to_entity()`
     - Convert the proxy to a JSON object.


Pretty-printing proxies
^^^^^^^^^^^^^^^^^^^^^^^^^

You can use the `dset.s` expression to convert the proxy to a Pandas series, suitable
to be pretty-print in a Jupyter notebook or in a terminal. 
This is useful for quick-and-dirty inspection of the proxy attributes. However, not
all attributes are shown; null values are not shown, nor user-defined attributes.
To get a full view of the proxy attributes, you can use `dset.sxl`


Proxy lists
-----------------------------

When you use a slice on a cursor, you get a *proxy list*. The same applies to getting 
the resources of a dataset, or the tasks of a worklow, etc.

A `ProxyList` object, which we will refer to as a *proxy list* is a typed list of
entities. You cannot have a mixed-type proxy list  (of course, you can have a **Python list** of 
mixed types of proxies, but that is not what we are talking about here).

Proxy lists are cheap to manipulate. Under the hood, they are just a lists of UUIDs, but accessing
an element returns an actual proxy for the entity. They are iterable and can be indexed much like
regular Python lists. Also, importantly, they can be used to transform their contained entities into 
*Pandas dataframes*. In this manner, you can easily and quickly search through lists of thousands of 
entities quickly.

.. code-block:: python

    # Get the first 1000 datasets
    df = client.datasets[:1000].DF
    # Convert to a Pandas dataframe

    df.loc[ df.title.str.contains('Iris') ]
    # Now you can use Pandas operations on the dataframe, e.g. filtering, sorting, etc.



Creating entities
============================

New entities are usually created via the `create` method of the cursor for the entity type.
For example, to create a new dataset, you can do the following:

.. code-block:: python

    red_org = c.organizations['red-org']

    dset = client.datasets.create(
        name="new-dataset", 
        title='My New Dataset', 
        organization=red_org,
        description='This is a new dataset.')
    # This will create a new dataset with the given name, title and description,
    # under organization 'red-org'.
    # The `dset` variable will be a proxy for the newly created dataset.


Providing the organization for every entity you create is sometimes tedious.
The client allows you to set a default organization for each cursor, to be
used when an organization is not specified.

.. code-block:: python

    client.datasets.default_organization = red_org
    # Now, when you create a new dataset, the default organization will be used.

    dset = client.datasets.create(
        name="another-dataset", 
        title='Another Dataset', 
        description='This is another dataset.')
    # This will create a new dataset under the default organization.    

In the same manner, we can create other types of entities. However, entities have different
defaults  and requirements. 

The default organization is not the same for all entity types. Each of datasets, workflows, processes and tools 
has its own default organization, which can be set using the `default_organization` attribute of the 
corresponding cursor.

For example, let us create a new process:

.. code-block:: python

    proc = client.processes.create()
    # This will create a new process with a default name and organization.
    # The default organization for processes is c.processes.default_organization.
    # The `proc` variable will be a proxy for the newly created process.


Creating dependent entities: resources and tasks
--------------------------------------------------

Still other entities are created differently, In particular, resources can be created
both via a call to `client.resources.create()`, but also by using the `add_resource` method
of a dataset, workflow, process or tool proxy. 
For example, to add a resource to a dataset, you can do the following:

.. code-block:: python

    dset = client.datasets['my-dataset']
    res = dset.add_resource(
        name="new-resource",
        url="https://example.com/data.csv",
        format="CSV"
    )
    # This will create a new resource with the given name and title,
    # under the specified dataset.
    # The `res` variable will be a proxy for the newly created resource.


Similarly, tasks can only be created as part of a workflow.
To create a new task in a workflow, you can do the following:

.. code-block:: python

    process = client.processes['my-process']
    task = process.run( ...   )  
    # This will execute a new task with the given name and title, under 
    # the specified process.
    # The `task` variable will be a proxy for the newly created task.



Updating entities
============================

Updating attributes through the proxy of an entity is usually straightforward.

.. code-block:: python

    dset = client.datasets['my-dataset']
    dset.title = 'My Updated Dataset'
    dset.notes = 'This is an updated dataset.'


We can also update special attributes, like the organization of the dataset:

.. code-block:: python

    red_org = client.organizations['red-org']
    dset.organization = red_org
    # This will update the organization of the dataset to 'red-org'.

Sometimes, we may want to update several attributes with a single operation.
To do this, we can use the `update` method of the proxy:

.. code-block:: python

    dset.update(
        title='My Updated Dataset',
        notes='This is an updated dataset.',
        organization=red_org
    )
    # This will update the title, notes and organization of the dataset in a single operation.

Another option is to use the special Python context manager `with` statement.

.. code-block:: python

    with deferred_sync(dset):
        dset.title = 'My Updated Dataset'
        dset.notes = 'This is an updated dataset.'
        dset.organization = red

In fact, more than one proxy can be updated in a single operation,
by using the `deferred_sync` context manager. If an exception is
raised during the update, all changes will be rolled back, and the proxies
will be restored to their previous state. 

This is useful when you want to update one or more entities via a User interface
(e.g., prompting the user for input), and you want to ensure that all updates
are applied successfully, or none at all.



Deleting entities
============================

Deleting entities is done via the `delete` method of the proxy.
For example, to delete a dataset, you can do the following:

.. code-block:: python

    dset = client.datasets['my-dataset']
    dset.delete()
    # This will delete the dataset with the given name.
    # The proxy will be invalidated, and the entity will no longer exist in the KLMS.


Soft deletion
----------------

Deleting entities from the Data Catalog should not be done very often
in a data lake, since entities are often linked and related in several complex ways.

However, sometimes it is necessary to remove entities from active status, e.g.,
when they are no longer needed. As a compromise, the STELAR KLMS allows you to
*soft-delete* entities. In fact, the `delete` method by default does not
actually remove an entity from the KLMS, but rather marks it as deleted.

Entities have the `state` attribute, which can taken only values :code:`"actiive"`
and :code:`"deleted"`. When an entity is deleted, its state is set to `"deleted"`,
and it is no longer visible in the Data Catalog. However, the entity still exists in the KLMS,
and can be restored by setting its state back to `"active"` (naturally, the entity UUID
remains the same and must be discovered somehow).

.. note::

    The `state` attribute of an *entity* should not be confused with the state of
    a *proxy* for this entity.


Purging, a.k.a. hard deletion
-------------------------------


To perform hard deletion of an entity, the `purge` attribute of the proxy can be used.
This will remove the entity from the KLMS completely, and it will no longer be accessible.

.. code-block:: python

    dset = client.datasets['my-dataset']
    dset.delete(purge=True)
    # This will remove the dataset with the given name from the KLMS completely.
    # The proxy will be invalidated, and the entity will no longer exist in the KLMS.
    # Note that this operation is irreversible, and the entity cannot be restored.

This operation may fail sometimes, e.g., if the entity is linked to other entities.
In this case, you will need to remove the links first.


Custom fields 
==============

Custom fields, also known as *extras*, are user-defined attributes that can be added 
to some types of entities in the Data Catalog. These fields are supported by the 
following entity types:

- Datasets
- Workflows
- Processes
- Tools
- Resources
- Organizations
- Groups

From the perspective of the STELAR Client, custom fields are just regular attributes
of the entity proxy. You can add, update and delete custom fields just like any other attribute.

.. code-block:: python

    dset = client.datasets['my-dataset']
    dset.my_field = 'my_custom_value'
    # This will add a custom field with the given name and value to the dataset.

    dset.update(my_field='my_updated_value')
    # This will update the custom field with the given name and value.

    del dset.my_field
    # This will delete the custom field with the given name from the dataset.


Custom fields can be any JSON-convertible value (string, number, boolean, list, dict, etc.).
You can tell what the custom fields of an entity are by looking at the `extras` attribute of the proxy.

.. note::
    
    For technical reasons, the custom fields of `Resource` proxies are in attribute `_extra`.


Tags
============================

Tags are a way to categorize and label entities in the Data Catalog. They can be used to
group entities by common characteristics, making it easier to search and filter them.

Tags are represented as strings, and should be made up as words or phrases.
Taggable entities include datasets, workflows, processes 
and tools (so-called packages). The current tags can be accessed via the `tags` attribute 
of the proxy. Two methods, `add_tags` and `remove_tags`, can be used to add or remove tags 
from the entity.

.. code-block:: python

    dset = client.datasets['my-dataset']
    if 'important' in dset.tags:
        print("This dataset is tagged as important.")
        dset.add_tags('urgent', 'confidential')
    else:
        print("This dataset is not tagged as important.")
        dset.remove_tags('urgent', 'confidential')
    # Returns a list of tags associated with the dataset.


Tag Vocabularies
-------------------

Vocabularies are named collections of tags that can be used to avoid tag name collisions
and to better designate the meaning of tags. There are many standard vocabularies used 
in library and information science, such as the Library of Congress Subject Headings (LCSH)
or the Dewey Decimal Classification (DDC).
See the wikipedia article on 
`controlled vocabularies <https://en.wikipedia.org/wiki/Controlled_vocabulary>`_
for more information.

In the STELAR KLMS, vocabularies are entities defined in the Data Catalog, and can be
used to create and manage tags. Vocabularies are shared across organizations and there
is no restriction on who can use them. Because of their shared nature, vocabularies are 
typically created and managed by the STELAR administrators, and not by regular users.

An example:

.. code-block:: python

    devstatus = client.vocabularies.create(name='devstatus', tags=[
        'planning', 'pre-alpha', 'alpha', 'beta', 
        'production', 'mature', 'inactive'])
    # This will create a new vocabulary with the given name, title and description.
    # The `vocab` variable will be a proxy for the newly created vocabulary.

    dset.add_tags('devstatus:alpha'))
    # Tag a dataset

Tags that do not belong to a vocabulary are called *free tags*. By contrast, tags that
belong to a vocabulary are called *vocabulary tags*. To distinguish the two, vocabulary tags
are always prefixed by the name of the vocabulary, e.g., `lcs:climate_change`, where `lcs` 
is the name of the vocabulary. 
On the other hand, free tags are just strings, e.g., `global warming`. They can be used
to label entities without the need to create a vocabulary.


Building a tag vocabulary
------------------------------

In order to support the compilation of tag vocabularies, the STELAR KLMS treats tags as
entities in their own right. This means that tags can be searched, created and deleted.

For example, to modify our `devstatus` vocabulary, we can do the following:

.. code-block:: python

    vocab = client.vocabularies['devstatus']

    plantag = c.tags['devstatus:planning']
    # get the proxy to the 'planning' tag in the 'devstatus' vocabulary

    plantag.delete()
    # This will remove the 'planning' tag from the vocabulary.

    c.tags.create(name='plan', vocabulary=vocab)
    # This will create a new tag in the vocabulary, with the name 'plan'.


Working with free tags
-------------------------

Free tags are just strings that do not contain the `:` (colon) separator.
Free tags can be added to entities without the need to create them explicitly.
Also, removing a free tag from all entities autmatically deletes it.

The client supports returning the list of free tags used by any entity in the 
catalog, in order to assist the user in searching for entities.

.. code-block:: python

    free_tags = client.tags[:].coll
    # Returns a list of free tags associated with entities in the catalog


Searching for entities
============================

The STELAR Client provides a powerful search functionality to find entities in the Data Catalog.
Searchable entities include datasets, workflows, processes, tools (so-called packages) and resources.
The search is performed using the `search` method of the cursor for the entity type.

Searching for resources
---------------------------

The search for resources is much simpler than for other entities, and we examine it first.
The search method takes 4 arguments:

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Argument
     - Description
   * - `query`
     -  The search query, a list of strings.
   * - `order_by`
     -  A field to order by.
   * - `offset`
     - The offset of the first result to return. Defaults to 0.
   * - `limit`
     - The max. number of results to return. Defaults to 1000.

The method returns a JSON object with the following fields:

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Field
     - Description
   * - `count`
     - The total number of results found.
   * - `results`
     - A list of JSON resources, selected by `offset` and `limit`.

The *query* parameter is  a list of strings, each of the form ``{field}:{term}``. 
Within each string, ``{field}`` is a field or extra field on the Resource domain
object.

All matches are made ignoring case; and apart from the ``hash`` field,
a term matches if it is a substring of the field's value.

If ``{field}`` is ``hash``, then an attempt is made to match the
`{term}` as a *prefix* of the ``Resource.hash`` field.

If ``{field}`` is an extra field, then an attempt is made to match against
the extra fields stored against the Resource.

Finally, when specifying more than one search criteria, the criteria are
AND-ed together.

.. note:: 
    
    Due to a Resource's extra fields being stored as a json blob, the
    match is made against the json string representation.  As such, false
    positives may occur:

    If the search criteria is: ::

        query = "field1:term1"

    Then a json blob with the string representation of: ::

        {"field1": "foo", "field2": "term1"}

    will match the search criteria!  This is a known short-coming of this
    approach.


As a convenience, the ``Resource`` cursor provides a `search_url` method, that
returns a proxy list of resources whose URL matches the given query.
For example, to find the dataset(s) that contain a specific file, you can do the following:

.. code-block:: python

    iris_datasets = {
        r.dataset 
        for r in client.resources.search_url('s3://klms-bucket/iris.csv')
        if isinstance(r.dataset, Dataset)
    }
    # This will return a set of datasets whose resource(s) point to the given file.



Searching for datasets and other packages
--------------------------------------------

The search facility for datasets and other packages is much more powerful than for resources.
Under the hood, it uses the full-text search capabilities of the STELAR KLMS implemented
by `Solr <https://solr.apache.org/>`_.

The ``search()`` method of the cursor for the entity type takes the following arguments:

.. list-table::
    :widths: 20 80
    :header-rows: 1
 
    * - Argument
      - Description
    * - `q`
      - The basic search query, a string.
    * - `bbox`
      - A bounding box filter on the ``spatial`` attribute.
    * - `fq`
      - List of filter clauses.
    * - `fl`
      - List of fields to return in the results. 
    * - `sort`
      - A field to sort the results by, e.g., ``title asc`` or ``created desc``.
    * - `offset`
      - The offset of the first result to return. Defaults to 0.
    * - `limit`
      - The max. number of results to return. Defaults to 1000.
    * - `facet`
      - A dictionary of facet field specs.


The return value is a JSON object with the following fields:

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Field
     - Description
   * - `count`
     - The total number of results found.
   * - `results`
     - A list of JSON objects representing the entities found.
   * - `search_facets`
     - A dictionary of facet counts for the fields specified in the `facet` argument.

We will now examine the arguments in more detail.

Basic search query
-----------------------------

The `q` argument is a string that contains the basic search query.
It can contain multiple terms, which are AND-ed together.
For example, to search for datasets that contain the term "iris" in 
their title or description, you can do the following:

.. code-block:: python

    results = client.datasets.search(q='iris')
    # This will return a list of datasets that contain the term "iris" in their title or description.

The query notation used is the 
`Solr query syntax <https://solr.apache.org/guide/solr/9_2/query-guide/query-syntax-and-parsers.html>`_.

Generally, the query syntax is very flexible and allows for complex queries.
Some examples of the query syntax are:

.. code-block:: python

    # Search for datasets that contain the term "iris" in their title or description
    results = client.datasets.search(q='iris')

    # Search for datasets that contain the term "iris" in their title and "flower" in their description
    results = client.datasets.search(q='title:iris AND description:flower')

    # Search for datasets that contain the term "iris" in their title or description, but not "flower"
    results = client.datasets.search(q='tags:flower AND title:iris')


An important feature of the query syntax is that it allows for ranked search.
You can see the relevance score of each result in the `score` field of the result.

.. code-block:: python

    client.datasets.search(q='iris', fl=['name', 'score'])
    # This will print the name and score of each dataset found in the search results.  

Solr supports a wide range of query syntax features, including wildcards,
phrase queries, altering the weight of terms in the final score, and more.


Bounding box filter
-----------------------------

The `bbox` argument is a bounding box filter on the `spatial` attribute of the entity.
It is a list of four numbers, representing the minimum and maximum latitude and longitude
values of the bounding box, in the order: [min_lon, min_lat, max_lon, max_lat].

Filters
-----------------------------

The `fq` argument is a list of filter clauses that can be used to filter the results.
Filtering is different from the main query, in that it does not affect the relevance score of the results.
For example, to filter the results to only include datasets that are in a specific organization,
you can do the following:

.. code-block:: python

    results = client.datasets.search(
        q='iris',
        fq=['organization:my-org']
    )
    # This will return a list of datasets that contain the term "iris" in their title or description,
    # and are in the organization "my-org".

Field list
-----------------------------
The `fl` argument is a list of fields to return in the results.
It can be used to limit the fields returned in the results,
for example, to only return the name and title of the datasets:

.. code-block:: python

    results = client.datasets.search(
        q='iris',
        fl=['name', 'title']
    )
    # This will return a list of datasets that contain the term "iris" in their title or description,
    # and only the name and title fields will be returned in the results.


Solr schema
--------------

To truly master the search capabilities of the STELAR KLMS, you should
familiarize yourself with the Solr schema used by the KLMS.
The schema is available as a JSON object obtained as:

.. code-block:: python

    solr_schema = client.GET('v2/search/schema').json()
    # This will return a JSON object representing the Solr schema for datasets.

