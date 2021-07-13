import datetime
import secrets
from collections import defaultdict
from operator import attrgetter
from uuid import uuid4

import pypitoken
import readme_renderer.markdown
import readme_renderer.rst
import readme_renderer.txt
from flask import Flask, render_template, redirect, url_for, abort, request, g, flash
from flask_login import LoginManager, login_required, current_user, logout_user
from flaskext.markdown import Markdown

from warehouse14 import simple_api
from warehouse14.forms import CreateProjectForm, CreateAPITokenForm
from warehouse14.login import OIDCAuthenticator, Authenticator, User
from warehouse14.models import Project, Account, Token
from warehouse14.pkg_helpers import guess_pkgname_and_version
from warehouse14.repos import DBBackend
from warehouse14.storage import SimpleFileStorage, PackageStorage

_RENDERERS = {
    None: readme_renderer.rst,  # Default if description_content_type is None
    "": readme_renderer.rst,  # Default if description_content_type is None
    "text/plain": readme_renderer.txt,
    "text/x-rst": readme_renderer.rst,
    "text/markdown": readme_renderer.markdown,
}


def create_app(
    db: DBBackend,
    storage: PackageStorage,
    auth: Authenticator,
    config: dict = None,
    allow_project_creation=False,
):
    app = Flask(__name__)
    if config:
        app.config.update(**config)
    Markdown(app, extensions=["footnotes", "fenced_code"])

    log = app.logger

    # Setup Login and authentication
    login_manager = LoginManager(app)

    @login_manager.user_loader
    def load_user(user_id):
        """Automatically creates a user for any OIDC login"""
        account = db.account_get(user_id)
        if account is None:
            account = db.account_save(user_id)
        return User(account) if account else None

    auth.init_app(app)

    simple_blueprint = simple_api.create_blueprint(
        db, storage, allow_project_creation=allow_project_creation
    )
    app.register_blueprint(simple_blueprint)

    def get_user_id():
        return current_user.account.name

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return auth.logout()

    @app.template_filter("sn")
    def filter_suppress_none(val):
        if val is not None:
            return val
        else:
            return ""

    @app.get("/")
    @login_required
    def index():
        return render_template("home.html")

    @app.get("/manage/account")
    @login_required
    def account():
        token_list = [
            (token.id, token.name) for token in db.account_token_list(get_user_id())
        ]
        return render_template("account/account.html", tokens=token_list)

    @app.route("/manage/account/token", methods=["GET", "POST"])
    @login_required
    def account_token():
        form = CreateAPITokenForm()
        if form.is_submitted():
            # create new token
            token_name = form.name.data
            token = Token(
                id=str(uuid4()),
                name=token_name,
                key=secrets.token_hex(16),
                created=datetime.datetime.utcnow(),
            )

            pypi_token = pypitoken.Token.create(
                domain="warehouse14",
                identifier=token.id,
                key=token.key,
                prefix="wh14",
            )

            # save token
            db.account_token_add(
                user_id=get_user_id(), token_id=token.id, name=token.name, key=token.key
            )

            # render with token view
            return render_template(
                "account/token.html",
                create_form=CreateAPITokenForm(formdata=None),
                new_token=token,
                token_raw=pypi_token.dump(),
            )

        return render_template("account/token.html", create_form=form)

    @app.get("/manage/account/token/delete")
    @login_required
    def account_token_delete():
        token_id = request.args.get("token_id")
        db.account_token_delete(get_user_id(), token_id)
        return redirect(url_for("account"))

    @app.get("/projects")
    @login_required
    def list_projects():
        own_projects = [
            project for project in db.project_list() if project.visible(get_user_id())
        ]
        own_projects.sort(key=attrgetter("name"))

        return render_template("project/projects.html", projects=own_projects)

    @app.get("/projects/<project_name>")
    @login_required
    def show_project(project_name):
        project = db.project_get(project_name)
        if project is None:
            abort(404)

        # In case no version is available, nothing has to be prepared
        latest_version = project.latest_version
        if latest_version is None:
            return render_template("project/project.html", project=project)

        metadata = latest_version.metadata
        # Render description depending on the type (plain, rst, markdown)
        renderer = _RENDERERS[latest_version.description_content_type]
        readme = renderer.render(latest_version.description)

        grouped_classifiers = defaultdict(list)
        for classifier in latest_version.classifiers:
            group, value = classifier.split(" :: ", 1)
            grouped_classifiers[group].append(value)

        # Parse URLS
        urls = []
        if url := metadata.get("url"):
            urls.append(("Homepage", url))
        for project_url in metadata.get("project_urls", []):

            if "=" in project_url:
                name, url = project_url.split("=", 1)
            elif "," in project_url:
                name, url = project_url.split(",", 1)
            else:
                name, url = ("URL", project_url)
            urls.append((name.strip(), url.strip()))

        return render_template(
            "project/project.html",
            project=project,
            readme=readme,
            grouped_classifiers=grouped_classifiers,
            urls=urls,
        )

    @app.route("/create_project", methods=["GET", "POST"])
    @login_required
    def create_project():
        form = CreateProjectForm()
        if form.validate_on_submit():
            project = db.project_save(
                Project(
                    name=form.name.data,
                    admins=[get_user_id()],
                    members=[],
                    public=form.public.data,
                )
            )

            return redirect(
                url_for("show_project", project_name=project.normalized_name())
            )
        else:
            return render_template("project/create_project.html", form=form)

    @app.route("/projects/<project_name>/edit", methods=["GET", "POST"])
    @login_required
    def edit_project(project_name):
        project = db.project_get(project_name)
        if not project:
            abort(404, f"No Project found with name {project_name}")

        form = CreateProjectForm(name=project.name, public=project.public)
        form.name.render_kw = {"disabled": "disabled"}

        if form.validate_on_submit():
            # Update fields
            project.public = form.public.data

            return redirect(url_for("show_project", project_name=form.name.data))
        else:
            return render_template(
                "project/project_edit.html", project=project, form=form
            )

    @app.get("/projects/<project_name>/users")
    @login_required
    def project_users(project_name):
        project = db.project_get(project_name)
        if not project:
            abort(404, f"No Project found with name {project_name}")

        return render_template("project/project_users.html", project=project)

    @app.post("/projects/<project_name>/admins")
    @login_required
    def project_add_admin(project_name):
        project = db.project_get(project_name)
        if not project.is_admin(get_user_id()):
            abort(401, 'You are not an admin, what are you doing here?')

        new_user = request.form.get("username")
        if new_user:
            log.info(f"{project_name} {get_user_id()} added {new_user} as admin")
            project.admins.append(new_user)
            db.project_save(project)

        return redirect(url_for("project_users", project_name=project_name))

    @app.get("/projects/<project_name>/admins/<username>/delete")
    @login_required
    def project_remove_admin(project_name, username):
        project = db.project_get(project_name)
        if not project.is_admin(get_user_id()):
            abort(401, 'You are not an admin, what are you doing here?')

        if username in project.admins:
            # Never delete the last admin!
            if len(project.admins) > 1:
                project.admins.remove(username)
                db.project_save(project)
            else:
                flash("A project requires at least one admin.")

        return redirect(url_for("project_users", project_name=project_name))

    @app.post("/projects/<project_name>/members")
    @login_required
    def project_add_member(project_name):
        project = db.project_get(project_name)
        if not project.is_admin(get_user_id()):
            abort(401, 'You are not an admin, what are you doing here?')

        new_user = request.form.get("username")
        if new_user:
            log.info(f"{project_name} {get_user_id()} added {new_user} as member")
            project.members.append(request.form["username"])
            db.project_save(project)
        return redirect(url_for("project_users", project_name=project_name))

    @app.get("/projects/<project_name>/members/<username>/delete")
    @login_required
    def project_remove_member(project_name, username):
        project = db.project_get(project_name)
        if not project.is_admin(get_user_id()):
            abort(401, 'You are not an admin, what are you doing here?')

        if username in project.members:
            project.members.remove(username)
            db.project_save(project)

        return redirect(url_for("project_users", project_name=project_name))

    return app
