"""
Exploration script for comando.la using StealthyFetcher with chromium (no real_chrome).
Run with: uv run --with scrapling scripts/explore_v5.py
"""
from scrapling.fetchers import StealthyFetcher


def fetch(url, label=""):
    print(f"\n{'='*60}")
    print(f"FETCHING: {label or url}")
    print("="*60)
    page = StealthyFetcher.fetch(
        url,
        headless=True,
        network_idle=True,
        google_search=False,
    )
    print(f"Status: {page.status}, URL: {page.url}")
    title_el = page.css("title")
    print(f"Title: {title_el[0].text if title_el else 'N/A'}")
    return page


def save_html(page, path):
    body = page.body
    if isinstance(body, bytes):
        body = body.decode('utf-8', errors='replace')
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"Saved {len(body)} chars to {path}")
    return body


def print_structure(page):
    print("\n--- BODY CHILDREN ---")
    for child in page.css("body > *")[:15]:
        cls = child.attrib.get('class', '')[:70]
        id_ = child.attrib.get('id', '')
        print(f"  <{child.tag} class='{cls}' id='{id_}'>")

    print("\n--- ALL LINKS (first 40) ---")
    for a in page.css("a")[:40]:
        href = a.attrib.get('href', '')
        text = a.text.strip()[:50]
        print(f"  [{text}] -> {href}")

    print("\n--- CONTENT CARDS ---")
    for sel in ["article", ".post", ".card", "li[class*='post']", "div[class*='post']", ".item"]:
        items = page.css(sel)
        if items:
            print(f"Selector '{sel}': {len(items)} items")
            for item in items[:2]:
                print(f"  HTML: {str(item)[:500]}")
                print()
            break

    print("\n--- SEARCH FORM ---")
    for sel in ["form", "input[type='search']", "input[name='s']", "input[name='q']"]:
        items = page.css(sel)
        if items:
            print(f"Selector '{sel}': {str(items[0])[:200]}")
            break


def print_magnet_info(page):
    print("\n--- MAGNET LINKS ---")
    magnets = page.css("a[href^='magnet:']")
    print(f"Total magnet links: {len(magnets)}")
    for m in magnets[:10]:
        href = m.attrib.get('href', '')
        print(f"  title attr: {m.attrib.get('title', '')}")
        print(f"  text: {m.text.strip()[:60]}")
        print(f"  class: {m.attrib.get('class', '')}")
        print(f"  href (150): {href[:150]}")
        # Check parent elements for context
        parent = m.parent
        if parent:
            print(f"  parent <{parent.tag} class='{parent.attrib.get('class', '')}'>")
            prev = parent.css("span[class*='botao'], [class*='quality'], [class*='lang']")
            if prev:
                print(f"  nearby span: {str(prev[0])[:150]}")
        print()

    print("\n--- QUALITY/LANGUAGE SPANS ---")
    for sel in [".botao_dublado", "[class*='botao']", "[class*='quality']", "[class*='download']", "[class*='torrent']"]:
        items = page.css(sel)
        if items:
            print(f"Selector '{sel}': {len(items)} items")
            for item in items[:5]:
                print(f"  {str(item)[:200]}")
            break


if __name__ == "__main__":
    # 1. Homepage
    try:
        page = fetch("https://comando.la", "HOMEPAGE")
        html = save_html(page, "/tmp/comando_home.html")
        print_structure(page)
        print("\n--- FIRST 3000 CHARS ---")
        print(html[:3000])
    except Exception as e:
        print(f"Error: {e}")
        import traceback; traceback.print_exc()

    # 2. Search
    try:
        page = fetch("https://comando.la/?s=avatar", "SEARCH: avatar")
        html = save_html(page, "/tmp/comando_search.html")
        print_structure(page)
    except Exception as e:
        print(f"Error: {e}")
        import traceback; traceback.print_exc()
