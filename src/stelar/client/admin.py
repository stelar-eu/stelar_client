from urllib.parse import urljoin

from requests.exceptions import HTTPError

from .base import BaseAPI
from .endpoints import APIEndpointsV1
from .model import DuplicateEntryError, MissingParametersError, STELARUnknownError
from .policy import Policy


class AdminAPI(BaseAPI):
    """
    Represents a class that handles administrative API actions, including policy and user management.
    """

    def get_user_by_id(self, user_id: str) -> dict:
        """Returns a user entity by UUID or by username. Requires admin rights.

        Args:
            user_id (str): User UUID or username.

        Returns:
            dict: The user representation in dictionary resembling JSON.
        """

        response = self.api_request("GET", f"v1/users/{user_id}")
        if response.status_code == 200:
            result = response.json().get("result", None)
            if result:
                userRepresentation = result.get("user", None)
                return userRepresentation
        else:
            return response.json()

    def get_users(self, offset: int = None, limit: int = None) -> dict:
        """Returns all user entities present inside the KLMS. Requires admin rights.

        Args:
            offset (int): Optional offset parameter to apply pagination logic.
            limit (int): Optional limit parameter to apply pagination. If not set, all
                users will be returned.

        Returns:
            dict: The user representations in dictionary resembling JSON.
        """

        response = self.api_request("GET", APIEndpointsV1.GET_USERS)
        if response.status_code == 200:
            result = response.json().get("result", None)
            if result:
                userRepresentation = result.get("users", None)
                return userRepresentation
        else:
            return response.json()

    def create_policy(self, policy: Policy):
        """
        Create a policy by sending its content to the specified API endpoint.

        This method sends a POST request to the API with the policy content in YAML format.
        If the policy is successfully created, the method updates the input `Policy` object with
        information about the policy details.

        Parameters
        ----------
        policy : Policy
            The `Policy` object containing the policy content to be created.

        Returns
        -------
        Policy
            A `Policy` object representing the policy details.

        Raises
        ------
        MissingParametersError
            If the API responds with a 400 status code, indicating a bad request due
            to missing or incorrect parameters.
        DuplicateEntryError
            If the API responds with a 409 status code, indicating that the dataset
            already exists.
        STELARUnknownError
            If the API responds with an unexpected error, an `STELARUnknownError`
            is raised with the error details.

        Examples
        --------
        policy = Policy(policy_content="your policy content in YAML format")
        admin.create_policy(policy)
        display(policy)

        See Also
        --------
        APIEndpointsV1.POST_POLICY : The API endpoint for creating policies.
        """

        if not policy:
            return None
        try:
            yaml_headers = {"Content-Type": "application/x-yaml"}
            policy_response = self.api_request(
                "POST",
                APIEndpointsV1.POST_POLICY,
                headers=yaml_headers,
                data=policy.policy_content,
            )
            if policy_response.status_code == 200:
                policy_repr = self.api_request(
                    "GET", urljoin(APIEndpointsV1.GET_POLICY_REPRESENATION, "active")
                )
                policy_info = self.api_request(
                    "GET", urljoin(APIEndpointsV1.GET_POLICY_INFO, "active")
                )
                if policy_info.status_code == 200 and policy_repr.status_code == 200:
                    yaml_content = policy_repr.content
                    if yaml_content.startswith(b"b'"):
                        yaml_content = yaml_content[2:-1]

                    formatted_yaml_string = yaml_content.decode("unicode_escape")
                    pjson = policy_info.json()["result"]["policy"]
                    pjson["policy_content"] = formatted_yaml_string
                    # print(yaml.dump(policy_response.json()['result']['policy']))

                    policy.update_from_dict(pjson)
                    policy.reset_dirty()
        except HTTPError as he:
            if he.response.status_code == 400:
                raise MissingParametersError("Bad Request")
            elif he.response.status_code == 409:
                raise DuplicateEntryError("Dataset Already Exists")
            else:
                raise STELARUnknownError(f"Unknown Error: {he}")

    def get_policy_info(self, filter: str):
        """
        Retrieve detailed information about a specific policy based on a filter.

        Parameters
        ----------
        filter : str
            The filter string to identify the policy.

        Returns
        -------
        Policy
            A `Policy` object representing the policy details.

        Raises
        ------
        MissingParametersError
            If the API responds with a 400 status code.
        DuplicateEntryError
            If the API responds with a 409 status code.
        STELARUnknownError
            If an unexpected error occurs.

        Examples
        --------
        policy = admin.get_policy_info("policy-filter")
        display(policy)
        """
        if not filter:
            return None
        try:
            policy_repr = self.api_request(
                "GET", urljoin(APIEndpointsV1.GET_POLICY_REPRESENATION, filter)
            )
            policy_info = self.api_request(
                "GET", urljoin(APIEndpointsV1.GET_POLICY_INFO, filter)
            )
            if policy_info.status_code == 200 and policy_repr.status_code == 200:
                yaml_content = policy_repr.content
                if yaml_content.startswith(b"b'"):
                    yaml_content = yaml_content[2:-1]

                formatted_yaml_string = yaml_content.decode("unicode_escape")
                pjson = policy_info.json()["result"]["policy"]
                pjson["policy_content"] = formatted_yaml_string
                policy_obj = Policy.from_dict(pjson)
                return policy_obj
        except HTTPError as he:
            if he.response.status_code == 400:
                raise MissingParametersError("Bad Request")
            elif he.response.status_code == 409:
                raise DuplicateEntryError("Dataset Already Exists")
            else:
                raise STELARUnknownError(f"Unknown Error: {he}")

    def get_policy_representation(self, filter: str):
        """
        Retrieve the YAML representation of a specific policy based on a filter.

        Parameters
        ----------
        filter : str
            The filter string to identify the policy.

        Returns
        -------
        None

        Raises
        ------
        MissingParametersError
            If the API responds with a 400 status code.
        DuplicateEntryError
            If the API responds with a 409 status code.
        STELARUnknownError
            If an unexpected error occurs.

        Examples
        --------
        admin.get_policy_representation("policy-filter")
        """
        if not filter:
            return None
        try:
            policy_repr = self.api_request(
                "GET", urljoin(APIEndpointsV1.GET_POLICY_REPRESENATION, filter)
            )
            if policy_repr.status_code == 200:
                yaml_content = policy_repr.content
                if yaml_content.startswith(b"b'"):
                    yaml_content = yaml_content[2:-1]

                formatted_yaml_string = yaml_content.decode("unicode_escape")
                print(formatted_yaml_string)
        except HTTPError as he:
            if he.response.status_code == 400:
                raise MissingParametersError("Bad Request")
            elif he.response.status_code == 409:
                raise DuplicateEntryError("Dataset Already Exists")
            else:
                raise STELARUnknownError(f"Unknown Error: {he}")

    def get_policy_list(self):
        """
        Retrieve a list of all available policies and present them as tables.

        Returns
        -------
        Policy List
            A List of dictionaries containing policy information(policy_uuid, policy_familiar_name)

        Raises
        ------
        MissingParametersError
            If the API responds with a 400 status code.
        DuplicateEntryError
            If the API responds with a 409 status code.
        STELARUnknownError
            If an unexpected error occurs.

        Examples
        --------
        admin.get_policy_list()
        """
        try:
            policy_response = self.api_request("GET", APIEndpointsV1.GET_POLICY_LIST)
            if policy_response.status_code == 200:
                pjson = policy_response.json()["result"]["policies"]
                policy_list = [json for json in pjson]
                return policy_list
                # Policy.present_dictionaries_as_tables(policy_list)
        except HTTPError as he:
            if he.response.status_code == 400:
                raise MissingParametersError("Bad Request")
            elif he.response.status_code == 409:
                raise DuplicateEntryError("Dataset Already Exists")
            else:
                raise STELARUnknownError(f"Unknown Error: {he}")
