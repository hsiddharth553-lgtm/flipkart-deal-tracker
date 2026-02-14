from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import os

# Google token verification
from google.oauth2 import id_token
from google.auth.transport import requests as grequests

app = FastAPI()

# ===== CORS (ALLOW GITHUB PAGES + LOCAL) =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://hsiddharth553-lgtm.github.io",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== CONFIG =====
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
if not GOOGLE_CLIENT_ID:
    raise RuntimeError("GOOGLE_CLIENT_ID is not set")

# ===== DATABASE =====
conn = sqlite3.connect("app.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS favorites (
    email TEXT,
    product TEXT
)
""")
conn.commit()

# ===== MODELS =====
class LoginRequest(BaseModel):
    id_token: str

class FavoriteRequest(BaseModel):
    product: str

# ===== ROUTES =====

@app.post("/login")
def login(data: LoginRequest):
    try:
        idinfo = id_token.verify_oauth2_token(
            data.id_token,
            grequests.Request(),
            GOOGLE_CLIENT_ID
        )
        email = idinfo.get("email")
        return {"email": email}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/favorite")
def add_favorite(token: str, data: FavoriteRequest):
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            grequests.Request(),
            GOOGLE_CLIENT_ID
        )
        email = idinfo.get("email")

        cur.execute("INSERT INTO favorites (email, product) VALUES (?, ?)", (email, data.product))
        conn.commit()

        return {"status": "ok"}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/favorites")
def get_favorites(token: str):
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            grequests.Request(),
            GOOGLE_CLIENT_ID
        )
        email = idinfo.get("email")

        cur.execute("SELECT product FROM favorites WHERE email = ?", (email,))
        rows = cur.fetchall()

        return [r[0] for r in rows]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
