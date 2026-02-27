"""
Fetch detail pages from Wayback Machine to understand the structure of movie/series pages.
Run with: uv run --with beautifulsoup4 --with requests scripts/explore_detail.py
"""
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
}


def fetch_wayback(url, timestamp="20240617125042"):
    wayback_url = f"https://web.archive.org/web/{timestamp}/{url}"
    print(f"Fetching: {wayback_url}")
    resp = requests.get(wayback_url, headers=HEADERS, timeout=30)
    print(f"Status: {resp.status_code}, Size: {len(resp.text)} chars")
    return resp.text


def analyze_listing(html, label, save_path):
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(html)

    soup = BeautifulSoup(html, "html.parser")
    print(f"\n{'='*60}")
    print(f"LISTING PAGE: {label}")
    print("="*60)

    # Articles
    articles = soup.find_all("article")
    print(f"\nArticles: {len(articles)}")
    for article in articles[:5]:
        cls = ' '.join(article.get('class', []))
        h2 = article.find("h2")
        a_in_h2 = h2.find("a") if h2 else None
        img = article.find("img")
        cats = article.find_all("a", href=lambda x: x and "/category/" in str(x))
        thumbnail = article.find("div", class_="post-thumbnail") or article.find(class_=lambda c: c and "thumbnail" in ' '.join(c if isinstance(c, list) else [c]).lower())

        print(f"\n  Article classes: {cls[:100]}")
        if a_in_h2:
            print(f"  Title: {a_in_h2.get_text(strip=True)[:80]}")
            print(f"  URL: {a_in_h2.get('href', '')}")
        if img:
            src = img.get('src', img.get('data-src', img.get('data-lazy-src', '')))
            print(f"  Img src: {src[:80]}")
            print(f"  Img class: {' '.join(img.get('class', []))}")
        if cats:
            cat_names = [c.get_text(strip=True) for c in cats[:5]]
            print(f"  Categories: {cat_names}")
        # Find entry-summary or excerpt
        summary = article.find(class_=lambda c: c and ("summary" in ' '.join(c if isinstance(c, list) else [c]).lower() or "excerpt" in ' '.join(c if isinstance(c, list) else [c]).lower()))
        if summary:
            print(f"  Summary: {summary.get_text(strip=True)[:100]}")

    # Pagination structure
    print(f"\n--- PAGINATION ---")
    pag = soup.find(class_="wp-pagenavi")
    if pag:
        print(f"wp-pagenavi structure:")
        print(str(pag)[:600])
        page_links = pag.find_all("a")
        print(f"Page links: {[(l.get_text(strip=True), l.get('href','')[:50]) for l in page_links[:5]]}")

    # Navigation categories
    print(f"\n--- CATEGORIES ---")
    nav = soup.find("nav")
    if nav:
        links = nav.find_all("a")
        print(f"Nav links ({len(links)}):")
        for l in links[:20]:
            # Clean up wayback URLs
            href = l.get('href', '')
            if 'web.archive.org' in href:
                href = href.split('https://comando.la')[-1] if 'comando.la' in href else href
            print(f"  [{l.get_text(strip=True)[:30]}] -> {href[:60]}")


