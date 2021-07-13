import secrets
from operator import attrgetter

import flask_login
import requests_html
from flask import Response, redirect
from pytest import fixture
from requests_html import HTMLResponse
from wsgiadapter import WSGIAdapter

from tests.test_simple_api import given_project_with_file
from warehouse14 import create_app, DBBackend, Authenticator
from warehouse14.repos_dynamo import DynamoDBBackend
from warehouse14.storage import S3Storage


class MockAuthenticator(Authenticator):
    def init_app(self, app):
        @app.get("/_auto_login/<user_id>")
        def _login(user_id):
            login_manager: flask_login.LoginManager = app.login_manager
            user = login_manager._user_callback(user_id)
            flask_login.login_user(user)
            return f"Logged in as {flask_login.current_user}"

    def logout(self) -> Response:
        flask_login.logout_user()
        return redirect("/")


@fixture
def db(table) -> DBBackend:
    return DynamoDBBackend(table)


@fixture
def storage(bucket):
    return S3Storage(bucket)


@fixture
def app(db, storage):
    app = create_app(db, storage, MockAuthenticator())
    app.debug = True
    app.secret_key = secrets.token_hex(16)
    return app


@fixture
def html_client(app) -> requests_html.HTMLSession:
    session = requests_html.HTMLSession()
    session.mount("http://localhost", WSGIAdapter(app))
    return session


def _login(html_client, user_id):
    html_client.get(f"http://localhost/_auto_login/{user_id}")


def test_admin_add_new_restricted(html_client, app, db, storage):
    _login(html_client, "user1")
    project = given_project_with_file(db, storage, admins=["admin1"])

    res: HTMLResponse = html_client.post(
        f"http://localhost/projects/{project.name}/admins", data={"username": "admin2"}
    )

    assert res.status_code == 401


def test_admin_add_new(html_client, app, db, storage):
    _login(html_client, "admin1")
    project = given_project_with_file(db, storage, admins=["admin1"])

    res: HTMLResponse = html_client.post(
        f"http://localhost/projects/{project.name}/admins", data={"username": "admin2"}
    )

    assert res.status_code == 200, res.text
    assert list(map(attrgetter("text"), res.html.find(".admin"))) == [
        "admin1",
        "admin2",
    ]


def test_admin_add_duplicate(html_client, app, db, storage):
    _login(html_client, "admin1")
    project = given_project_with_file(db, storage, admins=["admin1"])

    res: HTMLResponse = html_client.post(
        f"http://localhost/projects/{project.name}/admins", data={"username": "admin1"}
    )

    assert res.status_code == 200, res.text
    assert list(map(attrgetter("text"), res.html.find(".admin"))) == ["admin1"]


def test_admin_add_empty(html_client, app, db, storage):
    _login(html_client, "admin1")
    project = given_project_with_file(db, storage, admins=["admin1"])

    res: HTMLResponse = html_client.post(
        f"http://localhost/projects/{project.name}/admins", data={"username": ""}
    )

    assert res.status_code == 200, res.text
    assert list(map(attrgetter("text"), res.html.find(".admin"))) == ["admin1"]


def test_admin_add_missing_field(html_client, app, db, storage):
    _login(html_client, "admin1")
    project = given_project_with_file(db, storage, admins=["admin1"])

    res: HTMLResponse = html_client.post(
        f"http://localhost/projects/{project.name}/admins", data={}
    )

    assert res.status_code == 200, res.text
    assert list(map(attrgetter("text"), res.html.find(".admin"))) == ["admin1"]


def test_admin_remove(html_client, app, db, storage):
    _login(html_client, "admin1")
    project = given_project_with_file(db, storage, admins=["admin1", "admin2"])

    res: HTMLResponse = html_client.get(
        f"http://localhost/projects/{project.name}/admins/admin2/delete"
    )

    assert res.status_code == 200, res.text
    assert list(map(attrgetter("text"), res.html.find(".admin"))) == ["admin1"]

def test_admin_remove_not_existing(html_client, app, db, storage):
    _login(html_client, "admin1")
    project = given_project_with_file(db, storage, admins=["admin1", "admin2"])

    res: HTMLResponse = html_client.get(
        f"http://localhost/projects/{project.name}/admins/admin3/delete"
    )

    assert res.status_code == 200, res.text
    assert list(map(attrgetter("text"), res.html.find(".admin"))) == ["admin1", "admin2"]


