#! python
import json
import sys
import zlib
from pprint import pprint

from itsdangerous import base64_decode


def decode(cookie):
    """Decode a Flask cookie."""
    try:
        compressed = False
        payload = cookie
        if payload.startswith("."):
            compressed = True
            payload = payload[1:]
        data = payload.split(".")[0]
        data = base64_decode(data)
        if compressed:
            data = zlib.decompress(data)

        return json.loads(data.decode("utf-8"))
    except Exception as e:
        return (
            "[Decoding error: are you sure this was a Flask session cookie? {}]".format(
                e
            )
        )


if __name__ == "__main__":
    cookie = sys.argv[1]
    pprint(decode(cookie), indent=2)
