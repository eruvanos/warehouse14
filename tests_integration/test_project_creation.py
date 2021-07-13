import flask_login
import pytest
from flask import Response, redirect
from pyppeteer import launch

from warehouse14 import create_app, Authenticator, DBBackend, PackageStorage
from warehouse14.repos_dynamo import DynamoDBBackend
from warehouse14.storage import S3Storage
from tests_integration.server import FlaskTestServer


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


@pytest.fixture
def authenticator():
    return MockAuthenticator()


@pytest.fixture
def db(table) -> DBBackend:
    return DynamoDBBackend(table)


@pytest.fixture
def storage(bucket) -> PackageStorage:
    return S3Storage(bucket)


@pytest.fixture
def server(tmpdir, db, storage, authenticator):
    # TODO bring back file backends?

    app = create_app(db, storage, authenticator)
    app.debug = False
    app.secret_key = "Secret"

    server = FlaskTestServer(app, port=5001)
    server.start()
    yield server
    server.shutdown_server()


async def _login(page, server_url, user_id):
    await page.goto(f"{server_url}/_auto_login/{user_id}")
    assert f"Logged in as {user_id}" in await page.plainText()


@pytest.mark.asyncio
async def test_title(server, authenticator):
    browser = await launch({"headless": True})
    page = await browser.newPage()

    await _login(page, server.url, "user1")

    await page.goto(server.url)

    title = await page.title()
    assert title == "Warehouse14"
    await browser.close()


@pytest.mark.asyncio
async def test_create_project(server, authenticator):
    browser = await launch({"headless": True})

    # Open product page
    page = await browser.newPage()
    await _login(page, server.url, "user1")

    await page.goto(server.url + "/projects")

    # Create project
    await page.click("#create-project-btn")

    # Enter name
    await page.type("#name", "ExampleProject")

    # Submit
    await page.click("button[type='submit']")

    # Assert we are on product page, edit button is available, no content
    assert "projects/exampleproject" in page.url
    assert await page.querySelector("#edit-project-btn")
    assert "You can upload new versions to" in await page.plainText()

    await browser.close()
