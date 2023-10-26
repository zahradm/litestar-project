from typing import List
from uuid import UUID

from pydantic import BaseModel, EmailStr, SecretStr


class Note(BaseModel):
    id: int
    title: str
    text: str
    user_id: UUID


class User(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    notes: List[Note] = []


class UserCreatePayload(BaseModel):
    name: str
    email: EmailStr
    password: SecretStr


class UserLoginPayload(BaseModel):
    email: EmailStr
    password: SecretStr
