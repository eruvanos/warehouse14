import os
import shutil
import tarfile
from uuid import uuid4

import boto3
import requests
from mirakuru import TCPExecutor
from mirakuru.exceptions import ProcessFinishedWithError

LATEST_URL = "https://s3.eu-central-1.amazonaws.com/dynamodb-local-frankfurt/dynamodb_local_latest.tar.gz"


class LocalDynamoDB:
    def __init__(
        self, download_path="/tmp/dynamodb", shared=False, in_memory=True, db_dir="./"
    ):
        self._path = download_path
        self._path_dynamodb_jar = os.path.join(download_path, "DynamoDBLocal.jar")
        self._port = self._get_open_port()

        extra_options = "-inMemory" if in_memory else f"-dbPath {db_dir}"
        extra_options += " -sharedDb" if shared else ""
        self.executor = TCPExecutor(
            f"java -Djava.library.path=./DynamoDBLocal_lib -jar {self._path_dynamodb_jar} -port {self._port} {extra_options}",
            host="localhost",
            port=self._port,
            timeout=60,
        )

        # Write random credentials into env
        self.aws_access_key = str(uuid4())
        self.aws_secret_access_key = str(uuid4())
        self.region = str(uuid4())

        os.environ["AWS_ACCESS_KEY_ID"] = self.aws_access_key
        os.environ["AWS_SECRET_ACCESS_KEY"] = self.aws_secret_access_key
        os.environ["AWS_DEFAULT_REGION"] = self.region

        self.__resources = set()

    def start(self):
        self._ensure_dynamodb_local()
        self.executor.start()
        return self

    def __enter__(self):
        self.start()
        return self.resource()

    def clear(self):
        for t in self.resource().tables.all():
            t.delete()

    def stop(self):
        # for resource in self.__resources:
        #     resource.
        try:
            self.executor.stop()
        except ProcessFinishedWithError:
            # Java exits with some strange code, ignore it, we wanted to stop it anyway
            pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def resource(self):
        dynamo_db = boto3.resource(
            "dynamodb",
            endpoint_url=self.endpoint_url(),
        )

        self.__resources.add(dynamo_db)
        return dynamo_db

    def endpoint_url(self) -> str:
        return "http://{host}:{port}".format(
            host="localhost",
            port=self._port,
        )

    def credentials(self, table="table"):
        return {
            "access_key": self.aws_access_key,
            "region": self.region,
            "secret_access_key": self.aws_secret_access_key,
            "table": table,
        }

    @staticmethod
    def _get_open_port():
        import socket

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
        s.close()
        return port

    def _ensure_dynamodb_local(self):
        if os.path.exists(self._path_dynamodb_jar):
            print(f'Use existing DynamoDB setup in "{self._path}"')

        else:
            self._download_dynamodb()

    def _download_dynamodb(self):
        print(f'Download dynamodb local to "{self._path}"')

        if os.path.exists(self._path):
            print(f'Clean "{self._path}"')
            shutil.rmtree(self._path)

        with requests.get(LATEST_URL, stream=True) as r:
            r.raise_for_status()

            with tarfile.open(fileobj=r.raw, mode="r:gz") as tar:
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(tar, self._path)

        for p in os.listdir(self._path):
            print(p)
