from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3

from google.oauth2 import id_token
from google.auth.transport import requests as grequests

import requests
from bs4 import BeautifulSoup

app = FastAPI()

# ================== CONFIG ==================
GOOGLE_CLIENT_ID = "996613039990-0trnr1a3dh4l5aevo57hci9v4mnc1ock.apps.googleusercontent.com"
SCRAPER_API_KEY = "a4daee406faf33361f2ac17e8e9268b8"  # ⚠️ Regenerate later for security

# ================== CORS ==================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================== DATABASE ==================
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

# ================== MODELS ==================
class LoginRequest(BaseModel):
    id_token: str

class FavoriteRequest(BaseModel):
    url: str

# ================== HELPERS ==================
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
    api_url = "http://api.scraperapi.com/"

    params = {
        "api_key": SCRAPER_API_KEY,
        "url": url,
        "country_code": "in",
        "render": "true"
    }

    try:
        r = requests.get(api_url, params=params, timeout=30)
    except Exception:
        return {"title": "Unknown Product", "price": "N/A", "image": ""}

    if r.status_code != 200:
        return {"title": "Unknown Product", "price": "N/A", "image": ""}

    soup = BeautifulSoup(r.text, "html.parser")

    # ✅ Title from OpenGraph (most reliable)
    title = None
    og_title = soup.select_one('meta[property="og:title"]')
    if og_title and og_title.get("content"):
        title = og_title["content"].strip()

    # ✅ Image from OpenGraph
    image = ""
    og_image = soup.select_one('meta[property="og:image"]')
    if og_image and og_image.get("content"):
        image = og_image["content"].strip()

    # ✅ Price from OpenGraph or fallback selectors
    price = None
    og_price = soup.select_one('meta[property="product:price:amount"]')
    if og_price and og_price.get("content"):
        price = "₹" + og_price["content"].strip()

    if not price:
        for sel in ["div._30jeq3", "div.Nx9bqj", "span._30jeq3"]:
            p = soup.select_one(sel)
            if p and p.text.strip():
                price = p.text.strip()
                break

    return {
        "title": title or "Unknown Product",
        "price": price or "N/A",
        "image": image
    }

# ================== ROUTES ==================
@app.post("/login")
def login(data: LoginRequest):
    email = verify_token(data.id_token)
    return {"email": email}

@app.post("/favorite")
def add_favorite(token: str = Query(...), data: FavoriteRequest = None):
    email = verify_token(token)

    if not data or not data.url:
        raise HTTPException(status_code=400, detail="Missing url")

    scraped = scrape_flipkart(data.url)

    cur.execute(
        "INSERT INTO favorites (email, url, title, price, image) VALUES (?, ?, ?, ?, ?)",
        (email, data.url, scraped["title"], scraped["price"], scraped["image"])
    )
    conn.commit()

    return {"status": "ok", "product": scraped}

@app.get("/favorites")
def get_favorites(token: str):
    email = verify_token(token)

    cur.execute("SELECT url, title, price, image FROM favorites WHERE email = ?", (email,))
    rows = cur.fetchall()

    return [
        {"url": r[0], "title": r[1], "price": r[2], "image": r[3]}
        for r in rows
    ]

@app.delete("/favorite")
def delete_favorite(token: str, url: str):
    email = verify_token(token)

    cur.execute("DELETE FROM favorites WHERE email = ? AND url = ?", (email, url))
    conn.commit()

    return {"status": "deleted"}
