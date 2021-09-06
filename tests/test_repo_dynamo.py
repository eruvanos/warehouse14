from datetime import datetime

import pytest
from freezegun import freeze_time

from tests.local_dynamodb import LocalDynamoDB
from warehouse14.models import Version, File
from warehouse14.repos import Project, DBBackend
from warehouse14.repos_dynamo import DynamoDBBackend, create_table


@pytest.fixture(scope="module")
def db():
    with LocalDynamoDB() as dynamo:
        yield dynamo


@pytest.fixture
def table(db):
    table = create_table(db, "table")
    yield table
    table.delete()


# noinspection PyMethodMayBeStatic
@freeze_time("2021-06-20 10:00:00")
class DBBackendTestSuite:
    @pytest.fixture
    def imp(self):
        raise NotImplementedError("Test suite has to provide DBBackend implementation")

    def test_account_save_returns_account_object(self, imp: DBBackend):
        now = datetime.now()
        actual_account = imp.account_save("userX", created=now, updated=now)

        assert actual_account.name == "userX"

    def test_account_save_sets_dates_on_initial_creation(self, imp: DBBackend):
        imp.account_save("userX")

        actual_account = imp.account_get("userX")

        assert actual_account.created == datetime.fromisoformat("2021-06-20 10:00:00")
        assert actual_account.updated == datetime.fromisoformat("2021-06-20 10:00:00")

    def test_account_save_sets_date_on_update(self, imp: DBBackend):
        imp.account_save("userX")

        actual_account = imp.account_get("userX")

        assert actual_account.name == "userX"
        assert actual_account.updated == datetime.fromisoformat("2021-06-20 10:00:00")

    def test_account_save_updates_updated_value(self, imp: DBBackend):
        with freeze_time("2021-06-20 10:00:00"):
            imp.account_save("userX")

        with freeze_time("2021-06-20 11:00:00"):
            actual_account = imp.account_save("userX")

        assert actual_account.name == "userX"
        assert actual_account.created == datetime.fromisoformat("2021-06-20 10:00:00")
        assert actual_account.updated == datetime.fromisoformat("2021-06-20 11:00:00")

    def test_account_get_returns_account_object(self, imp: DBBackend):
        imp.account_save("userX")

        actual_account = imp.account_get("userX")

        assert actual_account.name == "userX"

    def test_account_get_return_none_for_unknown_account(self, imp: DBBackend):
        actual_user = imp.account_get("userX")

        assert actual_user is None

    def test_account_token_list_returns_saved_token(self, imp: DBBackend):
        imp.account_save("userX")
        imp.account_token_add(
            user_id="userX",
            token_id="1",
            name="token1",
            key="secret",
        )

        actual_tokens = imp.account_token_list("userX")

        assert len(actual_tokens) == 1
        assert actual_tokens[0].id == "1"
        assert actual_tokens[0].name == "token1"
        assert actual_tokens[0].key == "secret"
        assert actual_tokens[0].created == datetime.fromisoformat("2021-06-20 10:00:00")

    def test_account_token_delete_removes_token(self, imp: DBBackend):
        imp.account_save("userX")
        imp.account_token_add(
            user_id="userX",
            token_id="1",
            name="token1",
            key="secret",
        )

        imp.account_token_delete("userX", "1")

        actual_tokens = imp.account_token_list("userX")
        assert len(actual_tokens) == 0

    def test_resolve_token_returns_an_account(self, imp: DBBackend):
        imp.account_save("userX")
        imp.account_token_add(
            user_id="userX",
            token_id="1",
            name="token1",
            key="secret",
        )

        actual_account = imp.resolve_token("1")

        assert actual_account.name == "userX"

    def test_resolve_token_returns_none_for_unknown_token(self, imp: DBBackend):
        imp.account_save("userX")

        actual_account = imp.resolve_token("1")

        assert actual_account is None

    def test_group_create(self, imp: DBBackend):
        imp.group_create("group1", admins=["user1"])

        group_names = imp.account_groups_list("user1")
        assert len(group_names) == 1
        assert group_names[0] == "group1"

    def test_group_list_names_empty(self, imp: DBBackend):
        group_names = imp.account_groups_list("user1")
        assert len(group_names) == 0

    def test_group_list_names_only_for_user(self, imp: DBBackend):
        imp.group_create("group1", admins=["user1"])
        imp.group_create("group2", admins=["user2"])

        group_names = imp.account_groups_list("user1")
        assert len(group_names) == 1
        assert group_names[0] == "group1"

    def test_group_get(self, imp):
        imp.group_create("group1", admins=["user1"])
        imp.group_create("group2", admins=["user2"])

        group = imp.group_get("group1")
        assert group is not None
        assert group.name == "group1"
        assert group.admins == ["user1"]

    def test_group_delete(self, imp):
        imp.group_create("group1", admins=["user1"])

        imp.group_delete("group1")

        group = imp.group_get("group1")
        assert group is None

        groups = imp.account_groups_list("user1")
        assert groups == []

    def test_project_save_returns_project_object(self, imp: DBBackend):
        actual_project = imp.project_save(
            Project(name="projectX", admins=[], members=[], public=False, versions={})
        )

        assert actual_project is not None
        assert actual_project.name == "projectX"
        # assert actual_project.created == datetime.fromisoformat("2021-06-20 10:00:00")
        # assert actual_project.updated == datetime.fromisoformat("2021-06-20 10:00:00")
        assert len(actual_project.admins) == 0
        assert len(actual_project.members) == 0
        assert actual_project.public is False
        assert len(actual_project.versions) == 0

    def test_project_save_returns_public_project(self, imp: DBBackend):
        actual_project = imp.project_save(
            Project(
                name="projectX",
                public=True,
            )
        )

        assert actual_project.public is True

    def test_project_get_returns_project_object_by_not_normalized_name(
        self, imp: DBBackend
    ):
        imp.project_save(
            Project(name="projectX", admins=[], members=[], public=False, versions={})
        )

        actual_project = imp.project_get("projectX")

        assert actual_project.normalized_name() == "projectx"
        assert actual_project.name == "projectX"
        assert len(actual_project.admins) == 0
        assert len(actual_project.members) == 0
        assert actual_project.public is False
        assert len(actual_project.versions) == 0

    def test_project_returns_project_object_by_normalized_name(self, imp: DBBackend):
        imp.project_save(
            Project(name="projectX", admins=[], members=[], public=False, versions={})
        )

        actual_project = imp.project_get(Project.normalize_name("projectX"))

        assert actual_project.normalized_name() == "projectx"
        assert actual_project.name == "projectX"
        assert len(actual_project.admins) == 0
        assert len(actual_project.members) == 0
        assert actual_project.public is False
        assert len(actual_project.versions) == 0

    def test_project_save_with_admin_and_member(self, imp: DBBackend):
        actual_project = imp.project_save(
            Project(
                name="projectX",
                admins=["admin1"],
                members=["member1"],
                public=False,
                versions={},
            )
        )

        assert actual_project.admins == ["admin1"]
        assert actual_project.members == ["member1"]

    def test_project_save_remove_admin_and_member(self, imp: DBBackend):
        imp.project_save(
            Project(
                name="projectX",
                admins=["admin1"],
                members=["member1"],
                public=False,
                versions={},
            )
        )

        actual_project = imp.project_save(
            Project(name="projectX", admins=[], members=[], public=False, versions={})
        )

        assert actual_project.admins == []
        assert actual_project.members == []

    def test_project_save_with_version_and_file(self, imp: DBBackend):
        actual_project = imp.project_save(
            Project(
                name="projectX",
                versions={
                    "0.0.1": Version(
                        version="0.0.1",
                        metadata={"summary": "summary"},
                        files=[File(filename="test.pkg", sha256_digest="xxx")],
                    )
                },
            )
        )

        assert "0.0.1" in actual_project.versions
        assert actual_project.versions["0.0.1"].version == "0.0.1"
        assert actual_project.versions["0.0.1"].metadata["summary"] == "summary"
        assert actual_project.versions["0.0.1"].files == [
            File(filename="test.pkg", sha256_digest="xxx")
        ]

    def test_project_list_returns_all_projects(self, imp: DBBackend):
        imp.project_save(Project(name="projectX"))
        imp.project_save(Project(name="projectY"))

        actual_projects = imp.project_list()

        assert actual_projects == [Project(name="projectY"), Project(name="projectX")]


class TestDynamoDBBackend(DBBackendTestSuite):
    @pytest.fixture
    def imp(self, table):
        yield DynamoDBBackend(table)
