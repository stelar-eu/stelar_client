import pathlib

import pandas as pd

from stelar.client import pdutils
from stelar.client.mutils import is_s3url, s3spec_to_pair
from stelar.client.pdutils import infer_format

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

    def add_dataframe(
        self, df: pd.DataFrame, s3path: str, format: str = None, **kwargs
    ) -> Resource:
        """Add a DataFrame as a resource to the dataset.

        Args:
            df (pd.DataFrame): The DataFrame to add.
            s3path (str): The S3 path to save the DataFrame.
            format (str): The format of the file. If not specified, an attempt will
                be done to infer it.
            **kwargs: Additional keyword arguments to pass to the write_dataframe function
        """

        # Infer the format of the file to save
        fmt = infer_format(s3path, format)
        if fmt is None:
            raise ValueError("Could not infer the format of the file to save.")

        # Collect properties of the new resource
        if not is_s3url(s3path):
            raise ValueError("The path must be an S3 URL.")
        bucket, path = s3spec_to_pair(s3path)
        stem = pathlib.PurePosixPath(path).stem

        rsrc = self.add_resource(
            name=stem,
            url=s3path,
            format=fmt,
            mimetype=f"application/{fmt}",
            description=df.describe().to_json(),
            columns=df.columns.tolist(),
            rows=len(df),
            size=df.memory_usage().sum(),
            relation="owned",
        )

        try:
            pdutils.write_dataframe(client_for(self), df, s3path, format=fmt, **kwargs)
        except Exception as e:
            rsrc.delete()
            raise e

        return rsrc

    def read_dataframe(self, format: str | None = None, **kwargs):
        """Read the dataset as a DataFrame.

        Note: the dataframe need not be stored in

        Args:
            format (str): The format of the file to read. If not specified, the format will be
                inferred from the file extension.
            kwargs (dict): Additional keyword arguments to pass to the read.

        Returns:
            pd.DataFrame: The DataFrame read from the dataset.
        """

        if not self.url:
            raise ValueError("The dataset URL is nil.")

        if (not format) and hasattr(self, "format"):
            format = self.format

        fmt = infer_format(self.url, format)
        if fmt is None:
            raise ValueError("Could not infer the format of the file to save.")

        return pdutils.read_dataframe(client_for(self), self.url, format=fmt, **kwargs)

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

    def publish_file(
        self,
        s3file: str,
        format: str | None = None,
        *,
        resource: dict | None = {},
        **dataset_properties,
    ) -> Dataset:
        """Publish a new dataset in the catalog for a single file in Storage.

        The main input to this call is a single file in Storage, identified by its S3 URL.
        By default, this call will create a new dataset in the catalog and a new resource,
        which will be initialized by provided properties and also by infering properties
        by analyzing the given S3 URL.

        If the :code:`resource` parameter is set explicitly to None, no resource will be created;
        instead, the dataset will be assigned the given S3 URL as its URL.

        Args:
            s3path (str): The S3 path to the file.
            format (str): The format of the file. If not specified, an attempt will
                be done to infer it.
            resource_properties (dict): Properties of the new resource. If this is set explicitly
                to None, no resource will be created; instead, the dataset
            **dataset_properties: Properties of the new dataset.
        """

    def publish_dataframe(
        self,
        df: pd.DataFrame,
        s3path: str,
        format: str | None = None,
        *,
        write={},
        **properties,
    ) -> Dataset:
        """Publish a DataFrame as a new dataset.

        The dataframe will be stored at the given path in the format specified
        by the 'format' argument. If the format is not specified, an attempt will
        be done to infer it from the file extension of the s3path.

        Additional arguments to the pandas write method (DataFrame.to_{format})
        can be passed using the 'write' argument.

        Args:
            df (pd.DataFrame): The DataFrame to publish.
            s3path (str): The S3 path to save the DataFrame.
            format (str): The format of the file. If not specified, an attempt will
                be done to infer it.
            write (dict): Keyword arguments to pass to the write_dataframe function
            **properties: Properties of the new dataset.
        """

        # Infer the format of the file to save
        fmt = infer_format(s3path, format)
        if fmt is None:
            raise ValueError("Could not infer the format of the file to save.")

        # Collect properties of the new resource
        if not is_s3url(s3path):
            raise ValueError("The path must be an S3 URL.")
        bucket, path = s3spec_to_pair(s3path)
        stem = pathlib.PurePosixPath(path).stem

        if "name" not in properties:
            properties["name"] = stem
        if "title" not in properties:
            properties["title"] = stem
        if "author" not in properties:
            properties["author"] = self.client.users.current_user.fullname
            properties["author_email"] = self.client.users.current_user.email
        if "maintainer" not in properties:
            properties["maintainer"] = self.client.users.current_user.fullname
            properties["maintainer_email"] = self.client.users.current_user.email

        properties["url"] = s3path
        properties["columns"] = df.columns.tolist()
        properties["rows"] = len(df)
        properties["size"] = df.memory_usage().sum()
        properties["format"] = fmt
        properties["mimetype"] = f"application/{fmt}"
        properties["description"] = df.describe().to_json()

        dataset = self.create(**properties)
        try:
            pdutils.write_dataframe(self.client, df, s3path, format=fmt, **write)
        except Exception as e:
            dataset.delete(purge=True)
            raise e
        return dataset
