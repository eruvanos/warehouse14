from io import BytesIO

import pypitoken
import requests
import requests_html
from flask import Flask
from pytest import fixture
from wsgiadapter import WSGIAdapter

import warehouse14
from tests import PROJECT_BASE_PATH
from warehouse14 import simple_api
from warehouse14.models import Version, File, Project
from warehouse14.repos import DBBackend
from warehouse14.repos_dynamo import DynamoDBBackend
from warehouse14.storage import SimpleFileStorage

EXAMPLE_SHA256_URL = (
    "sha256=a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
)
EXAMBLE_FILE_CONTENT = b"Hello World"


@fixture
def db(table) -> DBBackend:
    return DynamoDBBackend(table)


@fixture
def storage(tmpdir):
    return SimpleFileStorage(tmpdir)


@fixture
def app(db, storage):
    app = Flask(warehouse14.__name__)
    app.debug = True
    app.templates_auto_reload = False

    app.register_blueprint(
        simple_api.create_blueprint(db=db, storage=storage, allow_project_creation=True)
    )

    return app


def given_account_exists_with_api_key(db: DBBackend):
    account = db.account_save("userX")
    token = db.account_token_add(
        user_id="userX", token_id="token-id", name="", key="sec"
    )
    api_key = pypitoken.Token.create(
        domain="warehouse14",
        identifier=token.id,
        key=token.key,
        prefix="wh14",
    ).dump()
    return account, api_key


def given_project_with_file(
    db, storage, public=False, admins=None, members=None, project_name="example-pkg"
) -> Project:
    if members is None:
        members = []
    if admins is None:
        admins = []

    project = db.project_save(
        Project(
            name=project_name,
            admins=admins,
            members=members,
            public=public,
            versions={
                "0.0.1": Version(
                    version="0.0.1",
                    metadata={},
                    files=[
                        File(
                            filename=f"{project_name}-0.0.1.tar.gz",
                            sha256_digest="a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e",
                        )
                    ],
                )
            },
        )
    )
    storage.add(
        project=project_name,
        file=f"{project_name}-0.0.1.tar.gz",
        data=BytesIO(EXAMBLE_FILE_CONTENT),
    )
    return project


@fixture
def client(app) -> requests.Session:
    session = requests.Session()
    session.mount("http://localhost", WSGIAdapter(app))
    return session


@fixture
def html_client(app) -> requests_html.HTMLSession:
    session = requests_html.HTMLSession()
    session.mount("http://localhost", WSGIAdapter(app))
    return session


def test_list_access_denied(client, db):
    res = client.get("http://localhost/simple")
    assert res.status_code == 401


def test_index_lists_no_project(app, html_client, db, storage):
    account, api_key = given_account_exists_with_api_key(db)

    res = html_client.get("http://localhost/simple/", auth=("__token__", api_key))

    assert res.status_code == 200
    assert len(res.html.links) == 0


# TODO split
def test_index_lists_projects_regarding_access(app, html_client, db, storage):
    account, api_key = given_account_exists_with_api_key(db)
    db.project_save(
        Project(
            name="public_project",
            admins=[],
            members=[],
            public=True,
            versions={"0.0.1": Version(version="0.0.1")},
        )
    )
    db.project_save(
        Project(
            name="admin_project",
            admins=[account.name],
            members=[],
            public=False,
            versions={"0.0.1": Version(version="0.0.1")},
        )
    )
    db.project_save(
        Project(
            name="member_project",
            admins=[],
            members=[account.name],
            public=False,
            versions={"0.0.1": Version(version="0.0.1")},
        )
    )
    db.project_save(
        Project(
            name="private_project",
            admins=[],
            members=[],
            public=False,
            versions={"0.0.1": Version(version="0.0.1")},
        )
    )

    res = html_client.get("http://localhost/simple/", auth=("__token__", api_key))

    assert res.status_code == 200
    assert res.html.links == {"public-project/", "admin-project/", "member-project/"}


