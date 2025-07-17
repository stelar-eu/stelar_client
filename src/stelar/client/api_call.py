from __future__ import annotations

"""Classes used to access the STELAR API.
"""
from typing import TYPE_CHECKING, Optional

from .proxy import EntityNotFound, Proxy, ProxyCursor, ProxyList, ProxyOperationError
from .utils import client_for

if TYPE_CHECKING:
    from .client import Client

    APIContext = Proxy | Client | ProxyCursor | ProxyList


class api_context:
    def __init__(self, arg: APIContext):
        from .client import Client

        if isinstance(arg, Proxy):
            self.proxy = arg
            self.client = client_for(self.proxy)
            self.proxy_id = self.proxy.proxy_id
            self.proxy_type = type(self.proxy)
        elif isinstance(arg, (ProxyCursor, ProxyList)):
            self.proxy = None
            self.client = arg.client
            self.proxy_id = None
            self.proxy_type = arg.proxy_type
        elif isinstance(arg, Client):
            self.proxy = None
            self.client = arg
            self.proxy_id = None
            self.proxy_type = None


class api_model:
    @staticmethod
    def from_value(value):
        if isinstance(value, dict):
            return api_model(**{a: api_model.from_value(b) for a, b in value.items()})
        elif isinstance(value, list):
            return [api_model.from_value(v) for v in value]
        else:
            return value

    def __init__(self, **fields):
        self.members = []
        self.search = None
        for name, value in fields.items():
            setattr(self, name, value)

    def get_method(self, op, mm: api_model = None):
        if mm is None:
            return f"{self.name}_{op}"
        else:
            return f"{self.name}_{op}_{mm.name}"


api_models = {
    "Dataset": {
        "name": "dataset",
        "collection_name": "datasets",
        "search": "solr_search",
    },
    "Group": {
        "name": "group",
        "collection_name": "groups",
        "members": ["Dataset", "Workflow", "Tool", "Group", "User"],
    },
    "ImageRegistryToken": {
        "name": "image_registry_token",
        "collection_name": "image_registry_token",
    },
    "License": {
        "name": "license",
        "collection_name": "licenses",
    },
    "Organization": {
        "name": "organization",
        "collection_name": "organizations",
        "members": ["Dataset", "Workflow", "Tool", "Group", "User"],
    },
    "Policy": {
        "name": "policy",
        "collection_name": "policy",
    },
    "Process": {
        "name": "process",
        "collection_name": "processes",
        "members": ["Task"],
        "search": "solr_search",
    },
    "Resource": {
        "name": "resource",
        "collection_name": "resources",
        "search": "resource_search",
    },
    "Tag": {
        "name": "tag",
        "collection_name": "tags",
    },
    "Task": {
        "name": "task",
        "collection_name": "tasks",
    },
    "Tool": {
        "name": "tool",
        "collection_name": "tools",
        "search": "solr_search",
    },
    "User": {
        "name": "user",
        "collection_name": "users",
    },
    "Vocabulary": {
        "name": "vocabulary",
        "collection_name": "vocabularies",
    },
    "Workflow": {
        "name": "workflow",
        "collection_name": "workflows",
        "search": "solr_search",
    },
}
for m in api_models:
    api_models[m] = api_model.from_value(api_models[m])
for m in api_models:
    api_models[m].members = [api_models[mm] for mm in api_models[m].members]


OPERATIONS = [
    "create",
    "show",
    "update",
    "patch",
    "delete",
    "list",
    "fetch",
    "purge",
    "search",
]
MEMBER_OPERATIONS = ["add", "remove", "list_members"]
SEARCH_OPERATIONS = ["solr_search", "resource_search"]


