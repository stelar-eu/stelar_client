"""
    Implement an accessor for CKAN API that bypasses the STELAR API.
    This is useful for debugging and testing.
"""

from urllib.parse import urljoin
import requests


class CKAN:
    """A simple-minded back door to CKAN. It assumes that CKAN
       is published by the ingress on path '/dc'.

    Use as follows:
    First, ensure that there is a context in ~/.stelar containing the field
    'ckan_apitoken'. For example:
    [apitest]
    base_url=https://stelar.foo.com
    username=joe
    password=joesecret
    ckan_apitoken: 123415343416151235jgf1gh3412jk1ljh5g1l5g....

    Assuming the context is called 'apitest' (as above), do

    dc = CKAN('apitesst')
    dc.site_read()   # This is like 'ping'
    dc.help_show(name='site_read')  # shows CKAN help
    dc.package_list()
    dc.package_show(id='shakespeare_novels')

    dc.package_create(name='just_a_test', title='Just a test', owner_org='stelar-klms')
    dc.package_delete(id='just_a_test')

    ... etc. Use
    """

    def __init__(self, context="apitest", client=None):
        from .client import Client

        if client is None:
            self.client = Client(context)
        else:
            self.client = client
        self.ckanapi = urljoin(self.client._base_url, "/dc/api/3/action/")
        self.headers = {
            "Authorization": self.client._ckan_apitoken,
        }
        self.docs = {}
        self.bad_names = set()
        self.status = self.check()

    def __bool__(self) -> bool:
        return self.status

    def check(self) -> bool:
        try:
            url = urljoin(self.ckanapi, "site_read")
            resp = requests.get(url, headers=self.headers)
            result = resp.json()["result"]
            success = resp.json()["success"]
            return success and result
        except Exception:
            return False

    def __getattr__(self, name):
        if name in self.bad_names:
            raise AttributeError(name)

        # As a check that the API endpoint exists, try to fetch the
        # documentation for it. Any error in that will be translated
        # as a non-existent attribute
        try:
            doc = self.docs.get(name)
            if doc is None:
                urlh = urljoin(self.ckanapi, "help_show")
                resp = requests.post(urlh, json={"name": name}, headers=self.headers)
                doc = resp.json()["result"]
                self.docs[name] = doc
        except Exception as e:
            self.bad_names.add(name)
            raise AttributeError(name) from e

        url = urljoin(self.ckanapi, name)

        def ckan_call(json_obj={}, **kwargs):
            json = json_obj | kwargs
            resp = requests.post(url, json=json, headers=self.headers)
            return resp.json()

        ckan_call.__name__ = name
        ckan_call.__doc__ = doc
        setattr(self, name, ckan_call)

        return ckan_call

    def __repr__(self):
        return f"<CKAN {self.ckanapi} {'active' if self.status else 'bad'}>"
