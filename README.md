# Warehouse14

While the PyPI (Warehouse) provides a global package index for all Python users, companies and closed groups do have the
need for a non-global Python package index.

While [existing projects](#related-projects) provide different options for a private package index, Warehouse14 provides
an implementation that requires authentication by default, but provides the option for a decentralized access management
on individual project level.

## Features

* Authentication via OIDC provider by default
* User manageable API keys for download/upload
* Project
    * Project page
    * Package metadata
    * User access management
        * **Admin** is able to modify package content and upload new versions. They also manage users.
        * **Member** read access to private repositories.
    * Project Types: Public (still require authentication) / Private (Access only for defined users)

## Deployment

> TODO 🙈

### Deploy on AWS Lambda

```python
# Requirements: warehouse[aws], apig_wsgi

import boto3
from warehouse14 import OIDCAuthenticator, create_app
from warehouse14.repos_dynamo import DynamoDBBackend, create_table
from warehouse14.storage import S3Storage

# requires apig_wsgi
from apig_wsgi import make_lambda_handler

auth = OIDCAuthenticator(
    client_id="<your oidc client id>",
    client_secret="<your oidc client secret>",
    user_id_field="email",
    server_metadata_url="https://<idp>/.well-known/openid-configuration",
)

dynamodb = boto3.resource("dynamodb")
table = create_table(dynamodb, "table")
db = DynamoDBBackend(table)

bucket = boto3.resource("s3").Bucket("<bucket name>")
storage = S3Storage(bucket)

app = create_app(db, storage, auth, config={"SECRET_KEY": "{{ LONG_RANDOM_STRING }}"})
lambda_handler = make_lambda_handler(app, binary_support=True)
```

## Glossary

To use common Python terms we take over the glossary
of [Warehouse](https://warehouse.readthedocs.io/ui-principles.html#write-clearly-with-consistent-style-and-terminology)

| Term         | Definition                                                                                                                                                                                                        |
| :----------: | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: |
| Project      | A collection of releases and files, and information about them. Projects on Warehouse are made and shared by members of the Python community so others can use them.                                              |
| Release      | A specific version of a project. For example, the requests project has many releases, like requests 2.10 and requests 1.2.1. A release consists of one or more files.                                             |
| File         | Something that you can download and install. Because of different hardware, operating systems, and file formats, a release may have several files, like an archive containing source code or a binary wheel.      |
| Package      | A synonym for a file.                                                                                                                                                                                             |
| User         | A person who has registered an account on Warehouse.                                                                                                                                                              |
| Account      | An object representing a logged in user.                                                                                                                                                                          |
| Maintainer   | An user who has permissions to manage a project on Warehouse.                                                                                                                                                     |
| Owner        | An user who has permissions to manage a project on Warehouse, and has additional permission to add and remove other maintainers and owners to a project.                                                          |
| Author       | A free-form piece of information associated with a project. This information could be a name of a person, an organization, or something else altogether. This information is not linked to a user on Warehouse.   |

## Related Projects

* [warehouse](https://github.com/pypa/warehouse)
* [pypiserver](https://pypi.org/project/pypiserver/)
    * Backends:
        * Filesystem
    * upload supported
    * different auth options
* [pywharf](https://github.com/pywharf/pywharf)
    * Backends:
        * Filesystem
        * Github
    * server or github pages
    * NO UPLOAD
* [PyPICloud](https://pypicloud.readthedocs.io/en/latest/)
    * Backends:
        * Filesystem
        * S3
    * Cache via Redis, Dynamo, ...
    * Upload supported
    * Extendable
* [lapypi](https://github.com/amureki/lapypi)
    * almost fully PEP 503
    * Backends:
        * S3
    * Uses Chalice
* [plambdapi](https://github.com/berislavlopac/plambdapi)
    * Uses Terraform
    * Backends:
        * S3
    * Uses Chalice
* [pypiprivate](https://github.com/helpshift/pypiprivate)
    * static generator
    * Backends:
        * S3
* [elasticpypi](https://github.com/khornberg/elasticpypi)
    * Backends:
        * S3/ Dynamodb
    * serverless framework
    * 10MB limit
    * supports upload (strange /simple/post method)
    * uses s3 trigger to update dynamodb entries
* [devpypi](https://devpi.net/docs/devpi/devpi/stable/%2Bd/index.html)
