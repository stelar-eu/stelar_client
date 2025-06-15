
************************
User Management
************************
User Management in STELAR enables the creation, updating, and deletion of users, as well as the management of their roles and permissions.

Users are treated as entities defined by attributes such as name, email, and roles and can be fetched, created, modified, or deleted with respect to STELAR's Client design principles.
A table icluding the user's attributes and their description is provided below:

.. list-table::
    :widths: 20 80
    :header-rows: 1

    * - Attribute
      - Description
    * - active
      - The current state of the user (True/False)
    * - id
      - The unique identifier of the user
    * - joined_date
      - The timestamp when the user joined
    * - full_name
      - The full name of the user
    * - email
      - The email address of the user
    * - roles
      - The roles assigned to the user
    * - username
      - The username of the user
    * - first_name
      - The first name of the user
    * - last_name
      - The last name of the user
    * - email_verified
      - Indicates whether the user's email is verified (True/False)

Managing Users
========================

Similar to other entities, every user is represented by a proxy object that can be retrieved and proccessed through 
the :code:`users` cursor that the client provides.
To retrieve all users in the system, we can use the following code:

.. code-block:: python

    from stelar import Client

    # Initialize the STELAR client
    client = Client()

    # Retrieve all users
    users = client.users[:]

.. note::

    Managing users (list, create, etc.) requires admin privileges. This means that the initialization of 
    the STELAR client should be done with admin credentials.

To retrieve a specific user, we can use their UUID or username:

.. code-block:: python

    # Retrieve a specific user by their UUID
    user = client.users["user-uuid"]
    # Retrieve a specific user by their username
    user = client.users["username"]

or by using the `get()` method:

.. code-block:: python

    # Retrieve a specific user by their UUID using get()
    user = client.users.get("user-uuid")
    # Retrieve a specific user by their username using get()
    user = client.users.get("username")

This will return a user proxy object that contains the user's metadata, such as their **name**, **email**,
**roles**, and other attributes. To get the full representation of the user in tabular format, we can type:

.. code-block:: python

    # Retrieve the metadata of the user in tabular format
    user.s
    # or retrieve the extended metadata of the user in tabular format
    user.sxl

To access specific metadata attributes, we can use the following commands:

.. code-block:: python

    # Retrieve the full name of the user
    user.full_name
    # Retrieve the email address of the user
    user.email
    # Retrieve the roles assigned to the user
    user.roles

Creating Users
-----------------

To create a new user, we can use the :code:`create()` method of the :code:`users` cursor. The method
accepts the user's attributes as keyword arguments. For example:

.. code-block:: python

    # Create a new user
    new_user = client.users.create(
        username="jdoe",
        first_name="John",
        last_name="Doe",
        email="jdoe@example.com",
        email_verified=True,
        enabled=True,
        password="securepassword",
    )

Updating Users
-----------------

Updating users follows the same approach as :ref:`updating <updating-entities>` any other entity in STELAR.
We can update a user's attributes through the user proxy object. For example, to update a user's email we can do the following:

.. code-block:: python

    # Update the user's email
    jdoe = client.users["jdoe"]
    jdoe.email = "john.doe@example.com"

Or there is the option to update several attributes at once by using the :code:`update()` method:

.. code-block:: python

    # Update multiple attributes of the user
    jdoe.update(
        first_name="Johnathan",
        last_name="Doe",
        email_verified=False,
    )

This will update the specified attributes of the user in the STELAR system.

Deleting Users
-----------------

Deleting a user is like :ref:`deleting <deleting-entities>` any other entity in STELAR. We can perform a soft deletion of a user by typing:

.. code-block:: python

    # Soft delete the user
    jdoe = client.users["jdoe"]
    jdoe.delete()

Or permanently delete a user by using the `purge=True` argument:

.. code-block:: python

    # Permanently delete the user
    jdoe = client.users["jdoe"]
    jdoe.delete(purge=True)

Managing User Roles
=========================

In STELAR, users can be assigned roles that define their permissions and access levels within the system. 
Roles are predefined sets of permissions that can be assigned to users to control their actions and 
access to resources. To manage user roles, we can use the :code:`roles()`` method of the :code:`users` 
cursor to retrieve all available roles in the system. The roles are defined in the STELAR system and can
be assigned to users as needed.

.. code-block:: python

    # Retrieve all roles in the system
    roles = client.users.roles()

Assigning Roles to Users
--------------------------

In order to assign roles to users, we first need to retrieve the user proxy object for the user we want to
modify. Then, we can use the `add_role()` to assign the user a specific role or the `append_roles()` method
to assign multiple roles at once.

.. code-block:: python

    # Assign a role to the user
    jdoe = client.users["jdoe"]
    jdoe.add_role("data_scientist")


.. code-block:: python

    # Assign multiple roles to the user
    jdoe.append_roles(["data_engineer", "ml_engineer"])

Removing Roles from Users
--------------------------

In order to remove roles from a user, we can use the `remove_role()` method:

.. code-block:: python

    # Remove a role from the user
    jdoe.remove_role("data_scientist")

To check the roles assigned to a user, we can access the :code:`roles` attribute of the user proxy object:

.. code-block:: python

    # Retrieve the roles assigned to the user
    jdoe.roles

Updating User Roles
--------------------------

Updating user roles can be done through the method `set_roles()`:

.. code-block:: python

    # Update the user's roles
    jdoe.set_roles(["data_engineer", "ml_engineer"])

This will replace the existing roles of the user with the new set of roles provided in the list.
