# Pastel Time Tracker (Single-User)

A simple, local-first time tracker with a pastel, subtly transparent UI. Track activities grouped under larger categories (e.g., Exercise, Reading, Work, Play). View weekly and monthly summaries. Built with FastAPI, SQLite, and Jinja templates.

## Features (MVP)
- Manual entries with date, category, activity, duration, notes
- Categories and activities management
- Weekly and monthly summaries by category and activity
- CSV export
- Pastel + glass UI

## Requirements
- Python 3.11+

## Setup
```bash
cd ~/pastel-time-tracker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 in your browser.

## Project Structure
```
app/
  main.py
  database.py
  models.py
  schemas.py
  crud.py
  templates/
    base.html
    index.html
    weekly.html
    monthly.html
    manage_categories.html
    manage_activities.html
    settings.html
    chart_pie.html
  static/
    styles.css
    app.js
  utils/
    time_utils.py
.github/
  workflows/
    ci.yml
requirements.txt
requirements-dev.txt
README.md
.gitignore
```

## Development

Install dev tools and run basic checks:
```bash
pip install -r requirements-dev.txt
black --check .
```
