***************************************
Authorization policies
***************************************

Authorization policies in the STELAR KLMS are a set of rules that define what actions users can perform on entities within the system. As described in :ref:`authz-scheme-auth`, these policies are based on the concept of roles and permissions, where roles are assigned to users and permissions are granted to roles.
Policies can be expressed using the :ref:`policy_yaml_language`, which allows the definition of fine-grained permissions for accessing both STELAR and Storage resources.

Policies in STELAR are considered as entities, like any other entity (Datasets, Workflows, Processes etc.). They can be created and updated using the STELAR Client or the STELAR API. A policy entity contains metadata such as the name, state and creation_date, as well as the actual policy definition in YAML format.
A table of the available policy metadata is illustrated below:

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Attribute
     - Description 
   * - policy_name
     - The name of the policy
   * - active
     - The current state of the policy (True/False)
   * - id
     - The unique identifier of the policy
   * - created_at
     - The timestamp when the policy was created
   * - creator
     - The user who created the policy

Managing Policies
=================
Following the logic described at :ref:`entities-and-proxies`, for each policy, a proxy entity is created that contains the policy metadata and a reference to the actual policy definition.
Every policy proxy can be retrieved using the cursor :code:`policies`. Let's assume we want to retrieve all policies in the system. We first initialize the STELAR client:

.. code-block:: python

    from stelar import Client

    # Initialize the STELAR client
    client = Client()


.. note::
    Managing policies (list, create etc) requires admin privileges. That requires that the initialization of the STELAR client is done with the **admin** credentials.

Then we can retrieve all the available policies by typing:

.. code-block:: python

    # Retrieve all policies
    client.policies[:]

This will return the **UUIDs** of all policies in the system. We can retrieve a specific policy using its UUID, or the currently active policy by typing:

.. code-block:: python

    # Retrieve a specific policy by its UUID
    policy = client.policies["policy-uuid"]
    # Retrieve the currently active policy
    policy = client.policies["active"]

or by using the :code:`get()` method:

.. code-block:: python

    # Retrieve a specific policy by its UUID using get()
    policy = client.policies.get("policy-uuid")
    # Retrieve the currently active policy using get()
    policy = client.policies.get("active")

This will return a policy proxy object that contains the metadata of the policy, such as the **name**, **state**, **creation date**, and **creator**.
We can retrive the metadata of the policy in tabular format by typing:

.. code-block:: python

    # Retrieve the metadata of the policy in tabular format
    policy.s
    # Retrieve an extended view of the policy metadata
    policy.sxl

Or aquire a specific metadata attribute by typing, for example:

.. code-block:: python

    # Retrieve the creator of the policy
    policy.creator

To retrieve the actual policy definition in YAML format, we can use the :code:`spec` attribute of the policy proxy object:

.. code-block:: python

    # Retrieve the actual policy definition in YAML format
    policy_spec = policy.spec

The above command will return the policy definition as a byte array. We can store the policy definition in a file for further inspection or modification. For example, we can write the policy definition to a file named `policy.yaml`:

.. code-block:: python

    # Write the policy definition to a file
    with open("policy.yaml", "wb") as f:
        f.write(policy_spec)

Creating policies
------------------

To create a new policy, we can use the :code:`create()` method of the :code:`policies` cursor. The :code:`create()` method takes as an argument the desired policy definition . For example:

.. code-block:: python

    # Create a new policy
    new_policy_spec = """
    actions:
    - read: ["s3:GetObject"]
    - write: ["s3:PutObject"]
    - delete: ["s3:DeleteObject"]

    roles:
    - name: "Data-Manager"
      permissions:
        - action: "read"
          resource: "my-bucket/*"
        - action: "write"
          resource: "my-bucket/my-object-1.txt"
        - action: "delete"
          resource: "my-bucket/my-object-2.txt"
    """
    
    new_policy = client.policies.create(policy_yaml=new_policy_spec)

We can also create a policy by providing a policy specification file. For example, if we have a file named `policy.yaml` that contains the policy definition, we can type:

.. code-block:: python

    # Create a new policy from a file
    file_path = "/path/to/policy.yaml"
    with open(file_path, "rb") as f:
        new_policy = client.policies.create(policy_yaml=f.read())

This will create a new policy in the system and return a policy proxy object that contains the metadata of the newly created policy.

.. note::
    Every policy created in the system is automatically set as the active policy. Policy metadata (e.g., name, state) is defined exclusively by the system at the time of creation and cannot be modified by users. User-defined metadata is not supported.


Updating policies
-------------------
Updating a policy is similar to creating a new one. We can update the current policy definition by providing a new policy specification. For example, we want to update the currently active policy by adding a new role to it. We can do this by first retrieving the currently active policy:

.. code-block:: python

    # get the currently active policy specification
    active_policy = client.policies["active"]
    active_policy_spec = active_policy.spec

The active policy spec looks like:


.. code-block:: yaml

    actions:
    - read: ["s3:GetObject"]
    - write: ["s3:PutObject"]
    - delete: ["s3:DeleteObject"]

    roles:
    - name: "Data-Manager"
      permissions:
        - action: "read"
          resource: "my-bucket/*"
        - action: "write"
          resource: "my-bucket/my-object-1.txt"
        - action: "delete"
          resource: "my-bucket/my-object-2.txt"
    
We modify the policy specification by adding a new role. Then we apply the updated policy using the create() method again:

.. code-block:: python

    # Update the currently active policy by adding a new role
    updated_policy_spec = """
    actions:
    - read: ["s3:GetObject"]
    - write: ["s3:PutObject"]
    - delete: ["s3:DeleteObject"]

    roles:
    - name: "Data-Manager"
      permissions:
        - action: "read"
          resource: "my-bucket/*"
        - action: "write"
          resource: "my-bucket/my-object-1.txt"
        - action: "delete"
          resource: "my-bucket/my-object-2.txt"
    - name: "Data-Analyst"
      permissions:
        - action: "read"
          resource: "my-bucket/my-object-3.txt"
    """
    
    updated_policy = client.policies.create(policy_yaml=updated_policy_spec)

After applying the new policy, a :ref:`policy-recon` process is triggered by the Policy Controler that will reflect the changes made to the policy specification across all services.

.. note::
    Updating policy metadata (e.g., name, state) is not supported. This restriction ensures the integrity and consistency of policy entities within the system.

Deleting policies
-----------------
Deleteing a policy entity is not supported. Policies are considered as immutable entities in the STELAR KLMS. Instead, to effectively "delete" a policy, you can create a new policy with the desired changes and set it as the active policy. The previous policy will remain in the system but will not be used for authorization checks.
This approach allows you to maintain a history of policies while ensuring that only the most recent policy is actively enforced.