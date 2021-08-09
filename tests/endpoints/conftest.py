from _pytest.fixtures import fixture

from tests.local_login import MockAuthenticator
from warehouse14 import DBBackend
from warehouse14.repos_dynamo import DynamoDBBackend
from warehouse14.storage import S3Storage


@fixture
def authenticator():
    return MockAuthenticator()


@fixture
def db(table) -> DBBackend:
    return DynamoDBBackend(table)


@fixture
def storage(bucket):
    return S3Storage(bucket)
