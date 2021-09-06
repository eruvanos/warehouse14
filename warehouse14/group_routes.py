from flask import Flask, render_template
from flask_login import login_required, current_user

from warehouse14.repos import DBBackend


def get_user_id():
    return current_user.account.name


def add_routes(app: Flask, db: DBBackend):
    @app.route("/groups")
    @login_required
    def groups_list():
        user_id = get_user_id()

        groups = db.account_groups_list(user_id)
        return render_template("group/groups.html", groups=groups)
