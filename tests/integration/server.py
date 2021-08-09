import os
import sys
from threading import Thread

import requests
from flask import request, Flask


class FlaskTestServer(Thread):
    def __init__(self, app: Flask, port=5000):
        super().__init__(daemon=True)
        self.port = port
        self.app = app

        # Disable banners
        cli = sys.modules["flask.cli"]
        cli.show_server_banner = lambda *x: None
        self.app.env = "development"

        self.url = "http://localhost:%s" % self.port
        self.app.add_url_rule("/shutdown", view_func=self._shutdown_server)

    @staticmethod
    def get_open_port():
        import socket

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
        s.close()
        return port

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
        self.app.run(host="127.0.0.1", port=self.port)
