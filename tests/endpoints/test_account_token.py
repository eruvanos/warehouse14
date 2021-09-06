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


def test_tokens_list_empty(html_client, app):
    login(html_client, "user1")

    res: HTMLResponse = html_client.get("http://localhost/manage/account")

    assert res.status_code == 200

    tokens = list(map(lambda e: e.text, res.html.find(".account-token-name")))
    assert tokens == []


def test_tokens_list(html_client, app, db):
    login(html_client, "user1")

    db.account_token_add("user1", "token-1", "token-1-name", "key")

    res: HTMLResponse = html_client.get("http://localhost/manage/account")

    assert res.status_code == 200

    tokens = list(map(lambda e: e.text, res.html.find(".account-token-name")))
    assert tokens == ["token-1-name"]


def test_tokens_add(html_client, app, db):
    login(html_client, "user1")

    res: HTMLResponse = html_client.post(
        "http://localhost/manage/account/tokens_form", data={"name": "token-2"}
    )

    assert res.status_code == 200

    tokens = db.account_token_list("user1")
    assert len(tokens) == 1
    assert tokens[0].name == "token-2"


def test_tokens_remove(html_client, app, db):
    login(html_client, "user1")

    db.account_token_add("user1", "token-1", "token-1-name", "key")

    res: HTMLResponse = html_client.get(
        "http://localhost/manage/account/tokens/delete", params={"token_id": "token-1"}
    )

    assert res.status_code == 200
    assert res.url == "http://localhost/manage/account"

    tokens = list(map(lambda e: e.text, res.html.find(".account-token-name")))
    assert tokens == []

    tokens = db.account_token_list("user1")
    assert len(tokens) == 0
