"""
User routes — protected endpoints for reading and managing the current user.

Endpoints
---------
GET  /users/me            → return current user profile
GET  /users/me/passkeys   → list registered passkeys (id + device name + date)
DELETE /users/me/passkeys/{credential_id} → remove a passkey
"""

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.database import get_database
from app.models.user import UserResponse
from app.utils.jwt import get_current_user_id

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user(user_id: str = Depends(get_current_user_id)):
    """Return the profile of the authenticated user."""
    db = get_database()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        name=user.get("name", ""),
        picture=user.get("picture", ""),
        created_at=user["created_at"],
        last_login=user["last_login"],
        passkeys_count=len(user.get("passkeys", [])),
    )


@router.get("/me/passkeys")
async def list_passkeys(user_id: str = Depends(get_current_user_id)):
    """Return a summary of the user's registered passkeys (no public keys exposed)."""
    db = get_database()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return [
        {
            "credential_id": p["credential_id"],
            "device_name": p.get("device_name", "Unknown device"),
            "created_at": p.get("created_at"),
        }
        for p in user.get("passkeys", [])
    ]


@router.delete("/me/passkeys/{credential_id}", status_code=204)
async def remove_passkey(
    credential_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Remove a passkey from the user's account."""
    db = get_database()
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$pull": {"passkeys": {"credential_id": credential_id}}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
