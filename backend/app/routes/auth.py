"""
Authentication routes — Google OAuth 2.0 and WebAuthn passkeys.

Endpoints
---------
GET  /auth/google/login              → redirect URL for Google OAuth consent screen
GET  /auth/google/callback           → exchange code, upsert user, issue tokens
POST /auth/refresh                   → issue new access token from refresh token cookie
POST /auth/logout                    → revoke refresh token
POST /auth/passkey/register/begin    → (authenticated) start passkey registration
POST /auth/passkey/register/complete → (authenticated) finish passkey registration
POST /auth/passkey/authenticate/begin    → start passkey authentication
POST /auth/passkey/authenticate/complete → finish passkey authentication, issue tokens
"""

from datetime import datetime, timezone
import json
import urllib.parse

import httpx
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from webauthn.helpers.json import WebAuthnJsonEncoder

from app.config import get_settings
from app.database import get_database
from app.utils.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user_id,
)
from app.utils.passkey import (
    build_authentication_options,
    build_registration_options,
    decode_base64url,
    encode_bytes,
    verify_authentication,
    verify_registration,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
_REFRESH_COOKIE = "refresh_token"


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _set_refresh_cookie(response: Response, token: str) -> None:
    cfg = get_settings()
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=cfg.cookie_secure,
        samesite="lax",
        max_age=60 * 60 * 24 * cfg.refresh_token_expire_days,
        path="/auth/refresh",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_REFRESH_COOKIE, path="/auth/refresh")


# ──────────────────────────────────────────────
# Google OAuth
# ──────────────────────────────────────────────

@router.get("/google/login")
async def google_login():
    """Return the Google OAuth authorization URL."""
    cfg = get_settings()
    params = {
        "client_id": cfg.google_client_id,
        "redirect_uri": cfg.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    }
    auth_url = f"{_GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"
    return {"url": auth_url}


@router.get("/google/callback")
async def google_callback(code: str, response: Response):
    """Exchange OAuth code → Google tokens → user info → JWT tokens."""
    cfg = get_settings()
    db = get_database()

    # 1. Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            _GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": cfg.google_client_id,
                "client_secret": cfg.google_client_secret,
                "redirect_uri": cfg.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
    token_resp.raise_for_status()
    google_tokens = token_resp.json()

    # 2. Fetch user profile
    async with httpx.AsyncClient() as client:
        info_resp = await client.get(
            _GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {google_tokens['access_token']}"},
        )
    info_resp.raise_for_status()
    info = info_resp.json()

    # 3. Upsert user in MongoDB
    now = datetime.now(timezone.utc)
    result = await db.users.find_one_and_update(
        {"google_id": info["sub"]},
        {
            "$set": {
                "email": info["email"],
                "name": info.get("name", ""),
                "picture": info.get("picture", ""),
                "last_login": now,
            },
            "$setOnInsert": {
                "google_id": info["sub"],
                "passkeys": [],
                "created_at": now,
            },
        },
        upsert=True,
        return_document=True,
    )
    user_id = str(result["_id"])

    # 4. Issue tokens
    access_token = create_access_token({"sub": user_id, "email": info["email"]})
    refresh_token = create_refresh_token({"sub": user_id})

    # Store refresh token hash in DB (for revocation)
    await db.sessions.insert_one(
        {"user_id": user_id, "refresh_token": refresh_token, "created_at": now}
    )

    _set_refresh_cookie(response, refresh_token)
    return {"access_token": access_token, "token_type": "bearer"}


# ──────────────────────────────────────────────
# Token refresh / logout
# ──────────────────────────────────────────────

