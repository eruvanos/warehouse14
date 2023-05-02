from uuid import uuid4

import boto3
import pytest
from moto import mock_dynamodb, mock_s3

from tests.local_login import MockAuthenticator
from warehouse14 import DBBackend, PackageStorage
from warehouse14.repos_dynamo import DynamoDBBackend
from warehouse14.storage import S3Storage


@pytest.fixture
def bucket():
    """Pytest fixture that creates the bucket in
    the fake moto AWS account
    """
    with mock_s3():
        s3 = boto3.resource("s3", region_name="us-east-1")
        bucket = s3.Bucket(str(uuid4()))
        bucket.create()
        yield bucket


@pytest.fixture
def table():
    """Pytest fixture that creates the table in
    the fake moto AWS account
    """
    with mock_dynamodb():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        yield dynamodb.create_table(
            TableName=str(uuid4()),
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            BillingMode="PAY_PER_REQUEST",
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "sk_gsi",
                    "KeySchema": [
                        {"AttributeName": "sk", "KeyType": "HASH"},
                        {"AttributeName": "pk", "KeyType": "RANGE"},
                    ],
                    "Projection": {
                        "ProjectionType": "ALL",
                    },
                }
            ],
        )


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
async def page():
    from pyppeteer import launch

    browser = await launch({"headless": True})
    yield (await browser.pages())[0]

    await browser.close()
