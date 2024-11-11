

class APIEndpointsV1:

    """
    This class contains a universal definition of the API
    endpoints. This way, any modifications made here will be
    globally updated throughout the client's classes.

    Attributes:
        TOKEN_ISSUE (string): The endpoint for issuing an OAuth2.0 token
        TOKEN_VERIFY (string): The endpoint for verifying the status of an OAuth2.0 token
        TOKEN_REFRESH (string): The endpoint for issuing an OAuth2.0 token based on a refresh token already available.
  
    """
    TOKEN_ISSUE = "/auth/token/issue"
    TOKEN_VERIFY = "/auth/token/verify"
    TOKEN_REFRESH = "/auth/token/refresh"
    