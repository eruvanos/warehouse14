import pytest

from tests.integration import login, get_texts, click
from tests.integration.server import FlaskTestServer
from warehouse14 import create_app


@pytest.fixture
def server(tmpdir, db, storage, authenticator):
    app = create_app(
        db,
        storage,
        authenticator,
        restrict_project_creation=None,
        simple_api_allow_project_creation=False,
    )
    app.debug = False

    server = FlaskTestServer(app, port=FlaskTestServer.get_open_port())
    server.start()
    server.wait()
    yield server
    server.shutdown_server()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_title(server, authenticator, page):
    await login(page, server.url, "user1")

    await page.goto(server.url)

    title = await page.title()
    assert title == "Warehouse14"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_manage_project(server, authenticator, page):
    # Open product page
    await login(page, server.url, "user1")

    await page.goto(server.url + "/projects")

    # Create project
    await click(page, "#create-project-btn")

    # Enter name
    await page.type("#name", "ExampleProject")

    # Submit
    await click(page, "button[type='submit']")

    # Assert we are on product page, edit button is available, no content
    assert "projects/exampleproject" in page.url
    assert await page.querySelector("#edit-project-btn")
    assert "You can upload new versions to" in await page.plainText()

    # Open project edit page
    await click(page, "#edit-project-btn")
    await click(page, "#edit-project-users-tab")

    # Add Member
    await page.type("input[name=username]", "example-user")
    await click(page, "button[type='submit']")

    members = await get_texts(page, ".member")
    assert "example-user" in members, page.url

    # Remove Member
    await click(page, "#project-member-example-user-remove")
    members = await get_texts(page, ".member")
    assert "example-user" not in members
