from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import os
import requests
from bs4 import BeautifulSoup

# Google auth
from google.oauth2 import id_token
from google.auth.transport import requests as grequests

app = FastAPI()

# CORS (allow your GitHub Pages + local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://hsiddharth553-lgtm.github.io",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
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
    title TEXT,
    url TEXT,
    image TEXT,
    price TEXT,
    mrp TEXT
)
""")
conn.commit()

# ===== MODELS =====
class LoginRequest(BaseModel):
    id_token: str

class FavoriteRequest(BaseModel):
    url: str

# ===== HELPERS =====
def scrape_flipkart(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    r = requests.get(url, headers=headers, timeout=15)
    if r.status_code != 200:
        raise Exception("Failed to fetch product page")

    soup = BeautifulSoup(r.text, "html.parser")

    # Title
    title_tag = soup.find("span", {"class": "B_NuCI"})
    title = title_tag.get_text(strip=True) if title_tag else "Unknown Product"

    # Image
    img_tag = soup.find("img", {"class": "_396cs4"})
    image = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

    # Price
    price_tag = soup.find("div", {"class": "_30jeq3 _16Jk6d"})
    price = price_tag.get_text(strip=True) if price_tag else "N/A"

    # MRP
    mrp_tag = soup.find("div", {"class": "_3I9_wc _2p6lqe"})
    mrp = mrp_tag.get_text(strip=True) if mrp_tag else ""

    return {
        "title": title,
        "image": image,
        "price": price,
        "mrp": mrp,
        "url": url
    }

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

# ===== ROUTES =====

@app.post("/login")
def login(data: LoginRequest):
    email = verify_token(data.id_token)
    return {"email": email}

@app.post("/favorite")
def add_favorite(token: str, data: FavoriteRequest):
    email = verify_token(token)

    if "flipkart.com" not in data.url:
        raise HTTPException(status_code=400, detail="Only Flipkart links supported")

    product = scrape_flipkart(data.url)

    cur.execute(
        "INSERT INTO favorites (email, title, url, image, price, mrp) VALUES (?, ?, ?, ?, ?, ?)",
        (email, product["title"], product["url"], product["image"], product["price"], product["mrp"])
    )
    conn.commit()

    return {"status": "ok", "product": product}

@app.get("/favorites")
def get_favorites(token: str):
    email = verify_token(token)

    cur.execute(
        "SELECT title, url, image, price, mrp FROM favorites WHERE email = ?",
        (email,)
    )
    rows = cur.fetchall()

    result = []
    for r in rows:
        result.append({
            "title": r[0],
            "url": r[1],
            "image": r[2],
            "price": r[3],
            "mrp": r[4],
        })

    return result

@app.delete("/favorite")
def delete_favorite(token: str, url: str):
    email = verify_token(token)

    cur.execute(
        "DELETE FROM favorites WHERE email = ? AND url = ?",
        (email, url)
    )
    conn.commit()

    return {"status": "deleted"}
