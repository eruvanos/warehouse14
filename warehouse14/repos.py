from abc import abstractmethod, ABC
from typing import List, Optional

from warehouse14.models import Project, Account, Token


class DBBackend(ABC):

    # Account methods
    @abstractmethod
    def account_save(self, user_id: str, **kwargs) -> Optional[Account]:
        """
        Load non confidential data for a user
        :param user_id: ID of the user, who is represented by a account
        :param kwargs: further properties of the user
        """

    @abstractmethod
    def account_get(self, user_id: str) -> Optional[Account]:
        """
        Load non confidation data for a user
        :param user_id: ID of the user, which will be used to search for
        """

    @abstractmethod
    def account_token_add(
        self, user_id: str, token_id: str, name: str, key: str
    ) -> Optional[Token]:
        """
        Add a new API Token to an account
        """

    @abstractmethod
    def account_token_list(self, account_id: str) -> List[Token]:
        """
        List all API tokens of account
        """

    @abstractmethod
    def account_token_delete(self, account_id: str, token_id: str):
        """
        Delete API token from account
        """

    @abstractmethod
    def resolve_token(self, token_id: str) -> Optional[Account]:
        """
        Look up a account by given token id.

        :param token_id: Unique token id
        :return: user_id
        """

    # Project methods
    @abstractmethod
    def project_save(self, project: Project) -> Project:
        """
        Create a project in the package index
        :param project: project data
        """

    def project_get(self, name: str) -> Optional[Project]:
        """
        Returns project by given name.

        May be overwritten by subclasses, for an optimized implementation.
        :param name: project name
        :return: Project or None
        """

    @abstractmethod
    def project_list(self) -> List[Project]:
        """
        Lists all project names
        """
