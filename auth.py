from datetime import datetime, timedelta

import jwt

from litestar.exceptions import NotAuthorizedException
from models import UserLoginPayload


async def create_access_token(user_id: str) -> str:
    access_token_payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(access_token_payload, "your_secret_key", algorithm="HS256")


async def authenticate_user(token: str) -> str:
    try:
        payload = jwt.decode(token, "your_secret_key", algorithms=["HS256"])
        user_id = payload.get("user_id")
        if user_id:
            return user_id
        else:
            raise NotAuthorizedException
    except jwt.ExpiredSignatureError:
        raise NotAuthorizedException("Token has expired")
    except jwt.InvalidTokenError:
        raise NotAuthorizedException("Invalid token")

