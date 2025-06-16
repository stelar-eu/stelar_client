from .base import BaseAPI
from .policy import PolicyCursor
from .user import UserCursor


class AdminAPI(BaseAPI):
    """
    Represents a class that handles administrative API actions, including policy and user management.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.policies = PolicyCursor(self)
        self.users = UserCursor(self)
