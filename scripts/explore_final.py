"""
Full detailed exploration of the Emboscada movie page and search page.
Run with: uv run --with beautifulsoup4 --with requests scripts/explore_final.py
"""
import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
}

WB_RE = re.compile(r"https?://web\.archive\.org/web/[^/]*/")


def clean(url):
    return WB_RE.sub("", url)


def fetch(url):
    resp = requests.get(url, headers=HEADERS, timeout=30)
    print(f"Fetch {url[:80]} -> {resp.status_code}, {len(resp.text)} chars")
    return resp.text


# 1. Full Emboscada movie page
html = fetch("https://web.archive.org/web/20240617125042/https://comando.la/emboscada-torrent-2023-dual-audio-web-dl-1080p/")
soup = BeautifulSoup(html, "html.parser")

print("\n=== FULL MOVIE DETAIL STRUCTURE: Emboscada ===")
entry = soup.find(class_="entry-content")

print("\nFULL ENTRY-CONTENT HTML:")
print(str(entry))

print("\n\n=== DOWNLOAD SECTION - all links in entry ===")
if entry:
    for a in entry.find_all("a"):
        href = a.get('href', '')
        text = a.get_text(strip=True)
        cls = ' '.join(a.get('class', []))
        print(f"  text='{text[:50]}' class='{cls}' href='{href[:100]}'")

# 2. Fetch Young Sheldon full content
html2 = fetch("https://web.archive.org/web/20240520230952/https://comando.la/young-sheldon-7a-temporada-torrent-2024-dual-audio-5-1-dublado-web-dl-720p-1080p-2160p-4k-download/")
soup2 = BeautifulSoup(html2, "html.parser")
entry2 = soup2.find(class_="entry-content")

print("\n\n=== FULL SERIES DETAIL: Young Sheldon ===")
print("\nFULL ENTRY-CONTENT HTML:")
print(str(entry2))

print("\n\n=== ALL LINKS IN YOUNG SHELDON ENTRY ===")
if entry2:
    for a in entry2.find_all("a"):
        href = a.get('href', '')
        text = a.get_text(strip=True)
        # Clean the wayback wrapper for magnet links
        if "magnet:" in href:
            clean_href = clean(href)
            print(f"  MAGNET text='{text[:40]}' href='{clean_href[:150]}'")
        else:
            clean_href = clean(href)
            print(f"  LINK text='{text[:40]}' href='{clean_href[:80]}'")

# 3. Try search with timestamps that exist
search_timestamps = ["20240520230952", "20240617125042", "20230801000000"]
for ts in search_timestamps:
    html3 = fetch(f"https://web.archive.org/web/{ts}/https://comando.la/?s=avatar")
    soup3 = BeautifulSoup(html3, "html.parser")
    title = soup3.find("title")
    if title and "Wayback" not in title.get_text():
        print(f"\n=== SEARCH RESULTS (ts={ts}): avatar ===")
        articles = soup3.find_all("article")
        print(f"Articles: {len(articles)}")
        for art in articles[:5]:
            h2 = art.find("h2")
            a = h2.find("a") if h2 else None
            if a:
                print(f"  {a.get_text(strip=True)[:70]} -> {clean(a.get('href', ''))}")
        break
    else:
        print(f"  ts {ts}: Wayback index (no content)")
