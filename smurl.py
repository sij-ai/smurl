from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3
import string
import random

app = FastAPI(title="SMURL")

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

def init_db():
    with sqlite3.connect('urls.db') as conn:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_code TEXT UNIQUE NOT NULL,
            original_url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        conn.execute('''
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url_id INTEGER NOT NULL,
            clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (url_id) REFERENCES urls(id)
        )''')

def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/process")
async def process_input(request: Request, user_input: str = Form(...)):
    user_input = user_input.strip()

    # If it contains a dot, assume it's a URL
    if "." in user_input:
        if not user_input.startswith(("http://", "https://")):
            user_input = "https://" + user_input

        with sqlite3.connect('urls.db') as conn:
            while True:
                short_code = generate_short_code()
                try:
                    conn.execute('INSERT INTO urls (short_code, original_url) VALUES (?, ?)',
                                (short_code, user_input))
                    conn.commit()
                    return templates.TemplateResponse("index.html", {
                        "request": request,
                        "short_url": f"{request.base_url}{short_code}"
                    })
                except sqlite3.IntegrityError:
                    continue  # Retry if collision

    # Otherwise, treat it as a shortcode and fetch analytics
    with sqlite3.connect('urls.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, original_url FROM urls WHERE short_code = ?', (user_input,))
        result = cursor.fetchone()

        if result:
            cursor.execute('SELECT COUNT(*) FROM clicks WHERE url_id = ?', (result[0],))
            click_count = cursor.fetchone()[0]

            return templates.TemplateResponse("index.html", {
                "request": request,
                "analytics_mode": True,
                "original_url": result[1],
                "click_count": click_count
            })

    return templates.TemplateResponse("index.html", {
        "request": request,
        "error": "Invalid input: Not a recognized URL or shortcode."
    })

@app.get("/{short_code}")
async def redirect_to_url(short_code: str):
    with sqlite3.connect('urls.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, original_url FROM urls WHERE short_code = ?', (short_code,))
        result = cursor.fetchone()

        if result:
            cursor.execute('INSERT INTO clicks (url_id) VALUES (?)', (result[0],))
            conn.commit()
            return RedirectResponse(url=result[1])

    raise HTTPException(status_code=404, detail="URL not found")

if __name__ == "__main__":
    init_db()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7997)
