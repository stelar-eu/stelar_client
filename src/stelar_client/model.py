from typing import List, Dict
from IPython.core.display import HTML
from IPython.display import display
import yaml


class Resource:
    """
    A class representing a STELAR resource with metadata and additional details.

    This class is designed to hold metadata for a STELAR resource entity, making it easier
    to manage and manipulate resource information within the client application runtime.
    """

    def __init__(self, url: str, format: str, name: str) -> None:
        """
        Initialize a Resource instance with essential fields.

        Args:
            url (str): The URL where the resource is located.
            format (str): The format of the resource.
            name (str): The name of the resource.
            kwargs: Additional optional fields.
        """
        self._data = {
            "url": url,
            "format": format,
            "name": name
        }
        self._original_data = self._data.copy()  # Copy for dirty tracking
        self._dirty_fields = set()  # Track which fields have been modified

        # Additional fields
        self.id = None
        self.relation = None
        self.package_id = None
        self.modified_date = None
        self.creation_date = None
        self.description = None

    def __getattr__(self, name):
        """Handle attribute access dynamically."""
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"'Resource' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        """Handle attribute assignment dynamically."""
        if name in {"_data", "_original_data", "_dirty_fields"} or name not in self._data:
            super().__setattr__(name, value)
        else:
            # Only mark as dirty if the value actually changes
            if self._data[name] != value:
                self._data[name] = value
                self._dirty_fields.add(name)

    def is_dirty(self):
        """Check if any field is dirty."""
        return bool(self._dirty_fields)

    def changes(self):
        """Return the fields that have been modified and their changes."""
        return {
            key: (self._original_data[key], self._data[key])
            for key in self._dirty_fields
        }

    def reset_dirty(self):
        """Reset the dirty state and save the current data as original."""
        self._original_data = self._data.copy()
        self._dirty_fields.clear()

    @classmethod
    def from_dict(cls, data: dict):
        """
        A class method to construct a Resource instance from a dictionary.

        Args:
            data (dict): The dictionary containing resource metadata.

        Returns:
            Resource: A fully constructed Resource instance.
        """
        instance = cls(
            url=data.get('url'),
            format=data.get('format'),
            name=data.get('name'),
        )
        instance._populate_additional_fields(data)
        return instance

    def _populate_additional_fields(self, data: dict):
        """
        Populate additional fields of the Resource object.

        Args:
            data (dict): The dictionary containing resource metadata.
        """
        self.id = data.get('id')
        self.relation = data.get('relation')
        self.package_id = data.get('package_id')
        self.modified_date = data.get('metadata_modified')
        self.creation_date = data.get('created')
        self.description = data.get('description')
        return self

    def to_dict(self):
        """
        Convert the Resource instance into a dictionary.

        Returns:
            dict: A dictionary representation of the Resource instance.
        """
        resource_dict = {
            "resource_metadata":{
                "url": self.url,
                "format": self.format,
                "name": self.name,
            }   
        }
        return resource_dict

    def update_from_dict(self, data: dict):
        """
        Updates the current Resource instance with new data from a dictionary.

        Args:
            data (dict): A dictionary containing new data for the Resource.
        """
        for key in ['url', 'format', 'name']:
            if key in data:
                setattr(self, key, data[key])

        # Update additional fields
        self._populate_additional_fields(data)

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





class Dataset:
    """
    A class representing a STELAR dataset with metadata, resources, and additional details.
    """
    def __init__(self, title: str, notes: str, tags: List[str], extras: Dict = None, profile=None, resources: List = None):
        """
        Initializes an object of the Dataset class.
        """
        self._data = {
            "title": title,
            "notes": notes,
            "tags": tags,
            "extras": extras,
            "profile": profile,
            "resources": resources,
        }
        self._original_data = self._data.copy()  # Copy for dirty tracking
        self._dirty_fields = set()  # Track which fields have been modified

        # Additional fields
        self.id = None
        self.name = None
        self.modified_date = None
        self.creation_date = None
        self.num_tags = None
        self.num_resources = None
        self.creation_user_id = None
        self.url = None

    def __getattr__(self, name):
        """Handle attribute access dynamically."""
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"'Dataset' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        """Handle attribute assignment dynamically."""
        if name in {"_data", "_original_data", "_dirty_fields"} or name not in self._data:
            super().__setattr__(name, value)
        else:
            # Only mark as dirty if the value actually changes
            if self._data[name] != value:
                self._data[name] = value
                self._dirty_fields.add(name)

    def is_dirty(self):
        """Check if any field is dirty."""
        return bool(self._dirty_fields)

    def changes(self):
        """Return the fields that have been modified and their changes."""
        return {
            key: (self._original_data[key], self._data[key])
            for key in self._dirty_fields
        }

    def reset_dirty(self):
        """Reset the dirty state and save the current data as original."""
        self._original_data = self._data.copy()
        self._dirty_fields.clear()

    @classmethod
    def from_dict(cls, data: dict):
        """
        A class method for constructing a Dataset object from a dictionary of metadata.
        """
        tags = [tag.get("name") for tag in data.get("tags", [])]
        extras = {extra.get("key"): extra.get("value") for extra in data.get("extras", [])}
        resources = [Resource.from_dict(resource) for resource in data.get("resources", [])]

        instance = cls(
            title=data.get('title'),
            notes=data.get('notes'),
            tags=tags,
            extras=extras,
            resources=resources,
        )
        instance._populate_additional_fields(data)
        return instance

    def _populate_additional_fields(self, data: dict):
        """
        Populate additional fields of the Dataset object.
        """
        self.id = data.get('id')
        self.name = data.get('name')
        self.modified_date = data.get('metadata_modified')
        self.creation_date = data.get('metadata_created')
        self.num_tags = data.get('num_tags')
        self.num_resources = data.get('num_resources')
        self.creation_user_id = data.get('author')
        self.url = data.get('url')
        return self

    def to_dict(self):
        """
        Convert the Dataset instance into a dictionary.
        """
        if self.extras:
            json_dict = {
                "basic_metadata": {
                    "title": self.title,
                    "notes": self.notes,
                    "tags": self.tags,
                },
                "extra_metadata": self.extras,
            }
        else:
            json_dict = {
                "basic_metadata": {
                    "title": self.title,
                    "notes": self.notes,
                    "tags": self.tags,
                }
            }
        return json_dict
    

    def update_from_dict(self, data: dict):
        """
        Updates the current Dataset instance with new data from a dictionary.
        """
        for key in ['title', 'notes', 'tags', 'extras', 'resources']:
            if key in data:
                if key == 'tags':
                    tags = [tag.get("name") for tag in data.get("tags", [])]
                    setattr(self, key, tags)
                else:
                    setattr(self, key, data[key])

        # Update additional fields
        self._populate_additional_fields(data)

    
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
                    <td style="text-align: left; padding: 5px; border: 1px solid #ddd;">{resource.relation}</td>
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
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd;">{', '.join(self.tags)}</td>
                    </tr>
                    <tr style="background-color: rgba(255, 255, 255, 0.8);">
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd; font-weight: bold;">Modified Date:</td>
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd;">{self.modified_date or 'N/A'}</td>
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

    
    def __str__(self):
        dataset_info = f"Title: {self.title} | Dataset ID: {self.id} | Name: {self.name} | Tags: {self.tags} | Modified Date: {self.modified_date}\nDataset Resources:\n"
        if self.resources:
            for resource in self.resources:
                dataset_info += "\t" + str(resource) + "\n"
        else:
            dataset_info += "\tNo Resources Associated"
        return dataset_info
    
class Policy:
    """
    A class representing a STELAR policy with metadata and additional details.

    This class is designed to hold metadata for a STELAR policy entity, making it easier
    to manage and manipulate policy information within the client application runtime.
    """

    def __init__(self, policy_familiar_name: str, policy_content: str | dict ) -> None:
        """
        Initialize a Policy instance with essential fields.

        Args:
            familiar_name (str): The name of the policy to be applied.
            policy_content (str | dict): The yaml file describing the roles and permissions to be applied 
        """
        self._data = {
            "policy_familiar_name": policy_familiar_name,
        }
        self._original_data = self._data.copy()  # Copy for dirty tracking
        self._dirty_fields = set()  # Track which fields have been modified

        # Additional fields
        self.active = None
        self.created_at = None
        self.policy_uuid = None
        self.user_id = None

        self.policy_content = self._parse_policy_content(policy_content)


    def _parse_policy_content(self, content: str | dict) -> str:
        """
        Return the raw YAML content (as string or file content).

        Args:
            content (str | dict): YAML string, file path, or dictionary.

        Returns:
            str: Raw YAML content as a string.
        """
        if isinstance(content, dict):
            raise ValueError("Expected YAML content as string or file path, not a dictionary.")

        try:
            if isinstance(content, str):
                if "\n" in content or ":" in content:  # Likely a YAML string
                    return content  # Return YAML string as is
                else:  # Assume it's a file path
                    with open(content, 'r') as file:
                        return file.read() # Return raw file content as string
            else:
                raise ValueError("Content must be a YAML string or a file path.")

        except Exception as e:
            raise ValueError(f"Invalid YAML content: {e}")


    def __getattr__(self, name):
        """Handle attribute access dynamically."""
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"'Resource' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        """Handle attribute assignment dynamically."""
        if name in {"_data", "_original_data", "_dirty_fields"} or name not in self._data:
            super().__setattr__(name, value)
        else:
            # Only mark as dirty if the value actually changes
            if self._data[name] != value:
                self._data[name] = value
                self._dirty_fields.add(name)

    def is_dirty(self):
        """Check if any field is dirty."""
        return bool(self._dirty_fields)

    def changes(self):
        """Return the fields that have been modified and their changes."""
        return {
            key: (self._original_data[key], self._data[key])
            for key in self._dirty_fields
        }

    def reset_dirty(self):
        """Reset the dirty state and save the current data as original."""
        self._original_data = self._data.copy()
        self._dirty_fields.clear()

    @classmethod
    def from_dict(cls, data: dict):
        """
        A class method to construct a Policy instance from a dictionary.

        Args:
            data (dict): The dictionary containing policy metadata.

        Returns:
            Policy: A fully constructed Policy instance.
        """
        instance = cls(
            policy_familiar_name = data.get('policy_familiar_name'),
            policy_content = data.get('policy_content')
        )
        instance._populate_additional_fields(data)
        return instance

    def _populate_additional_fields(self, data: dict):
        """
        Populate additional fields of the Policy object.

        Args:
            data (dict): The dictionary containing policy metadata.
        """
        self.active = data.get('active')
        self.created_at = data.get('created_at')
        self.policy_uuid = data.get('policy_uuid')
        self.user_id = data.get('user_id')
        
        
        return self

    def to_dict(self):
        """
        Convert the Resource instance into a dictionary.

        Returns:
            dict: A dictionary representation of the Resource instance.
        """
        policy_dict = {
            "policy_familiar_name": self.policy_familiar_name,
            "yaml_content": self.policy_content
        }
        return policy_dict

    def update_from_dict(self, data: dict):
        """
        Updates the current Resource instance with new data from a dictionary.

        Args:
            data (dict): A dictionary containing new data for the Resource.
        """
        for key in ['policy_familiar_name']:
            if key in data:
                setattr(self, key, data[key])

        # Update additional fields
        self._populate_additional_fields(data)

    

    def _repr_html_(self):
        """
        Provide an HTML representation of the Policy instance for Jupyter display,
        with an extra cell named 'Policy Representation' displaying the policy content,
        and a watermark image behind the table.
        """
        # Format policy content as YAML (if present)
        policy_content_value = (
            f"<pre>{self.policy_content}</pre>"
            if self.policy_content
            else "No Policy Content"
        )

        # Build the table rows for the policy attributes
        rows = f"""
            <tr style="background-color: rgba(255, 255, 255, 0.8); color: black;">
                <td style="text-align: center; padding: 5px; border: 1px solid #ddd; font-weight: bold; width: 50%;">active:</td>
                <td style="text-align: center; padding: 5px; border: 1px solid #ddd; color: black; width: 50%;">{self.active or 'N/A'}</td>
            </tr>
            <tr style="background-color: rgba(230, 179, 255, 0.8); color: black;">
                <td style="text-align: center; padding: 5px; border: 1px solid #ddd; font-weight: bold; width: 50%;">created_at:</td>
                <td style="text-align: center; padding: 5px; border: 1px solid #ddd; color: black; width: 50%;">{self.created_at or 'N/A'}</td>
            </tr>
            <tr style="background-color: rgba(255, 255, 255, 0.8); color: black;">
                <td style="text-align: center; padding: 5px; border: 1px solid #ddd; font-weight: bold; width: 50%;">policy_familiar_name:</td>
                <td style="text-align: center; padding: 5px; border: 1px solid #ddd; color: black; width: 50%;">{self.policy_familiar_name}</td>
            </tr>
            <tr style="background-color: rgba(230, 179, 255, 0.8); color: black;">
                <td style="text-align: center; padding: 5px; border: 1px solid #ddd; font-weight: bold; width: 50%;">policy_uuid:</td>
                <td style="text-align: center; padding: 5px; border: 1px solid #ddd; color: black; width: 50%;">{self.policy_uuid or 'N/A'}</td>
            </tr>
            <tr style="background-color: rgba(255, 255, 255, 0.8); color: black;">
                <td style="text-align: center; padding: 5px; border: 1px solid #ddd; font-weight: bold; width: 50%;">user_id:</td>
                <td style="text-align: center; padding: 5px; border: 1px solid #ddd; color: black; width: 50%;">{self.user_id or 'N/A'}</td>
            </tr>
            <tr style="background-color: rgba(230, 179, 255, 0.8); color: black;">
                <td style="text-align: center; padding: 5px; border: 1px solid #ddd; font-weight: bold; width: 50%;">Policy Representation:</td>
                <td style="text-align: left; padding: 5px; border: 1px solid #ddd; color: black; width: 50%;">{policy_content_value}</td>
            </tr>
        """

        # Define the watermark image URL (Replace with your image path)
        watermark_image_url = "logo.png"

        # Build the complete HTML with "Policy Summary" centered above the table and watermark
        html = f"""
        <div style="position: relative; width: 100%; height: auto; display: flex; justify-content: flex-start; align-items: flex-start;">
            <table border="1" style="
                border-collapse: collapse;
                width: 50%;
                margin: 0;
                color: black;
                background-image: url('{watermark_image_url}');
                background-size: 60%;
                background-position: center;
                background-repeat: no-repeat;">
                <thead>
                    <tr>
                        <th colspan="2" style="text-align: center; padding: 10px; font-size: 18px; font-weight: bold; background-color: rgba(242, 242, 242, 0.8);">
                            Policy Summary
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        """
        return HTML(html)._repr_html_()



    
    def present_dictionaries_as_tables(dicts_list):
        """
        Display each dictionary as an individual HTML table with attributes on the left,
        values on the right, bolded attribute text, and black text for visibility.
        The values column is positioned closer to the split line.
        
        Parameters:
            dicts_list (list of dict): A list of dictionaries to present.
        """
        # Generate HTML tables with the desired style
        html_content = ""
        for idx, data in enumerate(dicts_list):
            # Build table rows with specified styles
            rows = "\n".join(
                f"""
                <tr style="background-color: {('rgba(255, 255, 255, 0.8)' if i % 2 == 0 else 'rgba(230, 179, 255, 0.8)')}; color: black;">
                    <td style="text-align: left; padding: 5px; border: 1px solid #ddd; font-weight: bold; color: black; width: 50%;">{key}:</td>
                    <td style="text-align: left; padding: 5px; border: 1px solid #ddd; color: black; width: 50%;">{value}</td>
                </tr>
                """ 
                for i, (key, value) in enumerate(data.items())
            )

            # Define the watermark image URL (Replace with your image path)
            watermark_image_url = "logo.png"

            # Build table HTML
            table_html = f"""
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
                                Policy Summary
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
            """
            html_content += table_html

        # Render the content
        display(HTML(html_content))



class MissingParametersError(Exception):
    pass

class DuplicateEntryError(Exception):
    pass

class STELARUnknownError(Exception):
    pass

class EntityNotFoundError(Exception):
    pass