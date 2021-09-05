"""
Copied from https://github.com/pypiserver/pypiserver
Under MIT license

Removed unused code lines
"""

import re
from urllib.parse import quote


def normalize_pkgname(name: str) -> str:
    """Perform PEP 503 normalization"""
    return re.sub(r"[-_.]+", "-", name).lower()


def normalize_pkgname_for_url(name: str) -> str:
    """Perform PEP 503 normalization and ensure the value is safe for URLs."""
    return quote(normalize_pkgname(name))
