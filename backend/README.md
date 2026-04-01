# KTU Result Analyzer — FastAPI Backend

## Stack
| Layer | Technology |
|-------|-----------|
| Framework | [FastAPI](https://fastapi.tiangolo.com/) |
| ASGI server | [Uvicorn](https://www.uvicorn.org/) |
| Database | [MongoDB](https://www.mongodb.com/) via [Motor](https://motor.readthedocs.io/) (async) |
| Auth | Google OAuth 2.0 + WebAuthn Passkeys ([py-webauthn](https://github.com/duo-labs/py_webauthn)) |
| JWT | [python-jose](https://github.com/mpdavis/python-jose) |

---

## Quick Start

### 1. Create and activate a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
```bash
cp .env.example .env
# Edit .env with your Google credentials, MongoDB URI, and JWT secret
```

### 4. Run the development server
```bash
uvicorn main:app --reload --port 8000
```

Interactive API docs are available at **http://localhost:8000/docs**

---

## Project Structure

```
backend/
├── main.py               # FastAPI app factory + lifespan (DB connect/disconnect)
├── requirements.txt
├── .env.example          # Template — copy to .env and fill in secrets
└── app/
    ├── config.py         # Pydantic-settings — all configuration in one place
    ├── database.py       # Motor async MongoDB client (connect / close / get_database)
    ├── models/
    │   └── user.py       # User document model + PasskeyCredential schema
    ├── routes/
    │   ├── auth.py       # Google OAuth 2.0 + Passkey registration & authentication
    │   └── users.py      # Protected user profile + passkey management endpoints
    └── utils/
        ├── jwt.py        # create_access_token, create_refresh_token, get_current_user_id
        └── passkey.py    # WebAuthn helpers (generate options, verify responses)
```

---

## API Endpoints

### Auth (`/auth`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/auth/google/login` | Returns the Google OAuth authorization URL |
| GET | `/auth/google/callback?code=` | Exchanges code for tokens, upserts user, issues JWT |
| POST | `/auth/refresh` | Issues new access token via refresh-token cookie |
| POST | `/auth/logout` | Revokes refresh token |
| POST | `/auth/passkey/register/begin` | 🔒 Starts passkey registration |
| POST | `/auth/passkey/register/complete` | 🔒 Completes passkey registration |
| POST | `/auth/passkey/authenticate/begin` | Starts passkey authentication |
| POST | `/auth/passkey/authenticate/complete` | Completes passkey authentication, issues JWT |

### Users (`/users`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/users/me` | 🔒 Current user profile |
| GET | `/users/me/passkeys` | 🔒 List registered passkeys |
| DELETE | `/users/me/passkeys/{credential_id}` | 🔒 Remove a passkey |

🔒 = requires `Authorization: Bearer <access_token>` header

---

## MongoDB Collections

| Collection | Purpose |
|-----------|---------|
| `users` | User profiles (email, name, picture, google_id, passkeys[]) |
| `sessions` | Active refresh tokens (for revocation) |
| `webauthn_challenges` | Temporary WebAuthn challenges (TTL index recommended) |

### Recommended Indexes
```js
// users
db.users.createIndex({ "email": 1 }, { unique: true })
db.users.createIndex({ "google_id": 1 }, { sparse: true })
db.users.createIndex({ "passkeys.credential_id": 1 })

// sessions
db.sessions.createIndex({ "user_id": 1 })
db.sessions.createIndex({ "refresh_token": 1 })

// webauthn_challenges — auto-expire after 5 minutes
db.webauthn_challenges.createIndex({ "created_at": 1 }, { expireAfterSeconds: 300 })
```

---

## Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials
2. Create **OAuth 2.0 Client ID** (Web application)
3. Add **Authorized redirect URIs**:
   - Development: `http://localhost:3000/auth/callback`
   - Production: `https://yourdomain.com/auth/callback`
4. Copy `Client ID` → `GOOGLE_CLIENT_ID` in `.env`
5. Copy `Client Secret` → `GOOGLE_CLIENT_SECRET` in `.env`
