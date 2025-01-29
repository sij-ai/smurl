from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
import sqlite3
import string
import random
from datetime import datetime, timedelta
import urllib.parse
from typing import List

app = FastAPI(title="SMURL")
host = "0.0.0.0"
port = 7997

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

def get_click_stats(url_id: int, timeframe: str) -> List[dict]:
    with sqlite3.connect('urls.db') as conn:
        now = datetime.now()
        if timeframe == 'day':
            interval = 'strftime("%Y-%m-%d %H:00:00", clicked_at)'
            start_time = now - timedelta(days=1)
        elif timeframe == 'week':
            interval = 'strftime("%Y-%m-%d", clicked_at)'
            start_time = now - timedelta(weeks=1)
        elif timeframe == 'year':
            interval = 'strftime("%Y-%m", clicked_at)'
            start_time = now - timedelta(days=365)
        else:  # all time
            interval = 'strftime("%Y-%m", clicked_at)'
            start_time = datetime.min

        cursor = conn.cursor()
        cursor.execute(f'''
            SELECT {interval} as period, COUNT(*) as clicks
            FROM clicks
            WHERE url_id = ? AND clicked_at > ?
            GROUP BY period
            ORDER BY period
        ''', (url_id, start_time))
        
        return [{"period": row[0], "clicks": row[1]} for row in cursor.fetchall()]

class URLRequest(BaseModel):
    url: HttpUrl

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/create")
async def create_short_url(url_request: URLRequest, request: Request):
    # Parse the input URL
    parsed_url = urllib.parse.urlparse(str(url_request.url))
    
    # Check if this is one of our own shortened URLs
    if parsed_url.netloc == request.base_url.netloc:
        # Extract the short code from the path
        short_code = parsed_url.path.strip('/')
        if short_code:
            with sqlite3.connect('urls.db') as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, original_url, created_at
                    FROM urls WHERE short_code = ?
                ''', (short_code,))
                url_data = cursor.fetchone()
                
                if url_data:
                    # Get click stats
                    stats = {
                        'day': get_click_stats(url_data['id'], 'day'),
                        'week': get_click_stats(url_data['id'], 'week'),
                        'year': get_click_stats(url_data['id'], 'year'),
                        'all': get_click_stats(url_data['id'], 'all')
                    }
                    return {
                        "is_analytics": True,
                        "original_url": url_data['original_url'],
                        "created_at": url_data['created_at'],
                        "stats": stats
                    }
    
    # If not our URL or no match found, create new short URL
    with sqlite3.connect('urls.db') as conn:
        while True:
            short_code = generate_short_code()
            try:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO urls (short_code, original_url) VALUES (?, ?)',
                           (short_code, str(url_request.url)))
                return {
                    "is_analytics": False,
                    "short_code": short_code
                }
            except sqlite3.IntegrityError:
                continue

@app.get("/{short_code}")
async def redirect_to_url(short_code: str):
    with sqlite3.connect('urls.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, original_url FROM urls WHERE short_code = ?', (short_code,))
        result = cursor.fetchone()
        
        if result:
            # Record the click
            cursor.execute('INSERT INTO clicks (url_id) VALUES (?)', (result[0],))
            conn.commit()
            return RedirectResponse(result[1])
        raise HTTPException(status_code=404, detail="URL not found")

if __name__ == "__main__":
    init_db()
    import uvicorn
    uvicorn.run(app, host=host, port=port)
