# Shorten My URL (SMURL)

SMURL is a lightweight, self-hosted URL shortener built with FastAPI and SQLite. It provides a simple, dark-themed interface for shortening URLs and viewing analytics. 

A testbed instance is available at [s.sij.ai](https://s.sij.ai).

## Setup

Clone the repo and install dependencies:

```sh
git clone https://sij.ai/sij/smurl.git
cd smurl
pip install fastapi uvicorn
```

Start the FastAPI server:

```sh
python smurl.py
```

SMURL assumes you're using a reverse proxy for TLS termination. [Caddy](https://caddyserver.com) is recommended.

## Usage

### Shorten a URL
1. Visit the URL you've reverse proxied to your SMURL instance—or, for the testbed instance, [s.sij.ai](https://s.sij.ai).
2. Enter a URL (with or without `https://`).
3. Click **SMURL** to generate a short link.

### Redirect
Visit a shortened URL, e.g.:

```
https://s.sij.ai/abc123
```

### View Analytics
1. Enter the shortcode (`abc123`) in the same input box.
2. Click **SMURL** to view click statistics.