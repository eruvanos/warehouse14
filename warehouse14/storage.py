import hashlib
from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path
from typing import Iterable, BinaryIO, Union


class PackageStorage(ABC):
    @abstractmethod
    def add(self, project: str, file: str, data: BinaryIO):
        """
        :param project: normalized name of the project
        :param file: file file of the blob to store
        :param data: blob to store
        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def get(self, project: str, file: str) -> BinaryIO:
        raise NotImplementedError()

    @abstractmethod
    def delete(self, project: str, file: str):
        raise NotImplementedError()

    def digest(self, project: str, file: str, hash_algo: str) -> str:
        """
        Reads and digests for a file according to specified hashing-algorithm.
        :param file: file of file in storage
        :param hash_algo: any algo contained in :mod:`hashlib`
        :return: <hash_algo>=<hex_digest>

        From https://stackoverflow.com/a/21565932/548792
        """
        data = self.get(project, file)

        digester = hashlib.new(hash_algo)
        blocksize = 2 ** 16
        for block in iter(lambda: data.read(blocksize), b""):
            digester.update(block)
        return f"{hash_algo}={digester.hexdigest()}"


class SimpleFileStorage(PackageStorage):
    def __init__(self, root: Union[str, Path], allow_overwrite=False):
        self._root = (Path(root) / "packages").expanduser().resolve()
        self._allow_overwrite = allow_overwrite

    def add(self, project: str, file: str, data: BinaryIO):
        key = self._root / project / file

        if key.exists() and not self._allow_overwrite:
            raise FileExistsError(str(key))

        key.parent.mkdir(parents=True, exist_ok=True)
        key.write_bytes(data.read())

    def get(self, project: str, file: str) -> BinaryIO:
        key = self._root / project / file
        return BytesIO(key.read_bytes())

    def delete(self, project: str, file: str):
        key = self._root / project / file
        if key.exists():
            key.unlink()


class S3Storage(PackageStorage):
    def __init__(self, bucket, allow_overwrite=False):
        self._bucket = bucket
        self._allow_overwrite = allow_overwrite

    def add(self, project: str, file: str, data: BinaryIO):
        key = f"{project}/{file}"

        if self._contains(key) and not self._allow_overwrite:
            raise FileExistsError(str(key))

        self._bucket.put_object(Key=key, Body=data.read())

    def list(self) -> Iterable[str]:
        for obj in self._bucket.objects.all():
            yield obj.key

    def get(self, project: str, file: str) -> BinaryIO:
        key = f"{project}/{file}"
        if self._contains(key):
            return self._bucket.Object(key).get()["Body"]
        else:
            raise KeyError()

    def delete(self, project: str, file: str):
        key = f"{project}/{file}"
        if self._contains(key):
            self._bucket.Object(key).delete()

    def _contains(self, key: str):
        objs = list(self._bucket.objects.filter(Prefix=key))
        return len(objs) > 0 and objs[0].key == key
