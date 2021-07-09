from datetime import datetime

from freezegun import freeze_time

from warehouse14 import Project
from warehouse14.models import Version, File
from warehouse14.repos_dynamo import DynamoDBBackend


def test_account_save_returns_account_object(table):
    now = datetime.now()
    repo = DynamoDBBackend(table)
    actual_account = repo.account_save("userX", created=now, updated=now)

    assert actual_account.name == "userX"


@freeze_time("2021-06-20 10:00:00")
def test_account_save_sets_dates_on_initial_creation(table):
    repo = DynamoDBBackend(table)
    repo.account_save("userX")

    actual_account = repo.account_get("userX")

    assert actual_account.created == datetime.fromisoformat("2021-06-20 10:00:00")
    assert actual_account.updated == datetime.fromisoformat("2021-06-20 10:00:00")


@freeze_time("2021-06-20 10:00:00")
def test_account_save_sets_date_on_update(table):
    repo = DynamoDBBackend(table)
    repo.account_save("userX")

    actual_account = repo.account_get("userX")

    assert actual_account.name == "userX"
    assert actual_account.updated == datetime.fromisoformat("2021-06-20 10:00:00")


def test_account_save_updates_updated_value(table):
    repo = DynamoDBBackend(table)

    with freeze_time("2021-06-20 10:00:00"):
        repo.account_save("userX")

    with freeze_time("2021-06-20 11:00:00"):
        actual_account = repo.account_save("userX")

    assert actual_account.name == "userX"
    assert actual_account.created == datetime.fromisoformat("2021-06-20 10:00:00")
    assert actual_account.updated == datetime.fromisoformat("2021-06-20 11:00:00")


def test_account_get_returns_account_object(table):
    repo = DynamoDBBackend(table)
    repo.account_save("userX")

    actual_account = repo.account_get("userX")

    assert actual_account.name == "userX"


def test_account_get_return_none_for_unknown_account(table):
    repo = DynamoDBBackend(table)

    actual_user = repo.account_get("userX")

    assert actual_user is None


@freeze_time("2021-06-20 10:00:00")
def test_account_token_list_returns_saved_token(table):
    repo = DynamoDBBackend(table)
    repo.account_save("userX")
    repo.account_token_add(
        user_id="userX",
        token_id="1",
        name="token1",
        key="secret",
    )

    actual_tokens = repo.account_token_list("userX")

    assert len(actual_tokens) == 1
    assert actual_tokens[0].id == "1"
    assert actual_tokens[0].name == "token1"
    assert actual_tokens[0].key == "secret"
    assert actual_tokens[0].created == datetime.fromisoformat("2021-06-20 10:00:00")


@freeze_time("2021-06-20 10:00:00")
def test_account_token_delete_removes_token(table):
    repo = DynamoDBBackend(table)
    repo.account_save("userX")
    repo.account_token_add(
        user_id="userX",
        token_id="1",
        name="token1",
        key="secret",
    )

    repo.account_token_delete("userX", "1")

    actual_tokens = repo.account_token_list("userX")
    assert len(actual_tokens) == 0

@freeze_time("2021-06-20 10:00:00")
def test_resolve_token_returns_an_account(table):
    repo = DynamoDBBackend(table)
    repo.account_save("userX")
    repo.account_token_add(
        user_id="userX",
        token_id="1",
        name="token1",
        key="secret",
    )

    actual_account = repo.resolve_token("1")

    assert actual_account.name == "userX"


@freeze_time("2021-06-20 10:00:00")
def test_resolve_token_returns_none_for_unknown_token(table):
    repo = DynamoDBBackend(table)
    repo.account_save("userX")

    actual_account = repo.resolve_token("1")

    assert actual_account is None


@freeze_time("2021-06-20 10:00:00")
def test_project_save_returns_project_object(table):
    repo = DynamoDBBackend(table)
    actual_project = repo.project_save(
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


@freeze_time("2021-06-20 10:00:00")
def test_project_save_returns_public_project(table):
    repo = DynamoDBBackend(table)
    actual_project = repo.project_save(
        Project(
            name="projectX",
            public=True,
        )
    )

    assert actual_project.public is True


@freeze_time("2021-06-20 10:00:00")
def test_project_get_returns_project_object_by_not_normalized_name(table):
    repo = DynamoDBBackend(table)
    repo.project_save(
        Project(name="projectX", admins=[], members=[], public=False, versions={})
    )

    actual_project = repo.project_get("projectX")

    assert actual_project.normalized_name() == "projectx"
    assert actual_project.name == "projectX"
    assert len(actual_project.admins) == 0
    assert len(actual_project.members) == 0
    assert actual_project.public is False
    assert len(actual_project.versions) == 0

@freeze_time("2021-06-20 10:00:00")
def test_project_returns_project_object_by_normalized_name(table):
    repo = DynamoDBBackend(table)
    repo.project_save(
        Project(name="projectX", admins=[], members=[], public=False, versions={})
    )

    actual_project = repo.project_get(Project.normalize_name("projectX"))

    assert actual_project.normalized_name() == "projectx"
    assert actual_project.name == "projectX"
    assert len(actual_project.admins) == 0
    assert len(actual_project.members) == 0
    assert actual_project.public is False
    assert len(actual_project.versions) == 0


@freeze_time("2021-06-20 10:00:00")
def test_project_save_with_admin_and_member(table):
    repo = DynamoDBBackend(table)
    actual_project = repo.project_save(
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


@freeze_time("2021-06-20 10:00:00")
def test_project_save_remove_admin_and_member(table):
    repo = DynamoDBBackend(table)
    repo.project_save(
        Project(
            name="projectX",
            admins=["admin1"],
            members=["member1"],
            public=False,
            versions={},
        )
    )

    actual_project = repo.project_save(
        Project(name="projectX", admins=[], members=[], public=False, versions={})
    )

    assert actual_project.admins == []
    assert actual_project.members == []


@freeze_time("2021-06-20 10:00:00")
def test_project_save_with_version_and_file(table):
    repo = DynamoDBBackend(table)
    actual_project = repo.project_save(
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


@freeze_time("2021-06-20 10:00:00")
def test_project_list_returns_all_projects(table):
    repo = DynamoDBBackend(table)
    repo.project_save(Project(name="projectX"))
    repo.project_save(Project(name="projectY"))

    actual_projects = repo.project_list()

    assert actual_projects == [Project(name="projectX"), Project(name="projectY")]
