
===================================
Quick start with the STELAR client
===================================

The STELAR client is a Python library that allows you either 
to interact with the STELAR KLMS either via a command line, 
such as a Jupyter notebook or an IPython shell, or,
it can be used as a library in your Python code, for example
in a GUI built using streamlit <https://streamlit.io/>.

In this quick start guide, we will show you how to install the client,
how to configure it, and how to use it to interact with the STELAR KLMS.

Installation
============

The client is available on PyPI, so you can install it using pip:

.. code-block:: bash

    pip install stelar_client

Configuration
=============
Before you can use the client, you need to configure it.
The client uses a configuration file to store the connection details
to the STELAR KLMS. The configuration file is a config file that
declares a number of :dfn:`contexts`. Each context is a set of
connection details to a specific instance of the STELAR KLMS.

The default location of the configuration file is in the user's home
directory, and by default it is called `.stelar`. So, if you are on a Unix-like
system, the configuration file will be `~/.stelar`.

Here is an example of a configuration file:

.. code-block:: config

    [default]
    url = https://stelar.example.com
    username = myuser
    password = mypassword

    [dev]
    url = https://dev.stelar.example.com
    username = mydevuser
    password = mydevpassword

This file declares two contexts: `default` and `dev`. The `default` context
is the default context that the client will use if no context is specified.
The `dev` context is an example of a context that you can use to connect to
a development instance of the STELAR KLMS.

Creating a client
=================

Once you have installed the client and created a configuration file,
you can start using the client. The first step is to import the client
and create a client object. Here is an example of how to do this:

.. code-block:: python

    from stelar.client import Client

    client = Client()

This will create a client object that is connected to the `default` context
in the configuration file. If you want to connect to a different context,
you can specify the context when creating the client object:

.. code-block:: python

    client = Client(context='dev')
    # same as  client = Client('dev')

Accessing the KLMS
------------------

Once you have created the client object, you can start using it to interact
with the STELAR KLMS. Let us start by looking at a list of available datasets:

.. code-block:: pycon

    client.datasets[:]
    Out[3]: Dataset['em_test_dataset', 'nyse_stock_dataset', 'shakespeare_novels', 'stock_movements_nyse', 'synopses_experiment', 'synopses_experiment_2', 'word_count_results']

This will return a list of datasets that are available in the STELAR KLMS.
Assume that we are interested in the NYSE stock dataset. We can get the 
dataset as follows:

.. code-block:: pycon

    nyse_stock_dataset = client.datasets['nyse_stock_dataset']
    nyse_stock_dataset
    Out[5]: <Dataset nyse_stock_dataset CLEAN>

This will return a *proxy object* that represents the NYSE stock dataset.
Via this proxy object, we can examine the dataset, download it, or upload
new data to it. For example, we can get a list of the columns in the dataset:

.. code-block:: pycon

    nyse_stock_dataset.sl
    Out[6]:
    author                                                           admin
    author_email                                            info@stelar.gr
    creator                           f04457e8-2cad-4893-ae30-4ac2f432df0e
    extras                                                              {}
    groups                                                              ()
    id                                7c67f766-e839-441a-98f2-3b3e5fcf62a5
    maintainer                                                        vsam
    maintainer_email                                                  None
    metadata_created                            2025-02-12 09:16:25.598958
    metadata_modified                           2025-03-13 11:56:23.441754
    name                                                nyse_stock_dataset
    notes                A collection of 1 year long historical data of...
    organization                                               stelar-klms
    private                                                          False
    resources            (Resource ID: f3579502-2113-4821-9bf4-9d540c12...
    spatial                                                           None
    state                                                           active
    tags                                   (AAPL, NVDA, NYSE, SDE, Stocks)
    title                                               NYSE Stock Dataset
    type                                                           dataset
    url                                                          stelar.de
    version                                                          0.0.3
    Name: Dataset (CLEAN), dtype: object

This will return a list of metadata fields for the dataset. The metadata
is displayed as a *pandas Series object*, which is useful for interactive
exploration of the dataset as a whole. In a programmatic context, you can
access the metadata fields as attributes of the proxy object:

.. code-block:: pycon

    nyse_stock_dataset.title
    Out[7]: 'NYSE Stock Dataset'

You can also update the metadata fields of the dataset:

.. code-block:: pycon

    nyse_stock_dataset.title = 'NYSE Stock Dataset 2025'
    nyse_stock_dataset.title
    Out[9]: 'NYSE Stock Dataset 2025'

You can examine resources that this dataset may contain:

.. code-block:: pycon

    nyse_stock_dataset.resources
    Out[10]: Resource[UUID('f3579502-2113-4821-9bf4-9d540c129b31'), UUID('e5bf830e-3b21-4fae-9991-d90486b5d06e')]

The value returned is **proxy list**, that is, a list-like object that
can be used to access proxy objects. For example, to get the **proxy object**
for the first resource in the list, you can do:

.. code-block:: pycon

    nyse_stock_dataset.resources[0]
    Out[11]: <Resource f3579502-2113-4821-9bf4-9d540c129b31 CLEAN>

We can examine this proxy object like we did with the dataset proxy object:

.. code-block:: pycon

    nyse_stock_dataset.resources[0].sl
    Out[12]:
    _extras                {'datastore_active': False, 'relation': 'owned'}
    cache_last_updated                                                 None
    cache_url                                                          None
    created                                      2025-02-12 09:17:10.411495
    dataset                                              nyse_stock_dataset
    description                                                            
    format                                                              CSV
    hash                                                                   
    id                                 f3579502-2113-4821-9bf4-9d540c129b31
    last_modified                                                      None
    metadata_modified                            2025-02-12 09:17:40.649473
    mimetype                                                       text/csv
    mimetype_inner                                                     None
    name                                              AAPL 1y Stock History
    position                                                              0
    resource_type                                                      None
    size                                                               None
    state                                                            active
    url                   s3://klms-bucket/raw-data/stocks/aapl_intraday...
    url_type                                                           None

This is quite a lot of information, but a resource is mainly about files in
the KLMS. This particular resource is a CSV file that contains the 1-year
historical stock data for the company AAPL. The `url` field contains the
location of the file in the KLMS.

Items:
  * download the file via pandas
  * edit the data frame
  * create a new dataset
  * publish some limited dataframe under the new dataset

