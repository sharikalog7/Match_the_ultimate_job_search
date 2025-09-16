# scraper.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote_plus
import time
from tqdm import tqdm

from nlp_utils import detect_sponsorship
from h1b_loader import H1BLookup
from db import JobDB

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JobSponsorBot/1.0; +https://example.com/bot)"
}

def bing_search(query: str, limit: int = 20):
    """
    Simple Bing HTML search scraping to find candidate job posting URLs.
    Returns list of urls (best-effort). Fragile; for production use an API.
    """
    results = []
    page = 0
    per_page = 10
    while len(results) < limit:
        offset = page * per_page
        q = quote_plus(query)
        url = f"https://www.bing.com/search?q={q}&first={offset+1}"
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        items = soup.select("li.b_algo h2 a")
        for a in items:
            href = a.get("href")
            if href and href not in results:
                results.append(href)
                if len(results) >= limit:
                    break
        page += 1
        time.sleep(1.0)  # polite pause
        if page > 5:
            break
    return results[:limit]

def parse_indeed(url: str):
    """
    Best-effort parsing of Indeed job page for description text, company, title, location.
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        return None
    soup = BeautifulSoup(r.text, "html.parser")

    # Title
    title = None
    t = soup.find("h1")
    if t:
        title = t.get_text(strip=True)

    # Company
    company = None
    comp = soup.select_one(".icl-u-lg-mr--sm.icl-u-xs-mr--xs")
    if comp:
        company = comp.get_text(strip=True)
    # fallback
    if not company:
        comp2 = soup.find("div", {"class": "jobsearch-InlineCompanyRating"})
        if comp2:
            company = comp2.get_text(" ", strip=True)

    # Location
    location = None
    loc = soup.select_one(".jobsearch-JobInfoHeader-subtitle div")
    if loc:
        location = loc.get_text(strip=True)

    # Description
    desc_el = soup.find(id="jobDescriptionText")
    description = desc_el.get_text("\n", strip=True) if desc_el else ""

    return {
        "title": title,
        "company": company,
        "location": location,
        "description": description
    }

def parse_generic(url: str):
    """Fallback: fetch page and take title and meta description snippet."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.title.string.strip() if soup.title else None
    # meta description
    md = soup.find("meta", attrs={"name":"description"}) or soup.find("meta", attrs={"property":"og:description"})
    description = md.get("content").strip() if md and md.get("content") else ""
    # Try to find company name heuristically
    company = None
    # Many job sites include 'company' or 'employer' in class names - best effort
    for sel in ["div.company", ".company", ".employer", "[itemprop='hiringOrganization']"]:
        el = soup.select_one(sel)
        if el:
            company = el.get_text(" ", strip=True)
            break

    return {
        "title": title,
        "company": company,
        "location": None,
        "description": description
    }

def extract_and_store(query: str, h1b_csv_path: str, limit: int = 20, db_path: str = "jobs.db"):
    links = bing_search(query, limit=limit)
    print(f"Found {len(links)} candidate links from search.")
    h1b = H1BLookup(h1b_csv_path)
    db = JobDB(path=db_path)

    for link in tqdm(links):
        parsed = None
        # naive site detection for Indeed
        try:
            hostname = urlparse(link).hostname or ""
        except:
            hostname = ""
        if "indeed." in hostname:
            parsed = parse_indeed(link)
        else:
            parsed = parse_generic(link)

        if not parsed:
            continue

        title = parsed.get("title") or ""
        company = parsed.get("company") or ""
        location = parsed.get("location") or ""
        description = parsed.get("description") or ""

        sponsorship_flag, diagnostic = detect_sponsorship(description + " " + title)
        h1b_hist = h1b.company_history(company) if company else None

        ok = db.insert_job(
            title=title,
            company=company,
            location=location,
            url=link,
            description=description,
            sponsorship_flag=sponsorship_flag,
            diagnostic=diagnostic,
            h1b_history=h1b_hist
        )
        # polite delay
        time.sleep(0.8)

    db.close()
    print("Done scraping and storing.")
