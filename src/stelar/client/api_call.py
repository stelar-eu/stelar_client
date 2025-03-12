from __future__ import annotations

"""Classes used to access the STELAR API.
"""
from typing import TYPE_CHECKING

from .proxy import EntityNotFound, Proxy, ProxyCursor, ProxyList, ProxyOperationError
from .utils import client_for

if TYPE_CHECKING:
    from .client import Client


class api_context:
    def __init__(self, arg: Proxy | Client):
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
    "Resource": {
        "name": "resource",
        "collection_name": "resources",
        "search": "resource_search",
    },
    "Organization": {
        "name": "organization",
        "collection_name": "organizations",
        "members": ["Dataset", "Workflow", "Tool", "Group", "User"],
    },
    "Group": {
        "name": "group",
        "collection_name": "groups",
        "members": ["Dataset", "Workflow", "Tool", "Group", "User"],
    },
    "Vocabulary": {
        "name": "vocabulary",
        "collection_name": "vocabularies",
    },
    "Tag": {
        "name": "tag",
        "collection_name": "tags",
    },
    "User": {
        "name": "user",
        "collection_name": "users",
    },
    "Process": {
        "name": "process",
        "collection_name": "processes",
        "members": ["Task"],
        "search": "solr_search",
    },
    "Task": {
        "name": "tasks",
        "collection_name": "tasks",
    },
    "Workflow": {
        "name": "workflow",
        "collection_name": "workflows",
        "search": "solr_search",
    },
    "Tool": {
        "name": "tool",
        "collection_name": "tools",
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

    def __init__(self, arg: Proxy | Client):
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
                        raise EntityNotFound(
                            self.proxy_type, self.proxy_id, f"{method} {endpoint}"
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

    def __init__(self, arg: Proxy | Client):
        super().__init__(arg)

    # def tag_list(self, vocabulary_id: str = None):
    #    raise NotImplementedError("tag_list")

    def user_fetch(self, limit: int = None, offset: int = None):
        response = self.request(
            "GET", "v1/users/", params={"limit": limit, "offset": offset}
        )
        users = response["users"]
        return users

    def user_list(self, limit: int = None, offset: int = None):
        return [u["id"] for u in self.user_fetch()]

    def user_show(self, id: str):
        response = self.request("GET", f"v1/users/{id}")
        return response["user"]

    def user_delete(self, id):
        return self.request("DELETE", f"v1/users/{id}")

    def user_create(self, **kwargs):
        raise NotImplementedError

    def user_update(self, id, **kwargs):
        raise NotImplementedError

    def user_patch(self, id, **kwargs):
        raise NotImplementedError

    def user_purge(self, id):
        raise NotImplementedError

    def entity_search(self, proxy_type: str, query_spec: dict):
        entity_type = api_models.collection_name
        return self.request("POST", f"v2/search/{entity_type}", json=query_spec)
