

class APIEndpointsV1:

    """
    This class contains a universal definition of the API
    endpoints. This way, any modifications made here will be
    globally updated throughout the client's classes.

    All endpoints contained here will have the api_url of the Client class
    prepended when called through the request(...) method of the BaseAPI parent class.
        
        e.g.:
        '/auth/token/issue'
        will be configured to be used as 
        http://mydomain.eu/stelar/api/v1/auth/token/issue

    Attributes:
        TOKEN_ISSUE (string): The endpoint for issuing an OAuth2.0 token
        TOKEN_VERIFY (string): The endpoint for verifying the status of an OAuth2.0 token
        TOKEN_REFRESH (string): The endpoint for issuing an OAuth2.0 token based on a refresh token already available.

        GET_USER (string): The endpoint for fetching information about a specific user by ID. 
        GET_USERS (string): The endpoint for fetching information about all users in the KLMS.

        GET_DATASET (string): The endpoint for fetching information about a specific dataset by ID.
        GET_DATASETS (string): The endpoint for fetching information about all datasets in the KLMS.
  
    """
    # Used under different HTTP schemes (POST for ISSUE, PUT for REFRESH)
    
    ### Authentication/Authorization Endpoints
    TOKEN_ISSUE = "/v1/users/token"                # POST
    TOKEN_REFRESH = "/v1/users/token"              # PUT
    TOKEN_VERIFY = "/v1/users/token"               # GET
    S3_CREDENTIALS = "/v1/users/s3/credentials"    # GET

    GET_USER = "/v1/users/"
    GET_USERS = "/v1/users"


    ### Dataset Endpoints
    GET_DATASET = "/v2/datasets/"
    GET_DATASETS = "/v2/datasets"
    GET_DATASETS_LIST = "/v2/datasets/list"
    POST_DATASETS = "/v2/datasets"
    DELETE_DATASET = "/v2/datasets/"
    PATCH_DATASET = "/v2/datasets/"

    ### Resource Endpoints
    POST_DATASET_RESOURCE = "/v2/datasets/?/resource"
    GET_DATASET_RESOURCES = "/v2/datasets/?/resources"
    GET_DATASET_RESOURCES_FILTER = "/v2/datasets/?/resources/"
    GET_RESOURCE = "/v2/resources/"
    DELETE_RESOURCE = "/v2/resources/"
    PATCH_RESOURCE = "/v2/resources/"

    ### Policy Endpoints
    POST_POLICY = "/v1/auth/policy"
    GET_POLICY_REPRESENATION = "/v1/auth/policy/representation/"
    GET_POLICY_INFO = "/v1/auth/policy/"
    GET_POLICY_LIST = "/v1/auth/policy"
    