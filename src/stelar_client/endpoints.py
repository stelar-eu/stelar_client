

class APIEndpointsV1:

    """
    This class contains a universal definition of the API
    endpoints. This way, any modifications made here will be
    globally updated throughout the client's classes.    
  
    """
    TOKEN_ISSUE = "/auth/token/issue"
    TOKEN_VERIFY = "/auth/token/verify"
    TOKEN_REFRESH = "/auth/token/refresh"
    