class api_call_base(api_context):
    """Access the STELAR API using a client or a proxy.

    This is the base class for api_call, defining the generic methods
    for all types of entities.
    """

    def __init__(self, arg: APIContext):
        super().__init__(arg)

    def request(
        self, method: str, endpoint: str, params: dict = None, *, json=None, **kwargs
    ):
        if json is None:
            if kwargs:
                json = dict(kwargs)
        else:
            json = json | kwargs

        # This may raise requests exceptions
        resp = self.client.api_request(method, endpoint, params=params, json=json)
        jsout = resp.json()
        match jsout:
            case {"success": True, "result": result}:
                return result
            case {"success": False, "error": error}:
                match resp.status_code:
                    case 404:
                        try:
                            api_name = api_models[self.proxy_type.__name__].name
                            entity_purged = error["detail"]["entity"] == api_name
                        except Exception:
                            entity_purged = False

                        raise EntityNotFound(
                            self.proxy_type,
                            self.proxy_id,
                            f"{method} {endpoint}",
                            purged=entity_purged,
                        )
                    case _:
                        raise ProxyOperationError(
                            self.proxy_type,
                            self.proxy_id,
                            f"{method} {endpoint}",
                            error,
                        )
            case _:
                raise RuntimeError(
                    "Unexpected response from the server",
                    method,
                    endpoint,
                    params,
                    json,
                    jsout,
                    resp.status_code,
                    resp,
                )

    def get_call(self, proxy_type, op, member_type=None):
        m = api_models[proxy_type.__name__]
        if member_type is None:
            call_name = m.get_method(op)
        else:
            mm = api_models[member_type.__name__]
            call_name = m.get_method(op, mm)
        return getattr(self, call_name)


# Populate the api_call class with the STELAR API endpoints
def generate_list(model: api_model):
    def gen_list(self, limit=None, offset=None):
        verb = "GET"
        endpoint = f"v2/{model.collection_name}"
        params = {"limit": limit, "offset": offset}
        return self.request(verb, endpoint, params)

    return gen_list


def generate_fetch(model: api_model):
    def gen_fetch(self, limit=None, offset=None):
        verb = "GET"
        endpoint = f"v2/{model.collection_name}.fetch"
        params = {"limit": limit, "offset": offset}
        return self.request(verb, endpoint, params)

    return gen_fetch


def generate_show(model: api_model):
    def gen_show(self, id):
        verb = "GET"
        endpoint = f"v2/{model.name}/{id}"
        return self.request(verb, endpoint)

    return gen_show


def generate_create(model: api_model):
    def gen_create(self, **kwargs):
        verb = "POST"
        endpoint = f"v2/{model.name}"
        return self.request(verb, endpoint, json=kwargs)

    return gen_create


def generate_update(model: api_model):
    def gen_update(self, id, **kwargs):
        verb = "PUT"
        endpoint = f"v2/{model.name}/{id}"
        return self.request(verb, endpoint, json=kwargs)

    return gen_update


def generate_patch(model: api_model):
    def gen_patch(self, id, **kwargs):
        verb = "PATCH"
        endpoint = f"v2/{model.name}/{id}"
        return self.request(verb, endpoint, json=kwargs)

    return gen_patch


def generate_delete(model: api_model):
    def gen_delete(self, id):
        verb = "DELETE"
        endpoint = f"v2/{model.name}/{id}"
        return self.request(verb, endpoint)

    return gen_delete


def generate_purge(model: api_model):
    def gen_purge(self, id):
        verb = "DELETE"
        endpoint = f"v2/{model.name}/{id}?purge=true"
        return self.request(verb, endpoint)

    return gen_purge


def generate_add(model: api_model, mm: api_model):
    def gen_add(self, id, member_id, capacity=None):
        verb = "POST"
        endpoint = f"v2/{model.name}/{id}/{mm.name}/{member_id}"
        return self.request(verb, endpoint, json={"capacity": capacity})

    return gen_add


def generate_remove(model: api_model, mm: api_model):
    def gen_remove(self, id, member_id):
        verb = "DELETE"
        endpoint = f"v2/{model.name}/{id}/{mm.name}/{member_id}"
        return self.request(verb, endpoint)

    return gen_remove


