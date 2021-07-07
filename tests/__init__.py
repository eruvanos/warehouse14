from contextlib import contextmanager
from pathlib import Path

from flask import template_rendered

import warehouse14

PROJECT_BASE_PATH = Path(warehouse14.__file__).parent.parent


@contextmanager
def captured_templates(app):
    recorded = []

    def record(sender, template, context, **extra):
        recorded.append((template, context))

    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)
