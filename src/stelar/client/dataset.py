from IPython.core.display import HTML

from stelar.client.package import PackageCursor

from .generic import GenericProxy
from .proxy import (
    BoolField,
    DateField,
    ExtrasProperty,
    ExtrasProxy,
    Id,
    NameId,
    Property,
    Reference,
    RefList,
    StateField,
    StrField,
    TaggableProxy,
    TagList,
    UUIDField,
)
from .resource import Resource
from .utils import client_for


class Dataset(GenericProxy, ExtrasProxy, TaggableProxy):
    """
    A proxy of a STELAR dataset.
    """

    id = Id()
    name = NameId()
    metadata_created = Property(validator=DateField)
    metadata_modified = Property(validator=DateField)
    state = Property(validator=StateField)
    type = Property(validator=StrField)
    creator = Property(validator=UUIDField, entity_name="creator_user_id")
    private = Property(
        validator=BoolField(nullable=False, default=False), updatable=True
    )
    title = Property(validator=StrField, updatable=True)
    notes = Property(validator=StrField(nullable=True), updatable=True)
    author = Property(validator=StrField(nullable=True), updatable=True)
    author_email = Property(validator=StrField(nullable=True), updatable=True)
    maintainer = Property(validator=StrField(nullable=True), updatable=True)
    maintainer_email = Property(validator=StrField(nullable=True), updatable=True)

    # N.B. This has been removed from the schema
    # license_id = Property(validator=StrField(nullable=True), updatable=True)

    url = Property(validator=StrField(nullable=True), updatable=True)
    version = Property(
        validator=StrField(nullable=True, maximum_len=100), updatable=True
    )

    resources = RefList(Resource, trigger_sync=True)
    organization = Reference(
        "Organization",
        entity_name="owner_org",
        create_default="default_organization",
        updatable=True,
        trigger_sync=True,
    )

    groups = RefList("Group", trigger_sync=False)
    extras = ExtrasProperty()
    tags = TagList()

    # *tags: list[str]
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
        """
        Provide an HTML representation of the Dataset instance for Jupyter display,
        with enhanced styles, watermark, and consistent formatting.
        """
        # Build the HTML for the resources table
        resources_html = ""
        if self.resources:
            resources_html = "".join(
                f"""
                <tr style="background-color: {('rgba(255, 255, 255, 0.8)' if i % 2 == 0 else 'rgba(230, 179, 255, 0.8)')};">
                    <td style="text-align: left; padding: 5px; border: 1px solid #ddd;">{resource.id or 'N/A'}</td>
                    <td style="text-align: left; padding: 5px; border: 1px solid #ddd;">{resource.name}</td>
                    <td style="text-align: left; padding: 5px; border: 1px solid #ddd;"><a href="{resource.url}" target="_blank">{resource.url}</a></td>
                    <td style="text-align: left; padding: 5px; border: 1px solid #ddd;">{resource.format}</td>
                </tr>
                """
                for i, resource in enumerate(self.resources)
            )
        else:
            resources_html = """
                <tr style="background-color: rgba(255, 255, 255, 0.8);">
                    <td colspan='5' style="text-align: center; padding: 10px; border: 1px solid #ddd;">No Resources Associated</td>
                </tr>
            """

        # Define the watermark image URL (Replace with your image path)
        watermark_image_url = "logo.png"

        # Build the Dataset Summary table
        summary_html = f"""
        <div style="position: relative; width: 100%; height: auto; display: flex; justify-content: flex-start; align-items: flex-start; margin-bottom: 20px;">
            <table border="1" style="
                border-collapse: collapse;
                width: 50%;
                margin: 0;
                color: black;
                background-image: url('{watermark_image_url}');
                background-size: 20%;
                background-position: center;
                background-repeat: no-repeat;">
                <thead>
                    <tr>
                        <th colspan="2" style="text-align: center; padding: 10px; font-size: 18px; font-weight: bold; background-color: rgba(242, 242, 242, 0.8);">
                            Dataset Summary
                        </th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="background-color: rgba(255, 255, 255, 0.8);">
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd; font-weight: bold;">ID:</td>
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd;">{self.id or 'N/A'}</td>
                    </tr>
                    <tr style="background-color: rgba(230, 179, 255, 0.8);">
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd; font-weight: bold;">Title:</td>
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd;">{self.title}</td>
                    </tr>
                    <tr style="background-color: rgba(255, 255, 255, 0.8);">
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd; font-weight: bold;">Notes:</td>
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd;">{self.notes}</td>
                    </tr>
                    <tr style="background-color: rgba(230, 179, 255, 0.8);">
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd; font-weight: bold;">Tags:</td>
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd;">{', '.join(['self.tags'])}</td>
                    </tr>
                    <tr style="background-color: rgba(255, 255, 255, 0.8);">
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd; font-weight: bold;">Modified Date:</td>
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd;">{self.metadata_modified or 'N/A'}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """

        # Build the Dataset Resources table
        resources_table_html = f"""
        <div style="position: relative; width: 100%; height: auto; display: flex; justify-content: flex-start; align-items: start;">
            <table border="1" style="
                border-collapse: collapse;
                width: 80%;
                margin: 0;
                color: black;
                background-image: url('{watermark_image_url}');
                background-size: 20%;
                background-position: center;
                background-repeat: no-repeat;">
                <thead>
                    <tr>
                        <th colspan="5" style="text-align: center; padding: 10px; font-size: 18px; font-weight: bold; background-color: rgba(242, 242, 242, 0.8);">
                            Dataset Resources
                        </th>
                    </tr>
                    <tr style="background-color: rgba(242, 242, 242, 0.8);">
                        <th style="text-align: left; padding: 5px; border: 1px solid #ddd;">ID</th>
                        <th style="text-align: left; padding: 5px; border: 1px solid #ddd;">Relation to Parent</th>
                        <th style="text-align: left; padding: 5px; border: 1px solid #ddd;">Name</th>
                        <th style="text-align: left; padding: 5px; border: 1px solid #ddd;">URL</th>
                        <th style="text-align: left; padding: 5px; border: 1px solid #ddd;">Format</th>
                    </tr>
                </thead>
                <tbody>
                    {resources_html}
                </tbody>
            </table>
        </div>
        """

        # Combine both tables into the final HTML
        html = f"{summary_html}<br>{resources_table_html}"
        return HTML(html)._repr_html_()

    def __disabled_str__(self):
        dataset_info = f"""Title: {self.title} | Dataset ID: {self.id} | Name: {self.name} | Tags: {self.tags} | Modified Date: {self.modified_date}\nDataset Resources:\n"""
        if self.resources:
            for resource in self.resources:
                dataset_info += "\t" + str(resource) + "\n"
        else:
            dataset_info += "\tNo Resources Associated"
        return dataset_info


class DatasetCursor(PackageCursor):
    def __init__(self, client):
        super().__init__(client, Dataset)
