from io import BytesIO

from warehouse14.storage import S3Storage


def test_round_trip(bucket):
    fs = S3Storage(bucket)

    # Add
    fs.add("example_project", "test.txt", BytesIO(b"Hello World!"))

    # List files
    assert list(fs.list()) == ["example_project/test.txt"]

    # Retrieve file
    data = fs.get("example_project", "test.txt")
    assert data.read() == b"Hello World!"

    # Delete file
    fs.delete("example_project", "test.txt")
    assert list(fs.list()) == []
