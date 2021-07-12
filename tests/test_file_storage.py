from io import BytesIO

from warehouse14.storage import SimpleFileStorage


def test_round_trip(tmpdir):
    fs = SimpleFileStorage(tmpdir)

    # Add
    fs.add("example_project", "test.txt", BytesIO(b"Hello World!"))
    assert (tmpdir / "packages" / "example_project" / "test.txt").exists()

    # Retrieve file
    data = fs.get("example_project", "test.txt")
    assert data.read() == b"Hello World!"

    # Delete file

    fs.delete("example_project", "test.txt")
    assert not (tmpdir / "example_project" / "test.txt").exists()
