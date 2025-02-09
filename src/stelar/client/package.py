"""Declare utilities for package-derived types of entities.

These will be:
- datasets
- workflows
- workflow processes
- tools
"""


from stelar.client.generic import GenericCursor
from stelar.client.utils import client_for
from stelar.client.vocab import Tag


class PackageCursor(GenericCursor):
    def __init__(self, client, proxy_type):
        super().__init__(client, proxy_type)

    def with_tag(self, tagarg):
        # Need to obtain the tag ID, in order to call tag_show
        match tagarg:
            case Tag():
                raw_list = list(tagarg.get_tagged_datasets())
            case str():
                raw_list = list(client_for(self).tags[tagarg].get_tagged_datasets())
            case _:
                raise ValueError("Expected Tag or tagspec (a string)")

        # We need to filter the contents according to the proxy type...
        # This should probably happen at the server...
        return raw_list
