import requests_html
from pytest import fixture
from requests_html import HTMLResponse
from wsgiadapter import WSGIAdapter

from tests.endpoints import login
from tests.test_simple_api import given_project_with_file
from warehouse14 import create_app, Project


@fixture
def app(db, storage, authenticator):
    app = create_app(db, storage, authenticator)
    app.debug = True
    return app


@fixture
def html_client(app) -> requests_html.HTMLSession:
    session = requests_html.HTMLSession()
    session.mount("http://localhost", WSGIAdapter(app))
    return session


def test_show_start_page_with_text(html_client, app):
    login(html_client, "user1")

    res: HTMLResponse = html_client.get("http://localhost")

    assert "Welcome to our internal Python Package Index" in res.html.text


def test_projects_list_projects(html_client, app, db):
    login(html_client, "user1")

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
    login(html_client, "user1")
    project = given_project_with_file(db, storage, admins=["user1"])

    res: HTMLResponse = html_client.get(f"http://localhost/projects/{project.name}")

    assert res.status_code == 200, res.text
    assert (
        f"pip install --extra-index-url http://localhost/simple/ {project.name}"
        in res.html.find(".nav-content", first=True).text
    )
