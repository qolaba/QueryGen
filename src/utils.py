import os
from fastapi.security import HTTPAuthorizationCredentials


def check_token(api_key: HTTPAuthorizationCredentials) -> None:
    if api_key.credentials != os.environ["API_KEY"]:
        raise Exception("Invalid API key")
