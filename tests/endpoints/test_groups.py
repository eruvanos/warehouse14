import requests_html
from pytest import fixture
from requests_html import HTMLResponse
from wsgiadapter import WSGIAdapter

from tests.endpoints import login
from warehouse14 import create_app


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


def test_groups_list_empty(html_client, app):
    login(html_client, "user1")

    res: HTMLResponse = html_client.get("http://localhost/groups")

    assert res.status_code == 200

    groups = list(map(lambda e: e.text, res.html.find(".group-name")))
    assert groups == []


def test_groups_list(html_client, app, db):
    login(html_client, "user1")

    db.group_create("group1", admins=["user1"])

    res: HTMLResponse = html_client.get("http://localhost/groups")

    assert res.status_code == 200

    tokens = list(map(lambda e: e.text, res.html.find(".group-name")))
    assert tokens == ["group1"]
