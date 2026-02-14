from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3

# Google token verification
from google.oauth2 import id_token
from google.auth.transport import requests as grequests

app = FastAPI()

# CORS (allow frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8001", "http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== CONFIG =====
import os

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
if not GOOGLE_CLIENT_ID:
    raise RuntimeError("GOOGLE_CLIENT_ID is not set")

# ===== DATABASE =====
conn = sqlite3.connect("app.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    name TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT,
    product TEXT
)
""")

conn.commit()

# ===== MODELS =====
class LoginRequest(BaseModel):
    id_token: str

class FavoriteRequest(BaseModel):
    product: str

# ===== GOOGLE TOKEN VERIFY =====
def verify_google_token(token: str):
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            grequests.Request(),
            GOOGLE_CLIENT_ID
        )
        return idinfo
    except Exception as e:
        print("Google token verify error:", e)
        raise HTTPException(status_code=401, detail="Invalid Google token")

# ===== ROUTES =====

@app.post("/login")
def login(req: LoginRequest):
    info = verify_google_token(req.id_token)

    email = info["email"]
    name = info.get("name", "")

    cur.execute("INSERT OR IGNORE INTO users (email, name) VALUES (?, ?)", (email, name))
    conn.commit()

    return {"email": email, "name": name}

@app.post("/favorite")
def add_favorite(req: FavoriteRequest, token: str):
    info = verify_google_token(token)
    email = info["email"]

    cur.execute("INSERT INTO favorites (user_email, product) VALUES (?, ?)", (email, req.product))
    conn.commit()

    return {"status": "ok"}

@app.get("/favorites")
def get_favorites(token: str):
    info = verify_google_token(token)
    email = info["email"]

    cur.execute("SELECT product FROM favorites WHERE user_email = ?", (email,))
    rows = cur.fetchall()

    products = [r[0] for r in rows]
    return products
