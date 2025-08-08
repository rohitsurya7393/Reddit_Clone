# Reddit Clone MVP (Flask)
A tiny Reddit-style app with users, subreddits, posts, comments, and voting.

## Quickstart
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
flask --app app.py init-db
flask --app app.py run
```

Visit http://127.0.0.1:5000

## Features
- Auth (register/login/logout)
- Create subreddits (`r/<name>`) and posts
- Comment on posts
- Upvote/downvote posts and comments (toggle/change)
- Sort by **Hot** (score) and **New**

## Notes
- SQLite DB lives at `reddit.db` (see `config.py`).
- Change `SECRET_KEY` and `DATABASE_URL` via env vars in prod.
