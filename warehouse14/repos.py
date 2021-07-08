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
        raise NotImplementedError()

    @abstractmethod
    def account_get(self, user_id: str) -> Optional[Account]:
        """
        Load non confidation data for a user
        :param user_id: ID of the user, which will be used to search for
        """
        raise NotImplementedError()

    @abstractmethod
    def account_token_add(
        self, user_id: str, token_id: str, name: str, key: str
    ) -> Optional[Token]:
        raise NotImplementedError()

    @abstractmethod
    def account_token_list(self, account_id: str) -> List[Token]:
        raise NotImplementedError()

    @abstractmethod
    def account_token_delete(self, account_id: str, token_id: str):
        raise NotImplementedError()

    @abstractmethod
    def resolve_token(self, token_id: str) -> Optional[Account]:
        """
        Look up a account by given token id.

        :param token_id: Unique token id
        :return: user_id
        """
        raise NotImplementedError

    # Project methods
    @abstractmethod
    def project_save(self, project: Project) -> Project:
        """
        Create a project in the package index
        :param project: project data
        """
        raise NotImplementedError()

    @abstractmethod
    def project_get(self, name: str) -> Optional[Project]:
        """
        Returns project by given name.

        May be overwritten by subclasses, for an optimized implementation.
        :param name: project name
        :return: Project or None
        """
        name = Project.normalize_name(name)
        for project in self.projects():
            if project.normalized_name() == name:
                return project
        else:
            return None

    @abstractmethod
    def project_list(self) -> List[Project]:
        """
        Lists all project names
        """
        raise NotImplementedError()


#
#
# class SimpleFileDB:
#     def __init__(self, root: Union[str, Path]):
#         super().__init__()
#         self._root = Path(root).expanduser().resolve()
#
#         self._project_root = self._root / "projects"
#         self._account_root = self._root / "accounts"
#
#     def _save_project(self, project: Project):
#         file = self._locate_project(project.name)
#         file.parent.mkdir(parents=True, exist_ok=True)
#
#         with file.open("wt") as f:
#             f.write(project.json())
#
#     def _locate_project(self, name: str) -> Path:
#         return self._project_root / f"{Project.normalize_name(name)}.json"
#
#     def _locate_account(self, name) -> Path:
#         return self._account_root / f"{Account.hash_name(name)}.json"
#
#     def _list_projects(self) -> List[Project]:
#         project_files = [x for x in self._project_root.glob("**/*") if x.is_file()]
#         return [self._load_project(file) for file in project_files]
#
#     def _map_token_to_account(self) -> Dict[str, Account]:
#         tokens = {}
#         account_files = [x for x in self._account_root.glob("**/*") if x.is_file()]
#         for file in account_files:
#             account = Account.parse_file(file)
#             for token in account.tokens:
#                 tokens[token.id] = account
#         return tokens
#
#     @staticmethod
#     def _load_project(file: Union[str, Path]) -> Project:
#         return Project.parse_file(Path(file))
#
#     def create_project(self, project: Project):
#         self._save_project(project)
#         return project
#
#     def update_project(self, project: Project) -> Project:
#         # TODO raise Exception
#         self._save_project(project)
#         return project
#
#     def projects(self) -> List[Project]:
#         return self._list_projects()
#
#     def delete_project(self, name: str):
#         file = self._locate_project(name)
#         file.unlink(True)
#
#     def save_account(self, account: Account) -> Optional[Account]:
#         """
#         Load non confidation data for a user
#         :param user: User object to be saved in db
#         """
#         file = self._locate_account(account.name)
#         file.parent.mkdir(parents=True, exist_ok=True)
#
#         # Store user data
#         file.write_text(account.json())
#         # TODO resolving tokens requires a different way of storage
#         # file.write_text(json.dumps({
#         #     "name": account.name
#         # }))
#
#         return account.copy()
#
#     def resolve_token(self, token_id: str) -> Optional[Account]:
#         tokens = self._map_token_to_account()
#         return tokens.get(token_id)
#
#     def load_account(self, account_id: str) -> Optional[Account]:
#         """
#         Load non confidation data for a user
#         :param user_id: ID of the user, which will be used to search for
#         """
#         file = self._locate_account(account_id)
#         if file.exists():
#             return Account.parse_file(file)
#
#         return None