def generate_list_members(model: api_model, mm: api_model):
    def gen_list_members(self, id, capacity=None):
        verb = "GET"
        endpoint = f"v2/{model.name}/{id}/{mm.collection_name}"
        if capacity is not None:
            endpoint += f"?capacity={capacity}"
        return self.request(verb, endpoint)

    return gen_list_members


def generate_solr_search(model: api_model):
    def gen_search(self, query_spec):
        verb = "POST"
        endpoint = f"v2/search/{model.collection_name}"
        return self.request(verb, endpoint, json=query_spec)

    return gen_search


def generate_resource_search(model: api_model):
    def gen_search(self, query_spec):
        verb = "POST"
        endpoint = f"v2/search/{model.collection_name}"
        return self.request(verb, endpoint, json=query_spec)

    return gen_search


def generate_unimplemented(model: api_model, op, mm=None):
    def gen_unimplemented(self, *args, **kwargs):
        raise NotImplementedError(api_model.name, op, args, kwargs)

    return gen_unimplemented


# Instrumenting api_call_base with the generated methods.
# Where there is no specialized method defined,
# add the generated generic method to the api_call class.
for ptname in api_models:
    model = api_models[ptname]
    for op in OPERATIONS:
        call_name = model.get_method(op)
        match op:
            case "create":
                gcall = generate_create(model)
            case "show":
                gcall = generate_show(model)
            case "update":
                gcall = generate_update(model)
            case "patch":
                gcall = generate_patch(model)
            case "delete":
                gcall = generate_delete(model)
            case "list":
                gcall = generate_list(model)
            case "fetch":
                gcall = generate_fetch(model)
            case "purge":
                gcall = generate_purge(model)
            case "search":
                if model.search == "solr_search":
                    gcall = generate_solr_search(model)
                elif model.search == "resource_search":
                    gcall = generate_resource_search(model)
                else:
                    gcall = generate_unimplemented(model, op)

        gcall.__qualname__ = f"api_call_base.{call_name}"
        gcall.__name__ = call_name
        setattr(api_call_base, call_name, gcall)

    # Add the generated member methods to the api_call class
    for mm in model.members:
        for op in MEMBER_OPERATIONS:
            call_name = model.get_method(op, mm)

            match op:
                case "add":
                    gcall = generate_add(model, mm)
                case "remove":
                    gcall = generate_remove(model, mm)
                case "list_members":
                    gcall = generate_list_members(model, mm)

            gcall.__qualname__ = f"api_call_base.{call_name}"
            gcall.__name__ = call_name
            setattr(api_call_base, call_name, gcall)


