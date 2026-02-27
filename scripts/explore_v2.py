"""
Exploration script for comando.la - using StealthyFetcher with browser mode.
Run with: uv run --with scrapling scripts/explore_v2.py
"""
import asyncio
from scrapling.fetchers import StealthyFetcher


async def explore():
    # Use StealthyFetcher with headless browser to bypass Cloudflare
    fetcher = StealthyFetcher()

    print("Fetching homepage...")
    try:
        page = await fetcher.async_fetch(
            "https://comando.la",
            headless=True,
            network_idle=True,
            timeout=60000,
        )
        print(f"Status: {page.status}")
        print(f"URL: {page.url}")
        print(f"Title: {page.css('title')[0].text if page.css('title') else 'N/A'}")
        print()

        # Save HTML for inspection
        with open("/tmp/comando_homepage.html", "w") as f:
            f.write(str(page.html_content) if hasattr(page, 'html_content') else page.body)
        print("HTML saved to /tmp/comando_homepage.html")
        print()

        # Body structure
        print("--- BODY STRUCTURE ---")
        body_children = page.css("body > *")
        for child in body_children[:20]:
            cls = child.attrib.get('class', '')[:50]
            id_ = child.attrib.get('id', '')
            print(f"  <{child.tag} class='{cls}' id='{id_}'>")
        print()

        # Nav links
        print("--- NAV/MENU LINKS ---")
        for sel in ["nav a", "header a", ".menu a", ".navbar a", ".nav a", "#menu a"]:
            links = page.css(sel)
            if links:
                print(f"Selector '{sel}': {len(links)} links")
                for l in links[:15]:
                    print(f"  [{l.text.strip()}] -> {l.attrib.get('href', '')}")
                break
        print()

        # Content cards
        print("--- CONTENT CARDS ---")
        card_selectors = [
            "article",
            ".post",
            ".card",
            ".item",
            ".entry",
            "[class*='post-']",
            "[class*='card-']",
            ".movie-item",
            ".serie-item",
        ]
        for sel in card_selectors:
            items = page.css(sel)
            if items:
                print(f"Selector '{sel}': {len(items)} items")
                first = items[0]
                print(f"  First item class: {first.attrib.get('class', '')}")
                print(f"  First item HTML:\n{str(first)[:500]}")
                print()

        # Search
        print("--- SEARCH FORM ---")
        for sel in ["form", "input[type='search']", "input[type='text']", "input[name='s']"]:
            items = page.css(sel)
            if items:
                print(f"Selector '{sel}': {len(items)} items")
                for item in items[:2]:
                    print(f"  {str(item)[:300]}")

        # Print full raw body text (first 3000 chars)
        print("\n--- RAW HTML BODY (first 5000 chars) ---")
        body = page.css("body")
        if body:
            print(str(body[0])[:5000])

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


asyncio.run(explore())