def test_index_list_files_with_normalized_name(app, html_client, db, storage):
    account, api_key = given_account_exists_with_api_key(db)
    given_project_with_file(db, storage, project_name="ex.example-pkg_some",public=True)

    res = html_client.get(
        "http://localhost/simple/", auth=("__token__", api_key)
    )

    assert res.status_code == 200
    link = res.html.find("a")[0]
    assert link.text == "ex.example-pkg_some"
    assert link.attrs["href"] == "ex-example-pkg-some/"


def test_project_page_redirects_to_normalized_name(app, html_client, db, storage):
    account, api_key = given_account_exists_with_api_key(db)
    given_project_with_file(db, storage, project_name="ex.example-pkg_some",public=True)

    res = html_client.get(
        "http://localhost/simple/ex.example-pkg_some/", auth=("__token__", api_key), allow_redirects=False
    )

    assert res.status_code == 301

def test_project_page_list_files_of_public_project(app, html_client, db, storage):
    account, api_key = given_account_exists_with_api_key(db)
    given_project_with_file(db, storage, public=True)

    res = html_client.get(
        "http://localhost/simple/example-pkg/", auth=("__token__", api_key)
    )

    assert res.status_code == 200
    assert res.html.links == {
        f"/packages/example-pkg/example-pkg-0.0.1.tar.gz#{EXAMPLE_SHA256_URL}"
    }


def test_project_page_list_files_of_admin_project(app, html_client, db, storage):
    account, api_key = given_account_exists_with_api_key(db)
    given_project_with_file(db, storage, public=False, admins=[account.name])

    res = html_client.get(
        "http://localhost/simple/example-pkg/", auth=("__token__", api_key)
    )

    assert res.status_code == 200
    assert res.html.links == {
        "/packages/example-pkg/example-pkg-0.0.1.tar.gz#sha256=a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
    }


def test_project_page_list_files_of_member_project(app, html_client, db, storage):
    account, api_key = given_account_exists_with_api_key(db)
    given_project_with_file(db, storage, members=[account.name], public=False)

    res = html_client.get(
        "http://localhost/simple/example-pkg/", auth=("__token__", api_key)
    )

    assert res.status_code == 200
    assert res.html.links == {
        f"/packages/example-pkg/example-pkg-0.0.1.tar.gz#{EXAMPLE_SHA256_URL}"
    }



def test_project_page_denies_access_to_list_of_private_project(
    app, html_client, db, storage
):
    account, api_key = given_account_exists_with_api_key(db)
    given_project_with_file(db, storage, public=False)

    res = html_client.get(
        "http://localhost/simple/example-pkg/", auth=("__token__", api_key)
    )

    assert res.status_code == 401


def test_project_page_list_files_with_hash(app, html_client, db, storage):
    account, api_key = given_account_exists_with_api_key(db)
    given_project_with_file(db, storage, public=True)

    res = html_client.get(
        "http://localhost/simple/example-pkg/", auth=("__token__", api_key)
    )

    assert res.status_code == 200
    assert res.html.links == {
        f"/packages/example-pkg/example-pkg-0.0.1.tar.gz#sha256=a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
    }


def test_download_provides_file_of_public_with_sha(app, html_client, db, storage):
    account, api_key = given_account_exists_with_api_key(db)
    given_project_with_file(db, storage, public=True)

    res = html_client.get(
        f"http://localhost/packages/example-pkg/example-pkg-0.0.1.tar.gz#{EXAMPLE_SHA256_URL}",
        auth=("__token__", api_key),
    )

    assert res.status_code == 200
    assert res.content == EXAMBLE_FILE_CONTENT


def test_download_provides_file_of_public_project(app, html_client, db, storage):
    account, api_key = given_account_exists_with_api_key(db)
    given_project_with_file(db, storage, public=True)

    res = html_client.get(
        "http://localhost/packages/example-pkg/example-pkg-0.0.1.tar.gz",
        auth=("__token__", api_key),
    )

    assert res.status_code == 200
    assert res.content == EXAMBLE_FILE_CONTENT


