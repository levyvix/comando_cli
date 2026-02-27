"""
Fetch a snapshot of comando.la from Wayback Machine.
Run with: uv run --with scrapling --with beautifulsoup4 --with requests scripts/explore_wayback.py
"""
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
}

def fetch_wayback(url, timestamp="20250201000000"):
    """Fetch a page from Wayback Machine."""
    wayback_url = f"https://web.archive.org/web/{timestamp}/{url}"
    print(f"Fetching: {wayback_url}")
    resp = requests.get(wayback_url, headers=HEADERS, timeout=30)
    print(f"Status: {resp.status_code}")
    return resp.text


def analyze(html, label, save_path=None):
    if save_path:
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Saved to {save_path} ({len(html)} chars)")

    soup = BeautifulSoup(html, "html.parser")

    print(f"\n=== ANALYSIS: {label} ===")

    title = soup.find("title")
    print(f"Title: {title.get_text() if title else 'N/A'}")

    print("\n--- BODY CHILDREN ---")
    body = soup.find("body")
    if body:
        for child in list(body.children)[:20]:
            if hasattr(child, 'name') and child.name:
                cls = ' '.join(child.get('class', []))[:70]
                id_ = child.get('id', '')
                print(f"  <{child.name} class='{cls}' id='{id_}'>")

    print("\n--- NAV LINKS ---")
    for sel in [("nav", {}), ("ul", {"id": "menu-primary"}), ("ul", {"id": "primary-menu"}),
                ("div", {"id": "navigation"}), ("header", {})]:
        tag, attrs = sel
        found = soup.find(tag, attrs)
        if found:
            links = found.find_all("a")
            print(f"  <{tag} {attrs}>: {len(links)} links")
            for l in links[:15]:
                print(f"    [{l.get_text(strip=True)[:40]}] -> {l.get('href', '')[:80]}")
            break

    print("\n--- CONTENT CARDS ---")
    # WordPress-style articles
    articles = soup.find_all("article")
    if articles:
        print(f"Found {len(articles)} <article> elements")
        for article in articles[:3]:
            cls = ' '.join(article.get('class', []))
            h = article.find(["h1", "h2", "h3"])
            a = article.find("a", href=True)
            img = article.find("img")
            cats = article.find_all(class_=lambda c: c and ('cat' in ' '.join(c if isinstance(c, list) else [c]).lower() or 'type' in ' '.join(c if isinstance(c, list) else [c]).lower()))
            print(f"  <article class='{cls}'>")
            if h:
                print(f"    Title: {h.get_text(strip=True)[:80]}")
                title_a = h.find("a")
                if title_a:
                    print(f"    Title URL: {title_a.get('href', '')}")
            if a and (not h or a != h.find("a")):
                print(f"    Link: {a.get('href', '')[:80]}")
            if img:
                print(f"    Img: {img.get('src', img.get('data-src', img.get('data-lazy-src', '')))[:80]}")
            if cats:
                for cat in cats[:2]:
                    print(f"    Category: {cat.get_text(strip=True)[:40]}")
            print()
    else:
        # Try other selectors
        for sel in [".post", ".item", ".movie", ".serie", "li[class*=post]", "div[class*=post]"]:
            items = soup.select(sel)
            if items:
                print(f"  '{sel}': {len(items)} items")
                for item in items[:2]:
                    print(f"    HTML (400): {str(item)[:400]}")
                break

    print("\n--- PAGINATION ---")
    for sel in [".pagination", ".paginacao", ".wp-pagenavi", ".nav-links", ".page-numbers", "[class*=pag]"]:
        items = soup.select(sel)
        if items:
            print(f"  '{sel}': {str(items[0])[:300]}")
            break

    print("\n--- SEARCH FORM ---")
    forms = soup.find_all("form")
    for form in forms[:3]:
        action = form.get('action', '')
        method = form.get('method', 'get')
        inputs = form.find_all("input")
        print(f"  <form action='{action}' method='{method}'>")
        for inp in inputs:
            print(f"    <input type='{inp.get('type','')}' name='{inp.get('name','')}' placeholder='{inp.get('placeholder','')}'>")

    print("\n--- MAGNET LINKS ---")
    magnets = soup.find_all("a", href=lambda x: x and x.startswith("magnet:"))
    print(f"Found {len(magnets)} magnet links")
    for m in magnets[:5]:
        print(f"  title: {m.get('title', '')}")
        print(f"  class: {' '.join(m.get('class', []))}")
        print(f"  text: {m.get_text(strip=True)[:60]}")
        print(f"  href (130): {m.get('href', '')[:130]}")
        parent = m.parent
        if parent:
            print(f"  parent: <{parent.name} class='{' '.join(parent.get('class', []))}'>")
            # Look for nearby elements
            siblings = list(parent.children)
            for sib in siblings[:5]:
                if hasattr(sib, 'name') and sib.name and sib != m:
                    print(f"    sibling: <{sib.name} class='{' '.join(sib.get('class', []))}'>: {sib.get_text(strip=True)[:40]}")
        print()

    # All quality-related elements
    print("\n--- QUALITY/DOWNLOAD ELEMENTS ---")
    for sel in [".botao_dublado", "[class*=botao]", "[class*=download]", "[class*=torrent]",
                "[class*=quality]", "[class*=lang]", "[class*=dub]", "[class*=leg]"]:
        items = soup.select(sel)
        if items:
            print(f"  '{sel}': {len(items)}")
            for item in items[:3]:
                print(f"    {str(item)[:200]}")

    print("\n--- FIRST 2000 CHARS ---")
    print(html[:2000])


# Fetch homepage
try:
    html = fetch_wayback("https://comando.la/", "20250215000000")
    analyze(html, "HOMEPAGE", "/tmp/wayback_home.html")
except Exception as e:
    print(f"Error fetching homepage: {e}")

# Fetch search results
try:
    html = fetch_wayback("https://comando.la/?s=avatar", "20250215000000")
    analyze(html, "SEARCH RESULTS", "/tmp/wayback_search.html")
except Exception as e:
    print(f"Error fetching search: {e}")

# Try a specific movie page
try:
    html = fetch_wayback("https://comando.la/category/filmes/", "20250215000000")
    analyze(html, "FILMES CATEGORY", "/tmp/wayback_filmes.html")
except Exception as e:
    print(f"Error: {e}")
