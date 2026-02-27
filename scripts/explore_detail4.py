"""
Fetch movie detail and search pages from Wayback Machine.
Run with: uv run --with beautifulsoup4 --with requests scripts/explore_detail4.py
"""
import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
}

WB_PATTERN = re.compile(r"https://web\.archive\.org/web/\d+/")


def clean_url(url):
    """Remove Wayback Machine wrapper from URL."""
    return WB_PATTERN.sub("", url)


def fetch(url):
    print(f"Fetching: {url[:100]}")
    resp = requests.get(url, headers=HEADERS, timeout=30)
    print(f"  Status: {resp.status_code}, Size: {len(resp.text)}")
    return resp.text


def analyze_movie_detail(html, label, save_path=None):
    if save_path:
        with open(save_path, "w") as f:
            f.write(html)

    soup = BeautifulSoup(html, "html.parser")
    print(f"\n{'='*60}")
    print(f"MOVIE DETAIL: {label}")
    print("="*60)

    h1 = soup.find("h1")
    print(f"H1: {h1.get_text(strip=True)[:80] if h1 else 'N/A'}")

    entry = soup.find(class_="entry-content")
    if not entry:
        print("No entry-content!")
        return

    # Poster image
    poster = entry.find("img")
    if poster:
        src = clean_url(poster.get('src', poster.get('data-src', '')))
        print(f"\nPoster: {src[:80]}")
        print(f"  alt: {poster.get('alt', '')}")

    # Metadata paragraph
    print(f"\nMETADATA (first paragraph):")
    first_p = entry.find("p")
    if first_p:
        text = first_p.get_text(separator='\n', strip=True)
        print(text[:500])

    # Find all magnet links - clean up wayback prefix
    print(f"\nMAGNET LINKS:")
    all_hrefs = [a.get('href', '') for a in entry.find_all("a")]
    magnet_hrefs = []
    for href in all_hrefs:
        # Wayback wraps as: https://web.archive.org/web/TS/magnet:?...
        if "magnet:" in href:
            clean = re.sub(r"https://web\.archive\.org/web/[^/]+/", "", href)
            magnet_hrefs.append((href, clean))

    print(f"  Total: {len(magnet_hrefs)}")
    for orig, clean in magnet_hrefs[:10]:
        # Find the <a> with this href
        a = entry.find("a", href=orig)
        if a:
            text = a.get_text(strip=True)
            title_attr = a.get('title', '')
            cls = ' '.join(a.get('class', []))
            parent = a.parent

            print(f"\n  text='{text}' title='{title_attr[:50]}'")
            print(f"  class='{cls}'")
            print(f"  clean magnet: {clean[:150]}")
            if parent:
                print(f"  parent: <{parent.name} class='{' '.join(parent.get('class', []))}'> = '{parent.get_text(strip=True)[:80]}'")
                gp = parent.parent
                if gp:
                    print(f"  grandparent: <{gp.name} class='{' '.join(gp.get('class', []))}'> = '{gp.get_text(strip=True)[:60]}'")

    # Print full entry content
    print(f"\nFULL ENTRY (3000 chars):")
    print(str(entry)[:3000])


def analyze_search_results(html, label):
    soup = BeautifulSoup(html, "html.parser")
    print(f"\n{'='*60}")
    print(f"SEARCH RESULTS: {label}")
    print("="*60)

    title = soup.find("title")
    print(f"Title: {title.get_text() if title else 'N/A'}")

    h1 = soup.find("h1")
    print(f"H1: {h1.get_text(strip=True)[:80] if h1 else 'N/A'}")

    articles = soup.find_all("article")
    print(f"\nArticles: {len(articles)}")
    for art in articles[:5]:
        h2 = art.find("h2")
        a = h2.find("a") if h2 else None
        img = art.find("img")
        cats = [clean_url(c.get('href', '')) for c in art.find_all("a", href=lambda x: x and "/category/" in str(x))][:3]

        print(f"\n  Article classes: {' '.join(art.get('class', []))[:80]}")
        if a:
            url = clean_url(a.get('href', ''))
            print(f"  Title: {a.get_text(strip=True)[:70]}")
            print(f"  URL: {url}")
        if img:
            src = clean_url(img.get('src', img.get('data-src', '')))
            print(f"  Img: {src[:70]}")
        if cats:
            print(f"  Categories: {cats}")

    # Check search form structure
    print(f"\nSEARCH FORM:")
    form = soup.find("form", attrs={"method": "get"})
    if form:
        action = clean_url(form.get('action', ''))
        print(f"  <form action='{action}'>")
        for inp in form.find_all("input"):
            print(f"    <input type='{inp.get('type','')}' name='{inp.get('name','')}' placeholder='{inp.get('placeholder','')}'>")


# Movie detail page
try:
    # Use Young Sheldon as a series, try to find a movie
    # Let's try Emboscada
    html = fetch("https://web.archive.org/web/20240617125042/https://comando.la/emboscada-torrent-2023-dual-audio-web-dl-1080p/")
    analyze_movie_detail(html, "Emboscada (2023)", "/tmp/detail_emboscada.html")
except Exception as e:
    print(f"Emboscada error: {e}")

# Another movie
try:
    html = fetch("https://web.archive.org/web/20240617125042/https://comando.la/vampiras-as-noivas-de-dracula-torrent-2024-dual-audio-5-1-web-dl-1080p/")
    analyze_movie_detail(html, "Vampiras (2024)", "/tmp/detail_vampiras.html")
except Exception as e:
    print(f"Vampiras error: {e}")

# Search results
try:
    html = fetch("https://web.archive.org/web/20240617125042/https://comando.la/?s=avatar")
    analyze_search_results(html, "avatar")
    with open("/tmp/search_avatar_wb.html", "w") as f:
        f.write(html)
except Exception as e:
    print(f"Search error: {e}")

# Also try a different search
try:
    html = fetch("https://web.archive.org/web/20240617125042/https://comando.la/?s=batman")
    analyze_search_results(html, "batman")
except Exception as e:
    print(f"Batman search error: {e}")
