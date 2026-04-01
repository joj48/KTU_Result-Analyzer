from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field
from bson import ObjectId


# ──────────────────────────────────────────────
# Helper for MongoDB ObjectId serialization
# ──────────────────────────────────────────────

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> str:
        if not ObjectId.is_valid(v):
            raise ValueError(f"Invalid ObjectId: {v}")
        return str(v)


# ──────────────────────────────────────────────
# Passkey credential stored per-device
# ──────────────────────────────────────────────

class PasskeyCredential(BaseModel):
    credential_id: str
    public_key: str
    sign_count: int = 0
    device_name: str = "Unknown device"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ──────────────────────────────────────────────
# User document (stored in MongoDB)
# ──────────────────────────────────────────────

class UserInDB(BaseModel):
    id: PyObjectId | None = Field(default=None, alias="_id")
    email: str
    name: str
    picture: str = ""
    google_id: str | None = None
    passkeys: list[PasskeyCredential] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}


# ──────────────────────────────────────────────
# Public user response (excludes sensitive fields)
# ──────────────────────────────────────────────

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    picture: str
    created_at: datetime
    last_login: datetime
    passkeys_count: int = 0
