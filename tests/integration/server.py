import os
from threading import Thread

import requests
from flask import request, Flask


class FlaskTestServer(Thread):
    def __init__(self, app: Flask, port=5000):
        super().__init__(daemon=True)
        self.port = port
        self.app = app

        # Disable banners
        os.environ["WERKZEUG_RUN_MAIN"] = "true"
        self.app.env = "development"

        self.url = "http://localhost:%s" % self.port
        self.app.add_url_rule("/shutdown", view_func=self._shutdown_server)

    @staticmethod
    def _shutdown_server():
        if "werkzeug.server.shutdown" not in request.environ:
            raise RuntimeError("Not running the development server")
        request.environ["werkzeug.server.shutdown"]()
        return "Server shutting down..."

    def shutdown_server(self):
        requests.get("http://localhost:%s/shutdown" % self.port)
        self.join(30)

    def run(self):
        self.app.run(port=self.port)
