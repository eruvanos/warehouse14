import flask_login
from flask import request, render_template_string, redirect, session, url_for, Response, Flask

from warehouse14 import Authenticator


class MockAuthenticator(Authenticator):
    LOGIN_FORM = """
    <!DOCTYPE html>
    <html lang='en'>
    <head>
    <title>Test login</title>
    </head>
    <body>
    <form method="post">
          <div class="container">
            <label for="username"><b>Username</b></label>
            <input type="text" placeholder="Enter Username" name="username" required>
            <button type="submit">Login</button>
          </div>
        </form>
    </body>
    </html>
    """

    def init_app(self, app: Flask):
        if not hasattr(app, "login_manager"):
            raise ValueError(
                "The app requires to be initialized with Flask-Login before"
            )

        app.login_manager.unauthorized_handler(self._redirect_to_auth_server)

        @app.route("/_local_login", methods=("GET", "POST"))
        def _auto_login():
            if request.method == "GET":
                return render_template_string(MockAuthenticator.LOGIN_FORM)

            # Login user
            username = request.form["username"]
            login_manager: flask_login.LoginManager = app.login_manager
            user = login_manager._user_callback(username)
            flask_login.login_user(user)

            return redirect(session.get("next", "/"))

    def _redirect_to_auth_server(self):
        # Store origin url to redirect after login
        session["next"] = request.url
        redirect_uri = url_for("_auto_login", _external=True)
        return redirect(redirect_uri)

    def logout(self) -> Response:
        flask_login.logout_user()
        return redirect("/")
