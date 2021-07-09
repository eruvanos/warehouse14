from pathlib import Path
from pprint import pprint

import requests

import warehouse14

PROJECT_BASE_PATH = Path(warehouse14.__file__).parent.parent

api = "https://test-pypi.vwapps.run/simple/"
user = "__token__"
token = "wh14-AgELd2FyZWhvdXNlMTQCJGE0ZjBlOTRlLTY2YTgtNDgyOC1hMTQxLWEzNjIyZGNiM2ZhZAAABiDh---rL06JZKop2Cp2ABTXwDXd8P03DXkFmHiCe-SCvw"

with (PROJECT_BASE_PATH / "fixtures/mypkg/dist/example-pkg-0.0.1.tar.gz").open(
        "rb"
) as file:
    res = requests.post(
        api,
        auth=(user, token),
        data={
            ":action": "file_upload",
            "protocol_version": "1",
            "sha256_digest": "xxx",
            "filetype": "sdist",
            "pyversion": "source",
            "metadata_version": "2.2",
            "name": "example-pkg",
            "version": "0.0.1",
            "summary": "Example package to test file upload.",
        },
        files={"content": file},
        allow_redirects=False
    )

    print(res.status_code)
    print(res.text)
    pprint(dict(res.headers), indent=2)