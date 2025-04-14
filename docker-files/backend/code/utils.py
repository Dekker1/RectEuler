import logging
import os
import secrets
import string
from typing import Optional


def randomString(n: int = 12) -> str:
    # secure random string
    secure_str = ''.join((secrets.choice(string.ascii_letters) for i in range(n)))
    return secure_str


def generateID(IDLength=12, tokenLength=20):
    return randomString(IDLength), randomString(tokenLength)


def get_docker_variables(name: Optional[str] = None, secrets_dir: Optional[str] = None) -> str:
    value: Optional[str] = None
    if name is None and secrets_dir is None:
        raise RuntimeError(f"Both name and dir are None")

    if name is not None:
        value = os.environ.get(name)

    if secrets_dir is not None and value is None:
        path = os.environ.get(secrets_dir)
        try:
            with open(os.path.join(path), 'r') as secret_file:
                value = secret_file.read().rstrip('\n')
        except IOError as e:
            logging.log(logging.INFO, f"Could not read file {os.path.join(path)}")

    if value is None:
        raise RuntimeError(f"Could not get {name} from environment or {os.path.join(path)} from files.")
    return value
