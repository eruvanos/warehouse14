import secrets

import flask_login
import pytest
import requests_html
from flask import Response, redirect
from pytest import fixture
from requests_html import HTMLResponse
from wsgiadapter import WSGIAdapter

from warehouse14 import create_app, DBBackend, Authenticator, Project
from warehouse14.repos_dynamo import DynamoDBBackend
from warehouse14.storage import S3Storage
from tests.test_simple_api import given_project_with_file


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


def test_show_start_page_with_text(html_client, app):
    _login(html_client, "user1")

    res: HTMLResponse = html_client.get("http://localhost")

    assert "Welcome to our internal Python Package Index" in res.html.text


def test_projects_list_projects(html_client, app, db):
    _login(html_client, "user1")

    db.project_save(Project(name="public1", public=True))
    db.project_save(Project(name="admin1", admins=["user1"]))
    db.project_save(Project(name="member1", members=["user1"]))

    res: HTMLResponse = html_client.get("http://localhost/projects")

    assert res.status_code == 200, res.text
    assert res.html.find("#projects", first=True).links == {
        "/projects/admin1",
        "/projects/member1",
        "/projects/public1",
    }


def test_project_page_shows_details(html_client, app, db, storage):
    _login(html_client, "user1")
    project = given_project_with_file(db, storage, admins=["user1"])

    res: HTMLResponse = html_client.get(f"http://localhost/projects/{project.name}")

    assert res.status_code == 200, res.text
    assert (
        f"pip install -i http://localhost/simple/ {project.name}" in res.html.find(".nav-content", first=True).text
    )