def analyze_detail(html, label, save_path):
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(html)

    soup = BeautifulSoup(html, "html.parser")
    print(f"\n{'='*60}")
    print(f"DETAIL PAGE: {label}")
    print("="*60)

    # Title
    h1 = soup.find("h1")
    print(f"\nH1 Title: {h1.get_text(strip=True) if h1 else 'N/A'}")

    # Entry content
    entry = soup.find(class_="entry-content") or soup.find(class_="post-content")
    if entry:
        print(f"\n--- ENTRY CONTENT structure ---")
        # First image (poster)
        imgs = entry.find_all("img")
        for img in imgs[:3]:
            src = img.get('src', img.get('data-src', ''))
            print(f"  Img: {src[:80]}")
            print(f"  Img class: {' '.join(img.get('class', []))}")

        # Text content
        paras = entry.find_all("p")
        print(f"\n  Paragraphs ({len(paras)}):")
        for p in paras[:5]:
            txt = p.get_text(strip=True)[:100]
            if txt:
                print(f"    {txt}")

        # Download buttons / magnet links
        print(f"\n  Download elements:")
        all_links = entry.find_all("a")
        for a in all_links:
            href = a.get('href', '')
            if href.startswith("magnet:"):
                title = a.get('title', '')
                cls = ' '.join(a.get('class', []))
                text = a.get_text(strip=True)[:50]
                print(f"\n  MAGNET LINK:")
                print(f"    text: {text}")
                print(f"    title attr: {title}")
                print(f"    class: {cls}")
                print(f"    href (160): {href[:160]}")
                # Context
                parent = a.parent
                if parent:
                    print(f"    parent: <{parent.name} class='{' '.join(parent.get('class', []))}'>")
                    print(f"    parent text: {parent.get_text(strip=True)[:80]}")
                    # Check grandparent
                    gparent = parent.parent
                    if gparent:
                        print(f"    grandparent: <{gparent.name} class='{' '.join(gparent.get('class', []))}'>")
                        print(f"    grandparent text: {gparent.get_text(strip=True)[:100]}")

        # Look for quality/language labels
        print(f"\n--- QUALITY/LANGUAGE LABELS ---")
        botao_spans = entry.find_all("span", class_="botao_dublado")
        print(f"  botao_dublado spans: {len(botao_spans)}")
        for span in botao_spans[:5]:
            print(f"    text: {span.get_text(strip=True)}")
            # Find next magnet link after this span
            next_sibling = span.find_next_sibling("a")
            if next_sibling and next_sibling.get('href', '').startswith("magnet:"):
                print(f"    next magnet href (80): {next_sibling.get('href', '')[:80]}")

        # Look for all button-like elements
        for sel in ["[class*=botao]", "[class*=button]", "[class*=download]", ".wp-block-button"]:
            items = entry.select(sel)
            if items:
                print(f"\n  '{sel}' ({len(items)}):")
                for item in items[:5]:
                    print(f"    {str(item)[:200]}")

    # Meta info
    print(f"\n--- META INFO ---")
    meta_els = soup.find_all(class_=lambda c: c and ("meta" in ' '.join(c if isinstance(c, list) else [c]).lower() or "info" in ' '.join(c if isinstance(c, list) else [c]).lower()))
    for el in meta_els[:5]:
        print(f"  <{el.name} class='{' '.join(el.get('class', [])[:3])}'>: {el.get_text(strip=True)[:100]}")

    # Print raw entry content HTML
    if entry:
        print(f"\n--- RAW ENTRY CONTENT (2000 chars) ---")
        print(str(entry)[:2000])


# Fetch listing pages
try:
    html = fetch_wayback("https://comando.la/category/filmes/", "20240617125042")
    analyze_listing(html, "Filmes Category", "/tmp/detail_filmes.html")
except Exception as e:
    print(f"Error: {e}")

# Fetch a series listing
try:
    html = fetch_wayback("https://comando.la/category/series/", "20240617125042")
    analyze_listing(html, "Series Category", "/tmp/detail_series.html")
except Exception as e:
    print(f"Error: {e}")

# Fetch a specific movie detail page
try:
    html = fetch_wayback("https://comando.la/ultraman-a-ascensao-torrent-2024-audio-dublado-web-dl-1080p/", "20240617125042")
    analyze_detail(html, "Movie Detail: Ultraman", "/tmp/detail_movie.html")
except Exception as e:
    print(f"Error: {e}")

# Fetch a series page
try:
    # Let's find a series URL from the listing first
    html_series = fetch_wayback("https://comando.la/category/series/", "20240617125042")
    soup_s = BeautifulSoup(html_series, "html.parser")
    articles = soup_s.find_all("article")
    if articles:
        a = articles[0].find("h2").find("a") if articles[0].find("h2") else None
        if a:
            series_url = a.get('href', '').replace('https://web.archive.org/web/20240617125042/', '')
            if series_url.startswith('https://comando.la'):
                print(f"\nFound series URL: {series_url}")
                html = fetch_wayback(series_url, "20240617125042")
                analyze_detail(html, "Series Detail", "/tmp/detail_series_page.html")
except Exception as e:
    print(f"Error fetching series detail: {e}")
