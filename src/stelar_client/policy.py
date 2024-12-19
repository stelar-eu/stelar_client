from typing import List, Dict
from IPython.core.display import HTML
from IPython.display import display

    
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
        self.policy_content = data.get('policy_content')
        
        
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


