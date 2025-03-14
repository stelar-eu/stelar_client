"""Generation of rich (e.g., html) representations for proxies.

Code used here follows the ipython rich display protocol, which is
described in the IPython documentation.

It is also useful in the context of Jupyter notebooks, where the
representation of objects can be customized to provide a richer
experience to the user.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from IPython.display import HTML

if TYPE_CHECKING:
    from .dataset import Dataset
    from .resource import Resource


def resource_to_html(obj: Resource) -> str:
    """Return an HTML representation of a resource.

    Provide an HTML representation of the Resource instance for Jupyter display,
    with enhanced styles, watermark, and consistent formatting.
    """
    # Define the watermark image URL (Replace with your image path)
    watermark_image_url = "logo.png"

    # Build the table HTML
    prop_style = (
        "text-align: left; padding: 5px; border: 1px solid #ddd; font-weight: bold;"
    )
    val_style = "text-align: left; padding: 5px; border: 1px solid #ddd;"

    html = f"""
    <div style="position: relative; width: 100%; height: auto; display: flex; justify-content:
                                flex-start; align-items: flex-start; margin-bottom: 20px;">
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
                    <th colspan="2" style="text-align: center; padding: 10px; font-size: 18px;
                    font-weight: bold; background-color: rgba(242, 242, 242, 0.8);">
                        Resource Summary
                    </th>
                </tr>
                <tr style="background-color: rgba(242, 242, 242, 0.8);">
                    <th style="width: 50%; text-align: center;">Attribute</th>
                    <th style="width: 50%; text-align: center;">Value</th>
                </tr>
            </thead>
            <tbody>
                <tr style="background-color: rgba(255, 255, 255, 0.8);">
                    <td style=>ID:</td>
                    <td style={val_style}>{obj.id or 'N/A'}</td>
                </tr>
                <tr style="background-color: rgba(230, 179, 255, 0.8);">
                    <td style={prop_style}>Parent Package:</td>
                    <td style={val_style}>{obj.dataset.id or 'N/A'}</td>
                </tr>
                <tr style="background-color: rgba(255, 255, 255, 0.8);">
                    <td style={prop_style}>Relation To Parent:</td>
                    <td style={val_style}>{obj.relation or 'N/A'}</td>
                </tr>
                <tr style="background-color: rgba(230, 179, 255, 0.8);">
                    <td style={prop_style}>Name:</td>
                    <td style={val_style}>{obj.name}</td>
                </tr>
                <tr style="background-color: rgba(255, 255, 255, 0.8);">
                    <td style={prop_style}>URL:</td>
                    <td style={val_style}><a href="{obj.url}" target="_blank">{obj.url}</a></td>
                </tr>
                <tr style="background-color: rgba(230, 179, 255, 0.8);">
                    <td style={prop_style}>Format:</td>
                    <td style={val_style}>{obj.format}</td>
                </tr>
                <tr style="background-color: rgba(255, 255, 255, 0.8);">
                    <td style={prop_style}>Description:</td>
                    <td style={val_style}>{obj.description or 'N/A'}</td>
                </tr>
            </tbody>
        </table>
    </div>
    """
    return HTML(html)._repr_html_()


def dataset_to_html(obj: Dataset) -> str:
    """
    Provide an HTML representation of the Dataset instance for Jupyter display,
    with enhanced styles, watermark, and consistent formatting.
    """

    prop_style = (
        "text-align: left; padding: 5px; border: 1px solid #ddd; font-weight: bold;"
    )
    val_style = "text-align: left; padding: 5px; border: 1px solid #ddd;"

    # Build the HTML for the resources table
    resources_html = ""
    if obj.resources:
        resources_html = "".join(
            f"""
                <tr style="background-color: 
                    {('rgba(255, 255, 255, 0.8)' if i % 2 == 0 else 'rgba(230, 179, 255, 0.8)')};">
                    <td style={val_style}>{resource.id or 'N/A'}</td>
                    <td style={val_style}>{resource.name}</td>
                    <td style={val_style}><a href="{resource.url}" target="_blank">{resource.url}</a></td>
                    <td style={val_style}>{resource.format}</td>
                </tr>
                """
            for i, resource in enumerate(obj.resources)
        )
    else:
        resources_html = """
                <tr style="background-color: rgba(255, 255, 255, 0.8);">
                    <td colspan='5' style="text-align: center; padding: 10px; 
                            border: 1px solid #ddd;">No Resources Associated</td>
                </tr>
            """

    # Define the watermark image URL (Replace with your image path)
    watermark_image_url = "logo.png"

    # Build the Dataset Summary table
    summary_html = f"""
        <div style="position: relative; width: 100%; height: auto; 
                    display: flex; justify-content: flex-start; 
                    align-items: flex-start; margin-bottom: 20px;">
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
                        <th colspan="2" style="text-align: center; 
                                padding: 10px; font-size: 18px; 
                                font-weight: bold; 
                                background-color: rgba(242, 242, 242, 0.8);">
                            Dataset Summary
                        </th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="background-color: rgba(255, 255, 255, 0.8);">
                        <td style={prop_style}>ID:</td>
                        <td style={val_style}>{obj.id or 'N/A'}</td>
                    </tr>
                    <tr style="background-color: rgba(230, 179, 255, 0.8);">
                        <td style={prop_style}>Title:</td>
                        <td style={val_style}>{obj.title}</td>
                    </tr>
                    <tr style="background-color: rgba(255, 255, 255, 0.8);">
                        <td style={prop_style}>Notes:</td>
                        <td style={val_style}>{obj.notes}</td>
                    </tr>
                    <tr style="background-color: rgba(230, 179, 255, 0.8);">
                        <td style={prop_style}>Tags:</td>
                        <td style={val_style}>{', '.join(['obj.tags'])}</td>
                    </tr>
                    <tr style="background-color: rgba(255, 255, 255, 0.8);">
                        <td style={prop_style}>Modified Date:</td>
                        <td style={val_style}>{obj.metadata_modified or 'N/A'}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """

    # Build the Dataset Resources table
    resources_table_html = f"""
        <div style="
            position: relative; 
            width: 100%; height: auto; 
            display: flex; justify-content: flex-start; align-items: start;">
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
                        <th colspan="5" style="text-align: center; 
                                    padding: 10px; font-size: 18px; 
                                    font-weight: bold; 
                                    background-color: rgba(242, 242, 242, 0.8);">
                            Dataset Resources
                        </th>
                    </tr>
                    <tr style="background-color: rgba(242, 242, 242, 0.8);">
                        <th style={val_style}>ID</th>
                        <th style={val_style}>Relation to Parent</th>
                        <th style={val_style}>Name</th>
                        <th style={val_style}>URL</th>
                        <th style={val_style}>Format</th>
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
