
from typing import List, Dict
from IPython.core.display import HTML
from IPython.display import display
from .proxy import ProxyObj, ProxyId, ProxyProperty, ProxyCache

class Resource(ProxyObj):
    """
    A proxy for a STELAR resource with metadata and additional details.
    """

    package_id = ProxyProperty()
    
    url = ProxyProperty(updatable=True)
    format = ProxyProperty(updatable=True)
    hash = ProxyProperty(updatable=True)
    name = ProxyProperty(updatable=True)
    resource_type = ProxyProperty(updatable=True)
    mimetype = ProxyProperty(updatable=True)
    mimetype_inner = ProxyProperty(updatable=True)
    cache_url = ProxyProperty(updatable=True)
    size = ProxyProperty(updatable=True)
    created = ProxyProperty(updatable=True)
    last_modified = ProxyProperty(updatable=True)
    cache_last_updated = ProxyProperty(updatable=True)

    

    def __str__(self):
        """
        Provide a human-readable string representation of the Resource instance.

        Returns:
            str: A string describing the resource's key attributes.
        """
        return f"Resource ID: {self.id} | Relation: {self.relation} | Name: {self.name} | URL: {self.url} | Format : {self.format}"

    def _repr_html_(self):
        """
        Provide an HTML representation of the Resource instance for Jupyter display,
        with enhanced styles, watermark, and consistent formatting.
        """
        # Define the watermark image URL (Replace with your image path)
        watermark_image_url = "logo.png"

        # Build the table HTML
        html = f"""
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
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd; font-weight: bold;">ID:</td>
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd;">{self.id or 'N/A'}</td>
                    </tr>
                    <tr style="background-color: rgba(230, 179, 255, 0.8);">
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd; font-weight: bold;">Parent Package:</td>
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd;">{self.package_id or 'N/A'}</td>
                    </tr>
                    <tr style="background-color: rgba(255, 255, 255, 0.8);">
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd; font-weight: bold;">Relation To Parent:</td>
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd;">{self.relation or 'N/A'}</td>
                    </tr>
                    <tr style="background-color: rgba(230, 179, 255, 0.8);">
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd; font-weight: bold;">Name:</td>
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd;">{self.name}</td>
                    </tr>
                    <tr style="background-color: rgba(255, 255, 255, 0.8);">
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd; font-weight: bold;">URL:</td>
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd;"><a href="{self.url}" target="_blank">{self.url}</a></td>
                    </tr>
                    <tr style="background-color: rgba(230, 179, 255, 0.8);">
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd; font-weight: bold;">Format:</td>
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd;">{self.format}</td>
                    </tr>
                    <tr style="background-color: rgba(255, 255, 255, 0.8);">
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd; font-weight: bold;">Description:</td>
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd;">{self.description or 'N/A'}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """
        return HTML(html)._repr_html_()