class api_call(api_call_base):
    """Class that exposes the STELAR API for a given entity.

    `api_call(proxy).foo(...)`
    returns the 'result' of the STELAR API response on success,
    and raises a ProxyOperationError on failure.

    `api_call(client).foo(...)`
    does the same.
    """

    def __init__(self, arg: APIContext):
        super().__init__(arg)

    # def tag_list(self, vocabulary_id: str = None):
    #    raise NotImplementedError("tag_list")

    def user_fetch(self, limit: int = None, offset: int = None):
        users = self.request(
            "GET", "v1/users/", params={"limit": limit, "offset": offset}
        )
        return users

    def user_list(self, limit: int = None, offset: int = None):
        return [u["username"] for u in self.user_fetch()]

    def user_show(self, id: str):
        return self.request("GET", f"v1/users/{id}")

    def user_delete(self, id):
        return self.request("DELETE", f"v1/users/{id}")

    def user_create(self, **kwargs):
        return self.request("POST", "v1/users", json=kwargs)

    def user_update(self, id, **kwargs):
        raise NotImplementedError

    def user_patch(self, id, **kwargs):
        return self.request("PATCH", f"v1/users/{id}", json=kwargs)

    def user_purge(self, id):
        raise NotImplementedError

    def roles_fetch(self, limit: int = None, offset: int = None):
        """
        Fetch roles.

        Parameters
        ----------
        limit : int, optional
            The maximum number of roles to return.
        offset : int, optional
            The offset for pagination.

        Returns
        -------
        list
            A list of dictionaries containing role information.
        """
        roles = self.request("GET", "v1/users/roles")
        match (limit, offset):
            case (None, None):
                return roles
            case (None, _):
                return roles[offset:]
            case (_, None):
                return roles[:limit]
            case (_, _):
                return roles[offset : offset + limit]

    def user_add_role(self, user_id: str, role: str):
        """
        Add a role to a user.

        Parameters
        ----------
        user_id : str
            The ID of the user to whom the role will be added.
        role : str
            The role to be added to the user.
        Returns
        -------
        dict
            A dictionary containing the current user state.
        """
        return self.request("POST", f"v1/users/{user_id}/roles/{role}")

    def user_remove_role(self, user_id: str, role: str):
        """
        Remove a role from a user.

        Parameters
        ----------
        user_id : str
            The ID of the user from whom the role will be removed.
        role : str
            The role to be removed from the user.
        Returns
        -------
        dict
            A dictionary containing the current user state.
        """
        return self.request("DELETE", f"v1/users/{user_id}/roles/{role}")

    def user_add_roles(self, user_id: str, roles: list[str]):
        """
        Add multiple roles to a user.

        Parameters
        ----------
        user_id : str
            The ID of the user to whom the roles will be added.
        roles : list[str]
            A list of roles to be added to the user.

        Returns
        -------
        dict
            A dictionary containing the current user state.
        """
        return self.request("POST", f"v1/users/{user_id}/roles", json={"roles": roles})

    def user_set_roles(self, user_id: str, roles: list[str]):
        """
        Set roles for a user, replacing any existing roles.

        Parameters
        ----------
        user_id : str
            The ID of the user whose roles will be set.
        roles : list[str]
            A list of roles to be set for the user.

        Returns
        -------
        dict
            A dictionary containing the current user state.
        """
        return self.request("PATCH", f"v1/users/{user_id}/roles", json={"roles": roles})

    def entity_search(self, proxy_type: str, query_spec: dict):
        entity_type = api_models.collection_name
        return self.request("POST", f"v2/search/{entity_type}", json=query_spec)

    def dataset_export_zenodo(self, dataset_id: str) -> dict:
        """
        Export a dataset to Zenodo.

        Parameters
        ----------
        dataset_id : str
            The ID of the dataset to export.

        Returns
        -------
        dict
            A dictionary containing the export message, ready to be sent to zenodo.
        """
        return self.request("GET", f"v2/export/zenodo/{dataset_id}")

    #
    #
    # Handling tasks
    #
    #

    def task_job_input(self, task_id: str, signature: str) -> dict:
        """Get the input for a job in a task."""
        return self.request("GET", f"v2/task/{task_id}/{signature}/input")

    def task_post_job_output(
        self, task_id: str, signature: str, output_spec: dict
    ) -> dict:
        """Get the output for a job in a task."""
        return self.request(
            "POST", f"v2/task/{task_id}/{signature}/output", json=output_spec
        )

    def task_show_jobs(self, task_id: str):
        """Show the jobs associated with a task."""
        return self.request("GET", f"v2/task/{task_id}/jobs")

    def task_show_logs(self, task_id: str):
        """Show the logs associated with a task."""
        return self.request("GET", f"v2/task/{task_id}/logs")

    def task_signature(self, task_id: str) -> dict:
        """Get the signature of a task."""
        return self.request("GET", f"v2/task/{task_id}/signature")

    def task_list(self, limit: int = None, offset: int = None, state: str = None):
        """List tasks."""

        p = {"limit": limit, "offset": offset, "state": state}

        return self.request(
            "GET", "v2/tasks", params={k: v for k, v in p.items() if v is not None}
        )

    #
    # Policies
    #

    def policy_fetch(self, limit: int = None, offset: int = None):
        """
        Fetch policies.

        Parameters
        ----------
        limit : int, optional
            The maximum number of policies to return.
        offset : int, optional
            The offset for pagination.

        Returns
        -------
        list
            A list of dictionaries containing policy information.
        """
        policies = self.request("GET", "v1/auth/policy")["policies"]
        match (limit, offset):
            case (None, None):
                return policies
            case (None, _):
                return policies[offset:]
            case (_, None):
                return policies[:limit]
            case (_, _):
                return policies[offset : offset + limit]

    def policy_list(self, limit: int = None, offset: int = None):
        """
        List all policies.

        Parameters
        ----------
        limit : int, optional
            The maximum number of policies to return.
        offset : int, optional
            The offset for pagination.

        Returns
        -------
        list
            A list of dictionaries containing policy information (policy_uuid, policy_familiar_name).
        """
        return [e["policy_uuid"] for e in self.policy_fetch(limit, offset)]

    def policy_show(self, eid: str):
        """
        Show a specific policy.

        Parameters
        ----------
        policy_uuid : str
            The UUID of the policy to show.

        Returns
        -------
        dict
            A dictionary containing the policy information.
        """
        return self.request("GET", f"v1/auth/policy/{eid}")

    def policy_create(self, policy_yaml: str | bytes):
        """
        Create a new policy.

        Parameters
        ----------
        prolicy_data: str | bytes

        Returns
        -------
        dict
            A dictionary containing the created policy information.
        """

        # We need to use the client.request method in order to send
        # the policy data as a string or bytes.
        headers = {
            "Content-Type": "application/x-yaml",
        }
        response = self.client.request(
            "POST", "api/v1/auth/policy", headers=headers, data=policy_yaml
        )
        if response.status_code in range(200, 300):
            return response.json()["result"]
        else:
            raise RuntimeError(
                "Unexpected response trying to create policy",
                policy_yaml,
                response.status_code,
                response.json(),
            )

    def policy_spec(self, policy_uuid: str) -> bytes:
        """
        Get the specification of a policy.

        Parameters
        ----------
        policy_uuid : str
            The UUID of the policy to get the specification for.

        Returns
        -------
        dict
            A dictionary containing the policy specification.
        """
        response = self.client.GET("v1/auth/policy/representation", policy_uuid)
        if response.status_code in range(200, 300):
            return response.content
        else:
            raise RuntimeError(
                "Unexpected response trying to get policy spec",
                policy_uuid,
                response.status_code,
                response,
            )

    ##
    #
    # Image Registry Tokens
    #

    def image_registry_token_list(self, limit: int = None, offset: int = None):
        """
        List image registry tokens.

        Parameters
        ----------
        limit : int, optional
            The maximum number of tokens to return.
        offset : int, optional
            The offset for pagination.

        Returns
        """
        result = self.request("GET", "v2/registry/credentials")
        tokens = list(result.keys())
        match (limit, offset):
            case (None, None):
                return tokens
            case (None, _):
                return tokens[offset:]
            case (_, None):
                return tokens[:limit]
            case (_, _):
                return tokens[offset : offset + limit]

    def image_registry_token_create(self, title: str, expiration: str | None = None):
        """
        Create a new image registry token.
        Parameters
        ----------
        title : str
            The title of the token.
        expiration : str | None, optional
            The expiration date of the token in ISO format. Defaults to None.

        Returns
        -------
        dict
            A dictionary containing the created token information.
        """
        json = {"title": title}
        # TODO: Fix the stelarapi to accept expiration as a string

        return self.request("POST", "v2/registry/credentials", json=json)

    def image_registry_token_show(self, id: str):
        """
        Show an image registry token.

        Parameters
        ----------
        uuid : str
            The UUID of the token to show.

        Returns
        -------
        dict
            A dictionary containing the token information.
        """
        return self.request("GET", f"v2/registry/credentials/{id}")

    def image_registry_token_delete(self, uuid: str):
        """
        Delete an image registry token.

        Parameters
        ----------
        uuid : str
            The UUID of the token to delete.

        Returns
        -------
        dict
            A dictionary containing the deletion result.
        """
        return self.request("DELETE", f"v2/registry/credentials/{uuid}")

    #
    #
    # Relationships
    #
    #

    def relationships_fetch(
        self,
        subject_id: str,
        rel: Optional[str] = None,
        object_id: Optional[str] = None,
        /,
    ):
        """
        Show relationships for a subject.

        """
        p = [str(subject_id)]
        if rel is not None:
            p.append(str(rel))
            if object_id is not None:
                p.append(str(object_id))

        endpoint = f"v2/relationships/{'/'.join(p)}"
        return self.request("GET", endpoint)

    def relationship_show(self, subject_id: str, rel: str, object_id: str):
        """
        Show a specific relationship.

        Parameters
        ----------
        subject_id : str
            The ID of the subject of the relationship.
        rel : str
            The type of the relationship.
        object_id : str
            The ID of the object of the relationship.

        Returns
        -------
        dict
            A dictionary containing the relationship information.
        """
        r = self.relationships_fetch(subject_id, rel, object_id)
        if not r:
            raise EntityNotFound(
                "Relationship",
                (subject_id, rel, object_id),
                "fetch",
            )
        return r[0]

    def relationship_create(
        self,
        subject_id: str,
        rel: str,
        object_id: str,
        comment: Optional[str] = None,
    ):
        """
        Create a new relationship.

        Parameters
        ----------
        subject_id : str
            The ID of the subject of the relationship.
        rel : str
            The type of the relationship.
        object_id : str
            The ID of the object of the relationship.
        comment : str, optional
            A comment for the relationship.

        Returns
        -------
        dict
            A dictionary containing the created relationship information.
        """
        return self.request(
            "POST",
            f"v2/relationship/{subject_id}/{rel}/{object_id}",
            json=dict(comment=comment),
        )

    def relationship_update(
        self,
        subject_id: str,
        rel: str,
        object_id: str,
        comment: Optional[str] = None,
    ):
        """
        Update the comment of a relationship.

        Parameters
        ----------
        subject_id : str
            The ID of the subject of the relationship.
        rel : str
            The type of the relationship.
        object_id : str
            The ID of the object of the relationship.
        comment : str, optional
            A comment for the relationship.

        Returns
        -------
        dict
            A dictionary containing the created relationship information.
        """
        return self.request(
            "PUT",
            f"v2/relationship/{subject_id}/{rel}/{object_id}",
            json=dict(comment=comment),
        )

    def relationship_delete(self, subject_id: str, rel: str, object_id: str):
        """
        Delete a relationship.

        Parameters
        ----------
        subject_id : str
            The ID of the subject of the relationship.
        rel : str
            The type of the relationship.
        object_id : str
            The ID of the object of the relationship.
        """
        self.request("DELETE", f"v2/relationship/{subject_id}/{rel}/{object_id}")

    def resource_lineage(self, resource_id: str, forward: bool) -> dict:
        """
        Get the backward lineage of a resource.

        Parameters
        ----------
        resource_id : str
            The ID of the resource to get the lineage for.
        forward : bool
            If True, get the forward lineage; if False, get the backward lineage.

        Returns
        -------
        dict
            A dictionary containing the lineage information.
        """
        if forward:
            # The API has a different endpoint for forward lineage
            # This is a temporary workaround until the API is fixed
            # to use the same endpoint for both forward and backward lineage.
            direction = "cardinality"
        else:
            direction = "lineage"
        return self.request("GET", f"v2/resource/{resource_id}/{direction}")
