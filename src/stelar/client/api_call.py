from __future__ import annotations

"""Classes used to access the STELAR API.
"""
from functools import wraps
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
        for name, value in fields.items():
            setattr(self, name, value)

    def get_method(self, op):
        return f"{self.name}_{op}"


api_models = {
    "Dataset": {
        "name": "datset",
        "collection_name": "datsets",
    },
    "Resource": {
        "name": "resrc",
        "collection_name": "resrcs",
    },
    "Organization": {
        "name": "organization",
        "collection_name": "organizations",
    },
    "Group": {
        "name": "group",
        "collection_name": "groups",
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
}
for m in api_models:
    api_models[m] = api_model.from_value(api_models[m])


OPERATIONS = ["create", "show", "update", "patch", "delete", "list", "purge"]


class api_call(api_context):
    """Access the STELAR API using a client or a proxy"""

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

    def get_call(self, proxy_type, op):
        m = api_models[proxy_type.__name__]
        call_name = m.get_method(op)
        return getattr(self, call_name)


# Populate the api_call class with the STELAR API endpoints
def generate_list(model: api_model):
    def gen_list(self, limit=None, offset=None):
        verb = "GET"
        endpoint = f"v2/{model.collection_name}"
        params = {"limit": limit, "offset": offset}
        return self.request(verb, endpoint, params)

    name = model.get_method("list")
    gen_list.__name__ = name
    return gen_list


def generate_show(model: api_model):
    def gen_show(self, id):
        verb = "GET"
        endpoint = f"v2/{model.name}/{id}"
        return self.request(verb, endpoint)

    name = model.get_method("show")
    gen_show.__name__ = name
    return gen_show


def generate_create(model: api_model):
    def gen_create(self, **kwargs):
        verb = "POST"
        endpoint = f"v2/{model.name}"
        return self.request(verb, endpoint, json=kwargs)

    name = model.get_method("create")
    gen_create.__name__ = name
    return gen_create


def generate_update(model: api_model):
    def gen_update(self, id, **kwargs):
        verb = "PUT"
        endpoint = f"v2/{model.name}/{id}"
        return self.request(verb, endpoint, json=kwargs)

    name = model.get_method("update")
    gen_update.__name__ = name
    return gen_update


def generate_patch(model: api_model):
    def gen_patch(self, id, **kwargs):
        verb = "PATCH"
        endpoint = f"v2/{model.name}/{id}"
        return self.request(verb, endpoint, json=kwargs)

    name = model.get_method("patch")
    gen_patch.__name__ = name
    return gen_patch


def generate_delete(model: api_model):
    def gen_delete(self, id):
        verb = "DELETE"
        endpoint = f"v2/{model.name}/{id}"
        return self.request(verb, endpoint)

    name = model.get_method("delete")
    gen_delete.__name__ = name
    return gen_delete


def generate_purge(model: api_model):
    def gen_purge(self, id):
        verb = "DELETE"
        endpoint = f"v2/{model.collection_name}/{id}?purge=true"
        return self.request(verb, endpoint)

    name = model.get_method("purge")
    gen_purge.__name__ = name
    return gen_purge


for ptname in api_models:
    model = api_models[ptname]
    for op in OPERATIONS:
        call_name = model.get_method(op)
        if not hasattr(api_call, call_name):
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
                case "purge":
                    gcall = generate_purge(model)

            setattr(api_call, call_name, gcall)


class api_call_DC(api_context):
    """Class that exposes the CKAN API for the Data Catalog.

    `api_call(proxy).foo(...)`
    returns the 'result' of the CKAN API response on success,
    and raises a ProxyOperationError on failure.

    `api_call(client).foo(...)`
    does the same.
    """

    def __init__(self, arg: Proxy | Client):
        super().__init__(arg)
        self.ckan = self.client.DC

    def __getattr__(self, name):
        func = getattr(self.ckan, name)

        @wraps(func)
        def wrapped_call(*args, **kwargs):
            response = func(*args, **kwargs)
            if not response["success"]:
                err = response["error"]
                if err["__type"] == "Not Found Error":
                    raise EntityNotFound(self.proxy_type, self.proxy_id, name)
                else:
                    # Generic
                    raise ProxyOperationError(
                        self.proxy_type, self.proxy_id, name, response["error"]
                    )
            return response["result"]

        return wrapped_call

    def get_call(self, proxy_type, op):
        _map_to_ckan = {
            "Dataset": "package",
            "Resource": "resource",
            "Organization": "organization",
            "Group": "group",
            "Vocabulary": "vocabulary",
            "Tag": "tag",
            "User": "user",
        }
        ckan_type = _map_to_ckan[proxy_type.__name__]
        if ckan_type == "package" and op == "purge":
            call_name = "dataset_purge"
        else:
            call_name = f"{ckan_type}_{op}"
        return getattr(self, call_name)