@router.post("/refresh")
async def refresh_token(request: Request, response: Response):
    """Issue a new access token using the refresh token cookie."""
    db = get_database()
    token = request.cookies.get(_REFRESH_COOKIE)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    session = await db.sessions.find_one({"refresh_token": token})
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session not found or revoked")

    user_id: str = payload["sub"]
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    new_access = create_access_token({"sub": user_id, "email": user["email"]})
    return {"access_token": new_access, "token_type": "bearer"}


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Revoke the refresh token."""
    db = get_database()
    token = request.cookies.get(_REFRESH_COOKIE)
    if token:
        await db.sessions.delete_one({"refresh_token": token})
    _clear_refresh_cookie(response)
    return {"detail": "Logged out"}


# ──────────────────────────────────────────────
# Passkey — registration
# ──────────────────────────────────────────────

@router.post("/passkey/register/begin")
async def passkey_register_begin(
    user_id: str = Depends(get_current_user_id),
):
    """Generate and return WebAuthn registration options for the authenticated user."""
    db = get_database()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    options = build_registration_options(
        user_id=user_id,
        user_name=user["email"],
        user_display_name=user.get("name", user["email"]),
    )

    # Persist challenge temporarily
    await db.webauthn_challenges.replace_one(
        {"user_id": user_id, "type": "registration"},
        {
            "user_id": user_id,
            "type": "registration",
            "challenge": encode_bytes(options.challenge),
        },
        upsert=True,
    )

    return json.loads(json.dumps(options, cls=WebAuthnJsonEncoder))


@router.post("/passkey/register/complete")
async def passkey_register_complete(
    credential: dict,
    device_name: str = "Unknown device",
    user_id: str = Depends(get_current_user_id),
):
    """Verify registration response and store the new passkey on the user."""
    db = get_database()
    stored = await db.webauthn_challenges.find_one({"user_id": user_id, "type": "registration"})
    if not stored:
        raise HTTPException(status_code=400, detail="No pending registration challenge")

    expected_challenge = decode_base64url(stored["challenge"])
    verification = verify_registration(credential, expected_challenge)

    # Store credential on user document
    passkey = {
        "credential_id": encode_bytes(verification.credential_id),
        "public_key": encode_bytes(verification.credential_public_key),
        "sign_count": verification.sign_count,
        "device_name": device_name,
        "created_at": datetime.now(timezone.utc),
    }
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$push": {"passkeys": passkey}},
    )
    await db.webauthn_challenges.delete_one({"user_id": user_id, "type": "registration"})
    return {"detail": "Passkey registered successfully"}


# ──────────────────────────────────────────────
# Passkey — authentication
# ──────────────────────────────────────────────

@router.post("/passkey/authenticate/begin")
async def passkey_auth_begin():
    """Generate WebAuthn authentication options (discoverable credentials)."""
    db = get_database()
    options = build_authentication_options()

    await db.webauthn_challenges.replace_one(
        {"type": "authentication", "user_id": None},
        {
            "user_id": None,
            "type": "authentication",
            "challenge": encode_bytes(options.challenge),
        },
        upsert=True,
    )

    return json.loads(json.dumps(options, cls=WebAuthnJsonEncoder))


@router.post("/passkey/authenticate/complete")
async def passkey_auth_complete(credential: dict, response: Response):
    """Verify authentication response and issue JWT tokens."""
    db = get_database()
    stored = await db.webauthn_challenges.find_one({"type": "authentication", "user_id": None})
    if not stored:
        raise HTTPException(status_code=400, detail="No pending authentication challenge")

    expected_challenge = decode_base64url(stored["challenge"])
    raw_id = credential.get("rawId") or credential.get("id")

    # Look up user by credential id
    user = await db.users.find_one({"passkeys.credential_id": raw_id})
    if not user:
        raise HTTPException(status_code=401, detail="Credential not found")

    passkey = next(p for p in user["passkeys"] if p["credential_id"] == raw_id)
    verification = verify_authentication(
        authentication_response=credential,
        expected_challenge=expected_challenge,
        credential_public_key=decode_base64url(passkey["public_key"]),
        credential_current_sign_count=passkey["sign_count"],
    )

    # Update sign count
    await db.users.update_one(
        {"_id": user["_id"], "passkeys.credential_id": raw_id},
        {
            "$set": {
                "passkeys.$.sign_count": verification.new_sign_count,
                "last_login": datetime.now(timezone.utc),
            }
        },
    )
    await db.webauthn_challenges.delete_one({"type": "authentication", "user_id": None})

    user_id = str(user["_id"])
    access_token = create_access_token({"sub": user_id, "email": user["email"]})
    refresh_token = create_refresh_token({"sub": user_id})

    await db.sessions.insert_one(
        {"user_id": user_id, "refresh_token": refresh_token, "created_at": datetime.now(timezone.utc)}
    )

    _set_refresh_cookie(response, refresh_token)
    return {"access_token": access_token, "token_type": "bearer"}