def test_admin_remove_restricted(html_client, app, db, storage):
    _login(html_client, "user1")
    project = given_project_with_file(db, storage, admins=["admin1", "admin2"])

    res: HTMLResponse = html_client.get(
        f"http://localhost/projects/{project.name}/admins/admin2/delete"
    )

    assert res.status_code == 401


def test_admin_remove_last(html_client, app, db, storage):
    _login(html_client, "admin1")
    project = given_project_with_file(db, storage, admins=["admin1"])

    res: HTMLResponse = html_client.get(
        f"http://localhost/projects/{project.name}/admins/admin1/delete"
    )

    assert res.status_code == 200, res.text
    assert list(map(attrgetter("text"), res.html.find(".admin"))) == ["admin1"]
    assert list(map(attrgetter("text"), res.html.find(".flashing-message"))) == [
        "A project requires at least one admin."
    ]


def test_member_add_new_restricted(html_client, app, db, storage):
    _login(html_client, "user1")
    project = given_project_with_file(db, storage, admins=["admin1"], members=["user2"])

    res: HTMLResponse = html_client.post(
        f"http://localhost/projects/{project.name}/members", data={"username": "user3"}
    )

    assert res.status_code == 401


def test_member_add_new(html_client, app, db, storage):
    _login(html_client, "admin1")
    project = given_project_with_file(db, storage, admins=["admin1"], members=["user2"])

    res: HTMLResponse = html_client.post(
        f"http://localhost/projects/{project.name}/members", data={"username": "user3"}
    )

    assert res.status_code == 200, res.text
    assert list(map(attrgetter("text"), res.html.find(".member"))) == ["user2", "user3"]


def test_member_add_duplicate(html_client, app, db, storage):
    _login(html_client, "admin1")
    project = given_project_with_file(db, storage, admins=["admin1"], members=["user2"])

    res: HTMLResponse = html_client.post(
        f"http://localhost/projects/{project.name}/members", data={"username": "user2"}
    )

    assert res.status_code == 200, res.text
    assert list(map(attrgetter("text"), res.html.find(".member"))) == ["user2"]


def test_member_add_empty(html_client, app, db, storage):
    _login(html_client, "admin1")
    project = given_project_with_file(db, storage, admins=["admin1"], members=["user2"])

    res: HTMLResponse = html_client.post(
        f"http://localhost/projects/{project.name}/members", data={"username": ""}
    )

    assert res.status_code == 200, res.text
    assert list(map(attrgetter("text"), res.html.find(".member"))) == ["user2"]


def test_member_add_missing_field(html_client, app, db, storage):
    _login(html_client, "admin1")
    project = given_project_with_file(db, storage, admins=["admin1"], members=["user2"])

    res: HTMLResponse = html_client.post(
        f"http://localhost/projects/{project.name}/members", data={}
    )

    assert res.status_code == 200, res.text
    assert list(map(attrgetter("text"), res.html.find(".member"))) == ["user2"]


def test_member_remove_restricted(html_client, app, db, storage):
    _login(html_client, "user1")
    project = given_project_with_file(
        db, storage, admins=["admin1"], members=["user2", "user3"]
    )

    res: HTMLResponse = html_client.get(
        f"http://localhost/projects/{project.name}/members/user3/delete"
    )

    assert res.status_code == 401


def test_member_remove(html_client, app, db, storage):
    _login(html_client, "admin1")
    project = given_project_with_file(
        db, storage, admins=["admin1"], members=["user2", "user3"]
    )

    res: HTMLResponse = html_client.get(
        f"http://localhost/projects/{project.name}/members/user3/delete"
    )

    assert res.status_code == 200, res.text
    assert list(map(attrgetter("text"), res.html.find(".member"))) == ["user2"]


def test_member_remove_last(html_client, app, db, storage):
    _login(html_client, "admin1")
    project = given_project_with_file(db, storage, admins=["admin1"], members=["user2"])

    res: HTMLResponse = html_client.get(
        f"http://localhost/projects/{project.name}/members/user2/delete"
    )

    assert res.status_code == 200, res.text
    assert list(map(attrgetter("text"), res.html.find(".member"))) == []


def test_member_remove_not_existing(html_client, app, db, storage):
    _login(html_client, "admin1")
    project = given_project_with_file(db, storage, admins=["admin1"], members=["user2"])

    res: HTMLResponse = html_client.get(
        f"http://localhost/projects/{project.name}/members/user3/delete"
    )

    assert res.status_code == 200, res.text
    assert list(map(attrgetter("text"), res.html.find(".member"))) == ["user2"]
