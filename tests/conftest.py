from uuid import uuid4

import boto3
import pytest
from moto import mock_dynamodb2, mock_s3

from warehouse14.repos_dynamo import create_table


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
    with mock_dynamodb2():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        yield create_table(dynamodb, str(uuid4()))
