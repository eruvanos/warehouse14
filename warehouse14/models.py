import datetime
import hashlib
import re
from typing import List, Optional, Dict, Literal
from urllib.parse import quote

from pydantic import BaseModel

PackageType = Literal[
    "bdist_dmg",
    "bdist_dumb",
    "bdist_egg",
    "bdist_msi",
    "bdist_rpm",
    "bdist_wheel",
    "bdist_wininst",
    "sdist",
]


#
class File(BaseModel):
    # key: str
    # python_version: str
    # requires_python: str
    # packagetype: PackageType
    # comment_text: str
    filename: str
    # size: int
    # md5_digest: str
    sha256_digest: str
    # blake2_256_digest: datetime.datetime
    # upload_time: str
    # uploaded_via: str


#
# class VersionV2(BaseModel):
#     version: str
#
#     is_prerelease: bool
#     author: str
#     author_email: str
#     maintainer: str
#     maintainer_email: str
#     home_page: str
#     license: str
#     summary: str
#     keywords: str
#     platform: str
#     download_url: str
#     requires_python: str
#     created: datetime.datetime
#     description: str
#     classifiers: List[str]
#     files: List[File]


class Version(BaseModel):
    version: str
    metadata: dict = {}
    files: List[File] = list()

    @property
    def author(self):
        return self.metadata.get("author", "")

    @property
    def maintainer(self):
        return self.metadata.get("maintainer", "")

    @property
    def summary(self):
        return self.metadata.get("summary", "")

    @property
    def description(self) -> str:
        return self.metadata.get("description", "")

    @property
    def description_content_type(self) -> str:
        return self.metadata.get("description_content_type", "")

    @property
    def classifiers(self) -> List[str]:
        return self.metadata.get("classifiers", [])


class Token(BaseModel):
    id: str
    name: str
    key: str
    created: datetime.datetime


class Account(BaseModel):
    name: str
    created: datetime.datetime
    updated: datetime.datetime

    @staticmethod
    def hash_name(name: str):
        return hashlib.sha256(name.encode()).hexdigest()


class Project(BaseModel):
    # Primary key
    def normalized_name(self) -> str:
        """Perform PEP 503 normalization"""
        return Project.normalize_name(self.name)

    name: str
    admins: List[str] = []
    members: List[str] = []
    public: bool = False
    versions: Dict[str, Version] = {}

    @property
    def latest_version(self) -> Optional[Version]:
        if not self.versions:
            return None

        version = sorted(self.versions.keys())
        return self.versions[version[-1]]

    @property
    def files(self):
        return [file for version in self.versions.values() for file in version.files]

    def add_file(self, version: str, file: File):
        self.versions.setdefault(version, Version(version=version)).files.append(file)

    def visible(self, user: str):
        return self.public or (user in self.admins + self.members)

    def is_admin(self, user: str):
        return user in self.admins

    def normalized_name_for_url(self) -> str:
        """Perform PEP 503 normalization and ensure the value is safe for URLs."""
        return quote(self.normalized_name())

    @staticmethod
    def normalize_name(name: str) -> str:
        """Perform PEP 503 normalization"""
        return re.sub(r"[-_.]+", "-", name).lower()


# class DB(ABC):
#     def get_project(self, name: str) -> Optional[Project]:
#         """
#         Returns project by given name.
#
#         May be overwritten by subclasses, for an optimized implementation.
#         :param name: project name
#         :return: Project or None
#         """
#         name = Project.normalize_name(name)
#         for project in self.projects():
#             if project.normalized_name() == name:
#                 return project
#         else:
#             return None
#
#     @abstractmethod
#     def projects(self) -> List[Project]:
#         """
#         Lists all project names
#         """
#         raise NotImplementedError()
#
#     @abstractmethod
#     def create_project(self, project: Project) -> Project:
#         """
#         Create a project in the package index
#         :param project: project data
#         """
#         raise NotImplementedError()
#
#     @abstractmethod
#     def update_project(self, project: Project) -> Project:
#         """
#         Update a project in the package index
#         :param project: project data
#         :raises Exception - in case project does not exists
#         """
#         raise NotImplementedError()
#
#     @abstractmethod
#     def delete_project(self, name: str):
#         """
#         Deletes a project from the package index
#         :param name: Name of the project
#         """
#         raise NotImplementedError()
#
#     @abstractmethod
#     def save_account(self, account: Account) -> Optional[Account]:
#         """
#         Load non confidation data for a user
#         :param user: User object to be saved in db
#         """
#         raise NotImplementedError()
#
#     @abstractmethod
#     def load_account(self, user_id: str) -> Optional[Account]:
#         """
#         Load non confidation data for a user
#         :param user_id: ID of the user, which will be used to search for
#         """
#         raise NotImplementedError()
#
#     @abstractmethod
#     def resolve_token(self, token_id: str) -> Optional[Account]:
#         """
#         Look up a account by given token id.
#
#         :param token_id: Unique token id
#         :return: user_id
#         """
#         raise NotImplementedError
#
#
# class SimpleFileDB(DB):
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
