"""
Exploration script for comando.la using real Chrome (as the existing scraper does).
Run with: uv run --with scrapling scripts/explore_v3.py
"""
import asyncio
from scrapling.fetchers import StealthyFetcher


async def explore():
    fetcher = StealthyFetcher()

    print("Fetching homepage with real Chrome + network_idle...")
    try:
        page = await fetcher.async_fetch(
            "https://comando.la",
            headless=True,
            network_idle=True,
            timeout=60000,
        )
        print(f"Status: {page.status}")
        print(f"URL: {page.url}")
        title_el = page.css("title")
        print(f"Title: {title_el[0].text if title_el else 'N/A'}")

        # Save full HTML
        html_content = page.body if hasattr(page, 'body') else str(page)
        with open("/tmp/comando_v3.html", "w") as f:
            f.write(html_content)
        print(f"HTML length: {len(html_content)} chars saved to /tmp/comando_v3.html")
        print()

        # Print body structure
        print("--- TOP-LEVEL BODY CHILDREN ---")
        for child in page.css("body > *")[:10]:
            cls = child.attrib.get('class', '')[:60]
            id_ = child.attrib.get('id', '')
            print(f"  <{child.tag} class='{cls}' id='{id_}'>")
        print()

        # Find all links
        print("--- ALL LINKS (first 30) ---")
        for a in page.css("a")[:30]:
            href = a.attrib.get('href', '')
            text = a.text.strip()[:50]
            print(f"  [{text}] -> {href}")
        print()

        # Search for article/post cards
        print("--- ARTICLE/CARD ELEMENTS ---")
        for sel in ["article", ".post", ".card", ".item", "li[class*='post']", "div[class*='post']"]:
            items = page.css(sel)
            if items:
                print(f"Selector '{sel}': {len(items)} items")
                print(f"  First: {str(items[0])[:400]}")
                print()

        # Search for images
        print("--- IMAGES (first 10) ---")
        for img in page.css("img")[:10]:
            src = img.attrib.get('src', img.attrib.get('data-src', ''))
            alt = img.attrib.get('alt', '')
            print(f"  src={src[:80]} alt={alt[:50]}")

        print()
        print("--- FIRST 3000 CHARS OF BODY ---")
        print(html_content[:3000])

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


async def explore_search():
    fetcher = StealthyFetcher()
    print("\n" + "="*60)
    print("TESTING SEARCH: /?s=avatar")
    print("="*60)
    try:
        page = await fetcher.async_fetch(
            "https://comando.la/?s=avatar",
            headless=True,
            network_idle=True,
            timeout=60000,
        )
        print(f"Status: {page.status}, URL: {page.url}")
        html = page.body if hasattr(page, 'body') else str(page)
        with open("/tmp/comando_search.html", "w") as f:
            f.write(html)
        print(f"HTML saved ({len(html)} chars)")
        print()

        title_el = page.css("title")
        print(f"Title: {title_el[0].text if title_el else 'N/A'}")
        print()

        # Cards
        for sel in ["article", ".post", ".card", ".item", "[class*='post']"]:
            items = page.css(sel)
            if items:
                print(f"Cards ({sel}): {len(items)}")
                for item in items[:3]:
                    titles = item.css("h1, h2, h3, h4")
                    links = item.css("a")
                    imgs = item.css("img")
                    if titles:
                        print(f"  Title: {titles[0].text.strip()}")
                    if links:
                        print(f"  URL: {links[0].attrib.get('href', '')}")
                    if imgs:
                        print(f"  Img: {imgs[0].attrib.get('src', imgs[0].attrib.get('data-src', ''))}")
                    print()
                break

        print("--- RAW (first 2000 chars) ---")
        print(html[:2000])

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    await explore()
    await explore_search()

asyncio.run(main())
