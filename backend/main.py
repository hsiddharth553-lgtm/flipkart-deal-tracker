from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import os
import requests
from bs4 import BeautifulSoup

# Google token verification
from google.oauth2 import id_token
from google.auth.transport import requests as grequests

app = FastAPI()

# ========== CORS ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://hsiddharth553-lgtm.github.io"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== CONFIG ==========
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
if not GOOGLE_CLIENT_ID:
    raise RuntimeError("GOOGLE_CLIENT_ID is not set")

# ========== DATABASE ==========
conn = sqlite3.connect("app.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS favorites (
    email TEXT,
    title TEXT,
    image TEXT,
    price TEXT,
    old_price TEXT,
    url TEXT
)
""")
conn.commit()

# ========== MODELS ==========
class LoginRequest(BaseModel):
    id_token: str

class FavoriteRequest(BaseModel):
    url: str

# ========== HELPERS ==========
def fetch_flipkart_data(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    r = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    title_el = soup.select_one("span.B_NuCI")
    price_el = soup.select_one("div._30jeq3")
    old_price_el = soup.select_one("div._3I9_wc")
    image_el = soup.select_one("img._396cs4")

    title = title_el.text.strip() if title_el else "Unknown product"
    price = price_el.text.strip() if price_el else ""
    old_price = old_price_el.text.strip() if old_price_el else ""
    image = image_el["src"] if image_el else ""

    return {
        "title": title,
        "price": price,
        "old_price": old_price,
        "image": image,
        "url": url
    }

# ========== ROUTES ==========

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

        product = fetch_flipkart_data(data.url)

        cur.execute(
            "INSERT INTO favorites (email, title, image, price, old_price, url) VALUES (?, ?, ?, ?, ?, ?)",
            (email, product["title"], product["image"], product["price"], product["old_price"], product["url"])
        )
        conn.commit()

        return {"status": "ok", "product": product}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="Failed to add product")

@app.get("/favorites")
def get_favorites(token: str):
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            grequests.Request(),
            GOOGLE_CLIENT_ID
        )
        email = idinfo.get("email")

        cur.execute(
            "SELECT title, image, price, old_price, url FROM favorites WHERE email = ?",
            (email,)
        )
        rows = cur.fetchall()

        return [
            {
                "title": r[0],
                "image": r[1],
                "price": r[2],
                "old_price": r[3],
                "url": r[4],
            }
            for r in rows
        ]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.delete("/favorite")
def delete_favorite(token: str, url: str):
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            grequests.Request(),
            GOOGLE_CLIENT_ID
        )
        email = idinfo.get("email")

        cur.execute(
            "DELETE FROM favorites WHERE email = ? AND url = ?",
            (email, url)
        )
        conn.commit()

        return {"status": "deleted"}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
