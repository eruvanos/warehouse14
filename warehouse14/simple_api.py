"""
Implementation of PEP 503
"""
import logging
import mimetypes
import os
from pathlib import Path
from urllib.parse import urljoin

from flask import Blueprint, request, render_template, redirect, send_file, abort, g
from flask_httpauth import HTTPBasicAuth
from pypitoken import Token, ValidationError, LoaderError
from werkzeug.datastructures import MultiDict

from warehouse14.models import Project, File
from warehouse14.pkg_helpers import normalize_pkgname_for_url
from warehouse14.repos import DBBackend
from warehouse14.storage import PackageStorage

SINGLE_USE_METADATA = {
    "summary",
    "home_page",
    "author",
    "author_email",
    "maintainer",
    "maintainer_email",
    "license",
    "description",
    "keywords",
    "comment",
    "description_content_type",
}

MULTIPLE_USE_METADATA = {
    "project_urls",
    "classifiers",
}

ACCEPTED_METADATA = SINGLE_USE_METADATA | MULTIPLE_USE_METADATA


def extract_metadata(form: MultiDict):
    metadata = {}
    for key, value in form.items():
        if key in ACCEPTED_METADATA:
            if key in MULTIPLE_USE_METADATA:
                metadata[key] = form.getlist(key)
            elif key == "keywords":
                metadata[key] = value.split(",")
            else:
                metadata[key] = value
    return metadata


def create_blueprint(
    db: DBBackend, storage: PackageStorage, allow_project_creation: bool = False
):
    app = Blueprint("simple", __name__)
    token_auth = HTTPBasicAuth()
    log = logging.getLogger(__name__)

    @token_auth.verify_password
    def verify_password(username, password):
        """
        Verifies the given api token.

        :param username: name of the account
        :param password: api token with prefix
        :return: username
        """
        try:
            if username and username != "__token__":
                log.warning(f"Access without proper token {username}")
                return None

            token = Token.load(password)
            account = db.resolve_token(token.identifier)

            for tk in db.account_token_list(account.name):
                if tk.id == token.identifier:
                    # delay test to check for specific project access
                    token.check(key=tk.key, project="")

                    # Store token for later
                    g.token = token
                    return account.name
        except (LoaderError, ValidationError):
            log.warning(f"Access with invalid token permitted.")

        # Not authenticated
        return None

    @app.get("/simple/")
    @token_auth.login_required
    def simple_index():
        usern_name = token_auth.current_user()
        links = sorted(
            (p.name, p.normalized_name())
            for p in db.project_list()
            if p.visible(usern_name)
        )
        return render_template("simple/simple.html", links=links)

    @app.route("/simple/<project_name>/")
    @token_auth.login_required
    def simple_packages(project_name):
        # PEP 503: require normalized project
        normalized = normalize_pkgname_for_url(project_name)
        if project_name != normalized:
            log.info(f"Redirect to normalized project name url")
            return redirect(f"/simple/{normalized}/", 301)

        project = db.project_get(project_name)
        if project is None:
            abort(404)

        user_name = token_auth.current_user()
        if not project.visible(user_name):
            abort(401)

        links = (
            (
                os.path.basename(file.filename),
                urljoin(
                    request.path,
                    f"../../packages/{normalized}/{file.filename}#sha256={file.sha256_digest}",
                ),
            )
            for file in project.files
        )
        return render_template("simple/links.html", project=project_name, links=links)

        # packages = sorted(
        #     db.get_project(project),
        #     key=lambda x: (x.parsed_version, x.relfn),
        # )

        # current_uri = request.path
        #
        # links = (
        #     (
        #         os.path.basename(pkg.relfn),
        #         urljoin(current_uri, f"../../packages/{pkg.fname_and_hash}"),
        #     )
        #     for pkg in packages
        # )
        #
        # return render_template("simple/links.html", project=project, links=links)

    @app.route("/packages/<project_name>/<path:filename>")
    @token_auth.login_required
    def server_static(project_name: str, filename: str):
        # PEP 503: require normalized project
        normalized = normalize_pkgname_for_url(project_name)
        if project_name != normalized:
            log.info(f"Redirect to normalized project name url")
            return redirect(f"/simple/{normalized}/{filename}", 301)

        # Check access
        usern_name = token_auth.current_user()
        project = db.project_get(normalized)
        if not project.visible(usern_name):
            abort(401)

        # serve file
        log.info(f"Provide file {filename}")
        file = storage.get(project_name, filename)
        response = send_file(
            file,
            download_name=Path(filename).name,
            mimetype="application/octet-stream",
        )
        return response
        # if config.cache_control:
        #     response.set_header(
        #         "Cache-Control", f"public, max-age={config.cache_control}"
        #     )
        # raise NotFound(f"Not Found ({filename} does not exist)")

    @app.post("/simple/")
    @token_auth.login_required
    def upload():
        form = request.form

        # Get user
        username = token_auth.current_user()
        log.info(f"Upload request from {username}")

        # Validate request, check for required information
        if form[":action"] != "file_upload":
            log.warning(
                f"Wrong action '{form[':action:']}', only supporting 'file_upload'"
            )
            abort(
                403, f"Wrong action '{form[':action:']}', only supporting 'file_upload'"
            )
        if form["protocol_version"] != "1":
            log.warning(f"Wrong protocol_version '{form['protocol_version']}'.")
            abort(403, f"Wrong protocol_version '{form['protocol_version']}'.")
        if "content" not in request.files:
            log.warning(f"No upload content.")
            abort(403, f"No upload content.")

        REQUIRED_METADATA = {"name", "version", "filetype", "summary", "sha256_digest"}
        if not REQUIRED_METADATA.issubset(set(form.keys())):
            log.warning(f"Missing required information.")
            abort(403, f"Missing required information.")

        project_name = form["name"]
        version = form["version"]
        file = request.files["content"]
        sha256_digest = form["sha256_digest"]

        # get or create project
        project = db.project_get(project_name)
        if project is None:
            if not allow_project_creation:
                log.warning(f"No permission to create a new project via direct upload.")
                abort(401, f"No permission to create a new project via direct upload.")
            else:
                project = db.project_save(
                    Project(
                        name=project_name, admins=[username], members=[], public=False
                    )
                )

        # Check permissions, only admins are allowed to upload
        if username not in project.admins:
            log.warning(
                f"No permission to upload packages. {username} -> {project.normalized_name()}"
            )
            abort(401, f"No permission to upload packages")

        try:
            # Store file
            file_key = file.filename
            project.add_file(
                version, File(filename=file_key, sha256_digest=sha256_digest)
            )
            storage.add(project.normalized_name(), file_key, file.stream)
        except FileExistsError:
            log.warning("File already exists, overwriting not allowed")
            abort(409, "File already exists, overwriting not allowed")

        # Update metadata
        new_metadata = extract_metadata(form)
        project.versions[version].metadata.update(new_metadata)

        # Update project
        db.project_save(project)
        log.info(f"Uploaded new file for {project.normalized_name()}: {file_key}")

        return {"upload": "successfully"}

    return app
