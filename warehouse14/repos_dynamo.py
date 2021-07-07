import json
from datetime import datetime
from typing import Optional, TYPE_CHECKING, List

from boto3.dynamodb.conditions import Key

from warehouse14 import Account, Token, Project
from warehouse14.models import Version
from warehouse14.repos import DBBackend

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.service_resource import Table, DynamoDBServiceResource


def create_table(dynamodb: "DynamoDBServiceResource", table_name):
    if table_name in [table.name for table in dynamodb.tables.all()]:
        return dynamodb.Table(table_name)

    return dynamodb.create_table(
        TableName=table_name,
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


class DynamoDBBackend(DBBackend):
    def __init__(self, table: "Table"):
        self._table = table

    # account methods
    def account_save(self, user_id: str, **kwargs) -> Optional[Account]:
        """
        Load non confidential data for a user
        """
        # check if already exists, if so, get created date
        existing_account = self.account_get(user_id=user_id)
        created = existing_account.created if existing_account else datetime.now()

        self._table.put_item(
            Item={
                "pk": f"account#{user_id}",
                "sk": f"account#{user_id}",
                "created": created.isoformat(),
                "updated": datetime.now().isoformat(),
            }
        )
        return self.account_get(user_id=user_id)

    def account_get(self, user_id: str) -> Optional[Account]:
        """
        Load non confidation data for a user
        :param user_id: ID of the user, which will be used to search for
        """

        item = self._table.get_item(
            Key={
                "pk": f"account#{user_id}",
                "sk": f"account#{user_id}",
            }
        ).get("Item")

        if item is None:
            return None
        else:
            return Account(
                name=user_id,
                created=datetime.fromisoformat(item.get("created")),
                updated=datetime.fromisoformat(item.get("updated")),
            )

    def account_token_add(
        self, user_id: str, token_id: str, name: str, key: str
    ) -> Token:
        now = datetime.now()
        self._table.put_item(
            Item={
                "pk": f"account#{user_id}",
                "sk": f"token#{token_id}",
                "name": name,
                "key": key,
                "created": now.isoformat(),
            }
        )
        return Token(
            id=token_id,
            name=name,
            key=key,
            created=now,
        )

    def account_token_list(self, account_id: str) -> List[Token]:
        query = Key("pk").eq(f"account#{account_id}") & Key("sk").begins_with("token")
        items = self._table.query(KeyConditionExpression=query).get("Items", [])

        return [
            Token(
                id=item["sk"].split("#")[1],
                name=item["name"],
                key=item["key"],
                created=datetime.fromisoformat(item["created"]),
            )
            for item in items
        ]

    def account_token_delete(self, account_id: str):
        raise NotImplementedError()

    def resolve_token(self, token_id: str) -> Optional[Account]:
        """
        Look up a account by given token id.

        :param token_id: Unique token id
        :return: Account
        """

        items = self._table.query(
            IndexName="sk_gsi", KeyConditionExpression=Key("sk").eq(f"token#{token_id}")
        ).get("Items", [])

        if len(items) > 1:
            raise Exception(
                f"Not able to resolve token, found to many ({len(items)}) accounts."
            )
        elif len(items) == 0:
            return None

        account_id = items[0]["pk"].split("#")[1]
        return self.account_get(account_id)

    # Project methods
    def project_save(self, project: Project) -> Project:
        current = self.project_get(project.name)

        # calc admins diff
        current_admins = set(current.admins) if current else set()
        project_admins = set(project.admins)
        to_create_admins = project_admins - current_admins
        to_delete_admins = current_admins - project_admins

        # calc members diff
        current_members = set(current.members) if current else set()
        project_members = set(project.members)
        to_create_members = project_members - current_members
        to_delete_members = current_members - project_members

        # write to db
        with self._table.batch_writer() as w:
            # update project entry
            w.put_item(
                Item={
                    "pk": f"project#{project.name}",
                    "sk": f"project#{project.name}",
                    "name": project.name,
                    "versions": {
                        k: json.loads(v.json()) for k, v in project.versions.items()
                    },
                }
            )

            # update public state
            if project.public:
                w.put_item(
                    Item={
                        "pk": f"project#{project.name}",
                        "sk": f"account#public",
                        "role": "member",
                    }
                )
            else:
                w.delete_item(
                    Key={
                        "pk": f"project#{project.name}",
                        "sk": f"account#public",
                    }
                )

            # write admin diff
            for admin in to_create_admins:
                w.put_item(
                    Item={
                        "pk": f"project#{project.name}",
                        "sk": f"account#{admin}",
                        "name": admin,
                        "role": "admin",
                    }
                )
            for admin in to_delete_admins:
                w.delete_item(
                    Key={
                        "pk": f"project#{project.name}",
                        "sk": f"account#{admin}",
                    }
                )

            # write member diff
            for member in to_create_members:
                w.put_item(
                    Item={
                        "pk": f"project#{project.name}",
                        "sk": f"account#{member}",
                        "name": member,
                        "role": "member",
                    }
                )
            for member in to_delete_members:
                w.delete_item(
                    Key={
                        "pk": f"project#{project.name}",
                        "sk": f"account#{member}",
                    }
                )

        return self.project_get(project.name)

    def project_get(self, name: str) -> Optional[Project]:
        items = self._table.query(
            KeyConditionExpression=Key("pk").eq(f"project#{name}")
        ).get("Items", [])

        db_project = None
        public = False
        db_admins = []
        db_members = []
        for item in items:
            if item["sk"].startswith("project#"):
                db_project = item
            if item["sk"] == "account#public":
                public = True
            elif item["sk"].startswith("account#"):
                role = item.get("role")
                if role == "admin":
                    db_admins.append(item)
                elif role == "member":
                    db_members.append(item)

        if db_project is None:
            return None

        return Project(
            name=db_project["name"],
            admins=[a["name"] for a in db_admins],
            members=[a["name"] for a in db_members],
            public=public,
            versions={k: Version(**v) for k, v in db_project["versions"].items()},
        )

    def project_list(self) -> List[Project]:
        """
        Lists all project names
        """
        # TODO this will explode,
        # we have to scan the whole DB and do additional requests per project
        items = self._table.scan(
            FilterExpression=Key("pk").begins_with(f"project#")
            & Key("sk").begins_with("project#"),
            # ProjectionExpression="name"
        ).get("Items", [])

        return [self.project_get(p["name"]) for p in items]
