import json
from datetime import datetime, timedelta
from itertools import count
from typing import Any, Literal, List, Optional
from uuid import uuid4

import jwt

from litestar import Request, get, post, delete
from litestar.connection import ASGIConnection
from litestar.exceptions import HTTPException, NotAuthorizedException
from litestar.stores.memory import MemoryStore
from models import User, UserCreatePayload, UserLoginPayload, Note
from auth import authenticate_user

note_id_counter = count(start=1)
MOCK_DB: dict[str, User] = {}
memory_store = MemoryStore()
user_list: List[User] = []


async def retrieve_user_handler(session: dict[str, Any], connection: "ASGIConnection[Any, Any, Any, Any]") -> Optional[
    User]:
    return MOCK_DB.get(session.get("user_id"))


@post("/login")
async def login(data: UserLoginPayload, request: "Request[Any, Any, Any]") -> dict:
    user_id = await memory_store.get(data.email)

    if not user_id:
        raise NotAuthorizedException
    user_id = user_id.decode("utf-8")

    access_token_payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }

    access_token = jwt.encode(access_token_payload, "your_secret_key", algorithm="HS256")
    request.set_session({"access_token": access_token, "user_id": user_id})

    return {"access_token": access_token}


@post("/signup")
async def signup(data: UserCreatePayload, request: Request[Any, Any, Any]) -> User:
    user_email_list = [u.email for u in user_list]

    if data.email not in user_email_list:
        user = User(name=data.name, email=data.email, id=uuid4())

        await memory_store.set(data.email, str(user.id))
        MOCK_DB[str(user.id)] = user
        request.set_session({"user_id": str(user.id)})
        user_list.append(user)

        return user
    raise HTTPException(status_code=409, detail="This email is already registered")


@get("/user", sync_to_thread=False)
def get_user(request: Request[User, dict[Literal["user_id"], str], Any]) -> List[User]:
    return user_list


@post("/note")
async def add_note(data: Note, request: Request[Any, Any, Any]) -> Note:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise NotAuthorizedException("Missing or invalid authorization header")

    token = auth_header.split()[1]
    user_id = await authenticate_user(token)
    note_id = next(note_id_counter)
    note = Note(id=note_id, title=data.title, text=data.text, user_id=request.user.id)
    request.user.notes.append(note)
    await memory_store.set(str(note.id), note.json())

    if note.user_id != request.user.id:
        raise HTTPException(status_code=403, detail="You are not the owner of this note")

    return note


@post("/note/{note_id:int}")
async def update_note(note_id: int, data: Note, request: Request[User, dict[Literal["user_id"], str], Any]) -> Note:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise NotAuthorizedException("Missing or invalid authorization header")

    token = auth_header.split()[1]
    user_id = await authenticate_user(token)
    try:
        note_uuid = note_id
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid id")

    for note in request.user.notes:
        if note.id == note_uuid:
            note.title = data.title
            note.text = data.text

            await memory_store.set(str(note.id), note.json())

            return note

    raise HTTPException(status_code=404, detail="Note not found")


@delete("/note/{note_id:int}")
async def delete_note(
        note_id: int,
        request: Request[User, dict[Literal["user_id"], str], Any]
) -> None:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise NotAuthorizedException("Missing or invalid authorization header")

    token = auth_header.split()[1]
    user_id = await authenticate_user(token)

    try:
        note_uuid = note_id
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    for note in request.user.notes:
        if note.id == note_uuid:
            request.user.notes.remove(note)
            await memory_store.delete(str(note.id))
            return
    raise HTTPException(status_code=404, detail="Note not found")


@get("/note/{note_id:int}")
async def get_note(note_id: int, request: Request[User, dict[Literal["user_id"], str], Any]) -> Note:
    try:
        note_uuid = note_id
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid id")

    note = await memory_store.get(str(note_uuid))
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return Note(**json.loads(note.decode("utf-8")))
