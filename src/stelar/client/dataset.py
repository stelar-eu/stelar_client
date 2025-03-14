from .package import PackageCursor, PackageProxy
from .proxy import Property, RefList, StrField
from .reprstyle import dataset_to_html
from .resource import Resource
from .spatial import GeoJSON
from .utils import client_for


class Dataset(PackageProxy):
    """
    A proxy of a STELAR dataset.
    """

    title = Property(validator=StrField, updatable=True)
    url = Property(validator=StrField(nullable=True), updatable=True)
    version = Property(
        validator=StrField(nullable=True, maximum_len=100), updatable=True
    )

    # The spatial property
    spatial = Property(validator=GeoJSON(nullable=True), updatable=True)

    # Resources are dataset-specific
    resources = RefList(Resource, trigger_sync=True)

    # N.B. This has been removed from the schema
    # license_id = Property(validator=StrField(nullable=True), updatable=True)
    # profile

    # relationships_as_object
    # relationships_as subject

    def add_resource(self, **properties):
        """Add a new resource with the given properties.

        Example:  new_rsrc = d.add_resource(name="Profile", url="s3://datasets/a.json",
            format="json", mimetype="application/json")

        Args:
            **properties: The arguments to pass. See 'Resource' for details.
        """
        return client_for(self).resources.create(dataset=self, **properties)

    def _repr_html_(self):
        return dataset_to_html(self)

    def __disabled_str__(self):
        dataset_info = f"""Title: {self.title} | Dataset ID: {self.id} | Name: {self.name} | Tags: {self.tags} | Modified Date: {self.modified_date}\nDataset Resources:\n"""
        if self.resources:
            for resource in self.resources:
                dataset_info += "\t" + str(resource) + "\n"
        else:
            dataset_info += "\tNo Resources Associated"
        return dataset_info


class DatasetCursor(PackageCursor[Dataset]):
    def __init__(self, client):
        super().__init__(client, Dataset)
