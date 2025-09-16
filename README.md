# Match - Sponsorship-aware Job Finder — MVP

This repository contains a small proof-of-concept system that:
- Searches the web for job postings (Bing HTML search).
- Scrapes job pages (example: Indeed) for description, company, title.
- Detects sponsorship-related language via keyword/NLP.
- Cross-checks companies against a local H-1B CSV dataset.
- Stores everything in SQLite.
- Exposes a Streamlit app to browse results, open original job posting (apply), and generate verification email drafts.

## Files
- `scraper.py` — run to search and scrape job postings (stores into `jobs.db`).
- `nlp_utils.py` — sponsorship detection logic.
- `h1b_loader.py` — load H-1B CSV and lookup company history.
- `db.py` — SQLite wrapper.
- `app.py` — Streamlit app.
- `sample_h1b.csv` — tiny sample H-1B CSV.
- `requirements.txt`

## Quick start (local)

1. Clone the repo:
```bash
git clone <your-repo-url>
cd repo
