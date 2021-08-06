from requests import Session


def login(session: Session, username):
    session.post(f"http://localhost/_local_login", data={"username": username})
