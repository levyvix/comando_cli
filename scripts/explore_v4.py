"""
Exploration script for comando.la using synchronous StealthyFetcher with real_chrome.
Run with: uv run --with scrapling scripts/explore_v4.py
"""
from scrapling.fetchers import StealthyFetcher


def explore_homepage():
    print("=" * 60)
    print("FETCHING HOMEPAGE with real_chrome=True")
    print("=" * 60)
    page = StealthyFetcher.fetch(
        "https://comando.la",
        headless=True,
        real_chrome=True,
        network_idle=True,
        google_search=False,
    )
    print(f"Status: {page.status}")
    print(f"URL: {page.url}")
    title_el = page.css("title")
    print(f"Title: {title_el[0].text if title_el else 'N/A'}")

    # Save HTML
    body = page.body.decode('utf-8') if isinstance(page.body, bytes) else page.body
    with open("/tmp/comando_homepage_v4.html", "w", encoding="utf-8") as f:
        f.write(body)
    print(f"Saved {len(body)} chars to /tmp/comando_homepage_v4.html")
    print()

    # Body structure
    print("--- BODY CHILDREN ---")
    for child in page.css("body > *")[:15]:
        cls = child.attrib.get('class', '')[:60]
        id_ = child.attrib.get('id', '')[:30]
        print(f"  <{child.tag} class='{cls}' id='{id_}'>")
    print()

    # Navigation
    print("--- NAVIGATION LINKS ---")
    for sel in ["nav a", "header a", ".menu-item a", ".main-navigation a", "#main-menu a"]:
        links = page.css(sel)
        if links:
            print(f"Selector '{sel}': {len(links)} links")
            for l in links[:20]:
                print(f"  [{l.text.strip()[:40]}] -> {l.attrib.get('href', '')}")
            break
    print()

    # Cards
    print("--- CONTENT CARDS ---")
    for sel in ["article", ".post", ".card", ".item", "li.post", "div.post"]:
        items = page.css(sel)
        if items:
            print(f"Selector '{sel}': {len(items)} items")
            first = items[0]
            print(f"  First HTML (600 chars):\n{str(first)[:600]}")
            print()
            break

    # Search form
    print("--- SEARCH ---")
    for sel in ["form", "input[type='search']", "input[name='s']"]:
        items = page.css(sel)
        if items:
            print(f"Selector '{sel}': {str(items[0])[:200]}")
    print()

    # All links
    print("--- ALL <a> TAGS (first 40) ---")
    for a in page.css("a")[:40]:
        href = a.attrib.get('href', '')
        text = a.text.strip()[:40]
        print(f"  [{text}] -> {href}")

    return page


def explore_search(query="avatar"):
    print("\n" + "=" * 60)
    print(f"SEARCHING: ?s={query}")
    print("=" * 60)
    page = StealthyFetcher.fetch(
        f"https://comando.la/?s={query}",
        headless=True,
        real_chrome=True,
        network_idle=True,
        google_search=False,
    )
    print(f"Status: {page.status}, URL: {page.url}")
    title_el = page.css("title")
    print(f"Title: {title_el[0].text if title_el else 'N/A'}")
    print()

    body = page.body.decode('utf-8') if isinstance(page.body, bytes) else page.body
    with open("/tmp/comando_search_v4.html", "w", encoding="utf-8") as f:
        f.write(body)
    print(f"Saved {len(body)} chars")
    print()

    # Cards
    for sel in ["article", ".post", ".card", "li.post"]:
        items = page.css(sel)
        if items:
            print(f"Cards '{sel}': {len(items)}")
            for item in items[:3]:
                titles = item.css("h1, h2, h3")
                links = item.css("a")
                imgs = item.css("img")
                cats = item.css("[class*='cat'], [class*='type'], [class*='genre']")
                print(f"  --- Card ---")
                if titles:
                    print(f"  Title elem: {str(titles[0])[:200]}")
                if links:
                    print(f"  Link: {links[0].attrib.get('href', '')}")
                if imgs:
                    src = imgs[0].attrib.get('src', imgs[0].attrib.get('data-src', ''))
                    print(f"  Image: {src}")
                if cats:
                    print(f"  Category: {cats[0].text.strip()}")
                print()
            break

    print("--- RAW (first 3000 chars) ---")
    print(body[:3000])


def explore_detail(url):
    print("\n" + "=" * 60)
    print(f"DETAIL PAGE: {url}")
    print("=" * 60)
    page = StealthyFetcher.fetch(
        url,
        headless=True,
        real_chrome=True,
        network_idle=True,
        google_search=False,
    )
    print(f"Status: {page.status}, URL: {page.url}")
    body = page.body.decode('utf-8') if isinstance(page.body, bytes) else page.body
    with open("/tmp/comando_detail_v4.html", "w", encoding="utf-8") as f:
        f.write(body)
    print(f"Saved {len(body)} chars")
    print()

    # Title
    h1 = page.css("h1")
    print(f"H1: {h1[0].text.strip() if h1 else 'N/A'}")
    print()

    # Magnet links
    print("--- MAGNET LINKS ---")
    magnets = page.css("a[href^='magnet:']")
    print(f"Found {len(magnets)} magnet links")
    for m in magnets[:5]:
        print(f"  href (100 chars): {m.attrib.get('href', '')[:100]}")
        print(f"  title: {m.attrib.get('title', '')}")
        print(f"  text: {m.text.strip()[:50]}")
        print()

    # Quality labels
    print("--- QUALITY/LANGUAGE BUTTONS ---")
    for sel in [".botao_dublado", ".botao", "[class*='botao']", "[class*='quality']", "[class*='lang']"]:
        items = page.css(sel)
        if items:
            print(f"Selector '{sel}': {len(items)}")
            for item in items[:5]:
                print(f"  {str(item)[:200]}")
    print()

    # Entry content
    print("--- ENTRY CONTENT (first 1500 chars) ---")
    entry = page.css(".entry-content, .post-content, .content, article")
    if entry:
        print(str(entry[0])[:1500])

    print("\n--- RAW (last 2000 chars for magnet area) ---")
    print(body[-2000:])


if __name__ == "__main__":
    try:
        page = explore_homepage()
    except Exception as e:
        print(f"Homepage error: {e}")
        import traceback; traceback.print_exc()

    try:
        explore_search("avatar")
    except Exception as e:
        print(f"Search error: {e}")
        import traceback; traceback.print_exc()