def test_download_provides_file_of_admin_project(app, html_client, db, storage):
    account, api_key = given_account_exists_with_api_key(db)
    given_project_with_file(db, storage, admins=[account.name], public=False)

    res = html_client.get(
        "http://localhost/packages/example-pkg/example-pkg-0.0.1.tar.gz",
        auth=("__token__", api_key),
    )

    assert res.status_code == 200
    assert res.content == EXAMBLE_FILE_CONTENT


def test_download_provides_file_of_member_project(app, html_client, db, storage):
    account, api_key = given_account_exists_with_api_key(db)
    given_project_with_file(db, storage, members=[account.name], public=False)

    res = html_client.get(
        "http://localhost/packages/example-pkg/example-pkg-0.0.1.tar.gz",
        auth=("__token__", api_key),
    )

    assert res.status_code == 200
    assert res.content == EXAMBLE_FILE_CONTENT


def test_download_denies_access_to_file_of_private_project(
    app, html_client, db, storage
):
    account, api_key = given_account_exists_with_api_key(db)
    given_project_with_file(db, storage, public=False)

    res = html_client.get(
        "http://localhost/packages/example-pkg/example-pkg-0.0.1.tar.gz",
        auth=("__token__", api_key),
    )

    assert res.status_code == 401


def test_upload_to_admin_repo(app, html_client, db, storage):
    account, api_key = given_account_exists_with_api_key(db)
    db.project_save(
        Project(
            name="example-pkg",
            admins=[account.name],
        )
    )

    with (PROJECT_BASE_PATH / "fixtures/mypkg/dist/example-pkg-0.0.1.tar.gz").open(
        "rb"
    ) as file:
        res = html_client.post(
            "http://localhost/simple/",
            auth=("__token__", api_key),
            data={
                ":action": "file_upload",
                "protocol_version": "1",
                "sha256_digest": "xxx",
                "filetype": "sdist",
                "pyversion": "source",
                "metadata_version": "2.2",
                "name": "example-pkg",
                "version": "0.0.1",
                "summary": "Example package to test file upload.",
            },
            files={"content": file},
        )

    assert res.status_code == 200, res.text


def test_upload_to_private_repo_denied(app, html_client, db, storage):
    account, api_key = given_account_exists_with_api_key(db)
    db.project_save(
        Project(
            name="example-pkg",
            admins=[],
        )
    )

    with (PROJECT_BASE_PATH / "fixtures/mypkg/dist/example-pkg-0.0.1.tar.gz").open(
        "rb"
    ) as file:
        res = html_client.post(
            "http://localhost/simple/",
            auth=("__token__", api_key),
            data={
                ":action": "file_upload",
                "protocol_version": "1",
                "sha256_digest": "xxx",
                "filetype": "sdist",
                "pyversion": "source",
                "metadata_version": "2.2",
                "name": "example-pkg",
                "version": "0.0.1",
                "summary": "Example package to test file upload.",
            },
            files={"content": file},
        )

    assert res.status_code == 401, res.text


def test_uploaded_package_shown_with_given_hash(app, html_client, db, storage):
    account, api_key = given_account_exists_with_api_key(db)
    db.project_save(
        Project(
            name="example-pkg",
            admins=[account.name],
        )
    )

    with (PROJECT_BASE_PATH / "fixtures/mypkg/dist/example-pkg-0.0.1.tar.gz").open(
        "rb"
    ) as file:
        res = html_client.post(
            "http://localhost/simple/",
            auth=("__token__", api_key),
            data={
                ":action": "file_upload",
                "protocol_version": "1",
                "sha256_digest": "xxx",
                "filetype": "sdist",
                "pyversion": "source",
                "metadata_version": "2.2",
                "name": "example-pkg",
                "version": "0.0.1",
                "summary": "Example package to test file upload.",
            },
            files={"content": file},
        )

    res = html_client.get(
        "http://localhost/simple/example-pkg/", auth=("__token__", api_key)
    )
    assert res.html.links == {
        "/packages/example-pkg/example-pkg-0.0.1.tar.gz#sha256=xxx"
    }
