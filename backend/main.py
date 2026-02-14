from fastapi import FastAPI, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import os

# Google auth
from google.oauth2 import id_token
from google.auth.transport import requests as grequests

# Scraping
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# CORS (TEMP: allow all)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== CONFIG =====
GOOGLE_CLIENT_ID = "996613039990-0trnr1a3dh4l5aevo57hci9v4mnc1ock.apps.googleusercontent.com"

# ===== DATABASE =====
conn = sqlite3.connect("app.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS favorites (
    email TEXT,
    url TEXT,
    title TEXT,
    price TEXT,
    image TEXT
)
""")
conn.commit()

# ===== MODELS =====
class LoginRequest(BaseModel):
    id_token: str

class FavoriteRequest(BaseModel):
    url: str

# ===== HELPERS =====
def verify_token(token: str):
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            grequests.Request(),
            GOOGLE_CLIENT_ID
        )
        return idinfo.get("email")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

def scrape_flipkart(url: str):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=10)

    if r.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch product page")

    soup = BeautifulSoup(r.text, "html.parser")

    # Title
    title_tag = soup.find("span", {"class": "B_NuCI"})
    title = title_tag.text.strip() if title_tag else "Unknown Product"

    # Price
    price_tag = soup.find("div", {"class": "_30jeq3 _16Jk6d"})
    price = price_tag.text.strip() if price_tag else "N/A"

    # Image
    img_tag = soup.find("img", {"class": "_396cs4"})
    image = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

    return {"title": title, "price": price, "image": image}

# ===== ROUTES =====

@app.post("/login")
def login(data: LoginRequest):
    email = verify_token(data.id_token)
    return {"email": email}

@app.post("/favorite")
def add_favorite(
    token: str = Query(...),
    data: FavoriteRequest = Body(...)
):
    email = verify_token(token)

    scraped = scrape_flipkart(data.url)

    cur.execute(
        "INSERT INTO favorites (email, url, title, price, image) VALUES (?, ?, ?, ?, ?)",
        (email, data.url, scraped["title"], scraped["price"], scraped["image"])
    )
    conn.commit()

    return {"status": "ok"}

@app.get("/favorites")
def get_favorites(token: str = Query(...)):
    email = verify_token(token)

    cur.execute(
        "SELECT url, title, price, image FROM favorites WHERE email = ?",
        (email,)
    )
    rows = cur.fetchall()

    return [
        {"url": r[0], "title": r[1], "price": r[2], "image": r[3]}
        for r in rows
    ]

@app.delete("/favorite")
def delete_favorite(token: str = Query(...), url: str = Query(...)):
    email = verify_token(token)

    cur.execute(
        "DELETE FROM favorites WHERE email = ? AND url = ?",
        (email, url)
    )
    conn.commit()

    return {"status": "deleted"}
