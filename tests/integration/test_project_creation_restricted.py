import pytest

from tests.integration import login
from tests.integration.server import FlaskTestServer
from warehouse14 import create_app


@pytest.fixture
def server(tmpdir, db, storage, authenticator):
    app = create_app(
        db,
        storage,
        authenticator,
        restrict_project_creation=["admin"],
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
async def test_manage_project(server, authenticator, page):
    # Open product page
    await login(page, server.url, "user1")

    await page.goto(server.url + "/projects")

    # Create project button not shown
    assert len(await page.querySelectorAll("#create-project-btn")) == 0
