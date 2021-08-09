from socket import socket

from tests.local_dynamodb import LocalDynamoDB
from tests.local_login import MockAuthenticator

socket._GLOBAL_DEFAULT_TIMEOUT = 2

import logging
from pathlib import Path

from warehouse14 import create_app, SimpleFileStorage
from warehouse14.repos_dynamo import DynamoDBBackend, create_table

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    Path("tmp/db").mkdir(parents=True, exist_ok=True)
    local_dynamo = LocalDynamoDB(shared=True, in_memory=False, db_dir="tmp/db")

    with local_dynamo as dynamodb:
        table = create_table(dynamodb, "table")
        db = DynamoDBBackend(table)
        storage = SimpleFileStorage("tmp", allow_overwrite=False)

        auth = MockAuthenticator()  # redirects to form page, local login
        app = create_app(
            db,
            storage,
            auth,
            session_secret="Secret!",
            simple_api_allow_project_creation=False,
            restrict_project_creation=None,
        )
        app.debug = True
        app.templates_auto_reload = True

        print("Start here -> http://localhost:5000")
        app.run()
