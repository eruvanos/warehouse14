import requests_html
from pytest import fixture
from requests_html import HTMLResponse
from wsgiadapter import WSGIAdapter

from tests import captured_templates
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


def test_project_form_returns_form_template(html_client, app, db, storage):
    login(html_client, "user1")

    with captured_templates(app) as records:
        res: HTMLResponse = html_client.get(f"http://localhost/projects_form")

    assert res.status_code == 200, res.text

    template, context = records[0]
    assert template.name == "project/create_project.html"


def test_project_form_creates_project(html_client, app, db, storage):
    login(html_client, "user1")
    res = html_client.get(f"http://localhost/projects_form")
    csrf_token = res.html.find("#csrf_token", first=True).attrs["value"]

    with captured_templates(app) as records:
        res: HTMLResponse = html_client.post(
            f"http://localhost/projects_form",
            data={"name": "test-project", "public": True, "csrf_token": csrf_token},
        )

    assert res.status_code == 200, res.text

    project = db.project_get("test-project")
    assert project is not None
    assert project.public == True
    assert project.members == []
    assert project.admins == ["user1"]


def test_project_edit_returns_form_template(html_client, app, db, storage):
    login(html_client, "user1")
    project = given_project_with_file(db, storage, admins=["user1"])

    with captured_templates(app) as records:
        res: HTMLResponse = html_client.get(
            f"http://localhost/projects/{project.name}/edit"
        )

    assert res.status_code == 200, res.text

    template, context = records[0]
    assert template.name == "project/project_edit.html"


def test_project_edit_updates_project(html_client, app, db, storage):
    login(html_client, "user1")
    project = given_project_with_file(db, storage, admins=["user1"])

    res = html_client.get(f"http://localhost/projects/{project.name}/edit")
    csrf_token = res.html.find("#csrf_token", first=True).attrs["value"]

    with captured_templates(app) as records:
        res: HTMLResponse = html_client.post(
            f"http://localhost/projects/{project.name}/edit",
            data={"public": True, "csrf_token": csrf_token},
        )

    assert res.status_code == 200, res.text

    actual_project = db.project_get(project.name)
    assert actual_project is not None
    assert actual_project.public == True
    assert actual_project.members == []
    assert actual_project.admins == ["user1"]
