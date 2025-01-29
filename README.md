# Shorten My URL (SMURL)

SMURL is a lightweight, self-hosted URL shortener built with FastAPI and SQLite.  
It provides a simple, dark-themed interface for shortening URLs and viewing analytics.

A flagship instance is available at [s.sij.ai](https://s.sij.ai).

## Installation

Clone the repository:

```sh
git clone https://sij.ai/sij/smurl.git
cd smurl
```

Create a virtual environment and install dependencies:

```sh
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate  # Windows

pip install fastapi uvicorn
```

Initialize the database:

```sh
python -c "import smurl; smurl.init_db()"
```

## Running

Start the FastAPI server:

```sh
uvicorn smurl:app --host 0.0.0.0 --port 7997 --reload
```

SMURL assumes you're using a reverse proxy for TLS termination.  
[Caddy](https://caddyserver.com) is recommended.

## Usage

### Shorten a URL
1. Visit [s.sij.ai](https://s.sij.ai).
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

## Development

Modify `smurl.py`, `templates/index.html`, or `static/css/styles.css`, then restart:

```sh
uvicorn smurl:app --reload
```

## License

Released under the **MIT License**.