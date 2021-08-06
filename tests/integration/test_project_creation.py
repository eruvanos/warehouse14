import pytest
from pyppeteer import launch

from tests.integration import login, get_texts
from tests.integration.server import FlaskTestServer
from warehouse14 import create_app


@pytest.fixture
def server(tmpdir, db, storage, authenticator):
    app = create_app(
        db,
        storage,
        authenticator,
        restrict_project_creation=None,
        simple_api_allow_project_creation=False
    )
    app.debug = False
    app.secret_key = "Secret"

    server = FlaskTestServer(app, port=5001)
    server.start()
    yield server
    server.shutdown_server()


@pytest.mark.asyncio
async def test_title(server, authenticator, page):
    await login(page, server.url, "user1")

    await page.goto(server.url)

    title = await page.title()
    assert title == "Warehouse14"


@pytest.mark.asyncio
async def test_manage_project(server, authenticator, page):
    # Open product page
    await login(page, server.url, "user1")

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

    # Open project edit page
    await page.click("#edit-project-btn")
    await page.click("#edit-project-users-tab")

    # Add Member
    await page.type("input[name=username]", "example-user")
    await page.click("button[type='submit']")
    members = await get_texts(page, ".member")
    assert "example-user" in members

    # Remove Member
    await page.click("#project-member-example-user-remove")
    members = await get_texts(page, ".member")
    assert "example-user" not in members
