from abc import ABCMeta, abstractmethod
from typing import Dict
from urllib.parse import urlencode

import flask_login
from authlib.integrations.base_client.base_oauth import OAUTH_CLIENT_PARAMS
from authlib.integrations.flask_client import OAuth, FlaskRemoteApp
from flask import Flask, url_for, session, redirect, request, Response
from flask_login import UserMixin
from werkzeug.urls import url_parse

from warehouse14.models import Account


class User(UserMixin):
    def __init__(self, account: Account):
        self.account = account

    def get_id(self):
        return self.account.name

    def __str__(self):
        return self.account.name


class Authenticator(metaclass=ABCMeta):
    @abstractmethod
    def init_app(self, app):
        """
        init flask application, add required callbacks and more
        """
        pass

    @abstractmethod
    def logout(self) -> Response:
        """
        Provide logout response
        """
        pass


class OIDCAuthenticator(Authenticator):
    app: Flask

    def __init__(self, app=None, **kwargs):
        """
        kwargs are passed to the underlying authlib client if they are listed in OAUTH_CLIENT_PARAMS.
        """
        self.oauth = None
        self.oidc_config = {k: v for k, v in kwargs.items() if k in OAUTH_CLIENT_PARAMS}

        if app:
            self.init_app(app)

    def init_app(self, app: Flask):
        self.app = app

        self.oauth = OAuth(app)
        self.oauth.register(
            name="oidc",
            client_kwargs={"scope": "openid email profile"},
            **self.oidc_config,
        )

        app.route("/oauth")(self._auth)
        if hasattr(app, "login_manager"):
            # maybe move outside
            app.login_manager.unauthorized_handler(self._redirect_to_auth_server)
        else:
            raise ValueError(
                "The app requires to be initialized with Flask-Login before"
            )

    def logout(self) -> Response:
        url = url_parse(request.url)
        logout_url = url_parse(
            self.oauth.oidc.load_server_metadata().get("end_session_endpoint")
        )
        logout_url = logout_url._replace(
            query=urlencode({"redirect_uri": f"{url.scheme}://{url.netloc}"})
        )
        return redirect(logout_url.to_url())

    def _redirect_to_auth_server(self):
        # Store origin url to redirect after login
        session["next"] = request.url

        redirect_uri = url_for("_auth", _external=True)
        oidc: FlaskRemoteApp = self.oauth.oidc
        return oidc.authorize_redirect(redirect_uri)

    def _auth(self):
        oidc_client = self.oauth.oidc
        token = oidc_client.authorize_access_token()
        user: Dict = oidc_client.parse_id_token(token)

        user_id_field = self.app.config.get("OIDC_USER_ID_FIELD", "email")
        self._login_user_with_id(user.get(user_id_field))

        next_url = session.pop("next", "/")
        return redirect(next_url)

    # noinspection PyProtectedMember,PyUnresolvedReferences
    def _login_user_with_id(self, user_id):
        # Instead of passing the Database into the Authenticator, we reuse the setup Flask-Login to load the user
        # While this relies on implementation details, it eases the app setup process
        login_manager: flask_login.LoginManager = self.app.login_manager
        user = login_manager._user_callback(user_id)
        flask_login.login_user(user)
