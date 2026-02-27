"""
Exploration script for comando.la website structure.
Run with: uv run --with scrapling scripts/explore_comandola.py
"""
import asyncio
from scrapling import StealthyFetcher


async def explore_homepage():
    fetcher = StealthyFetcher(auto_match=False)
    print("=" * 60)
    print("FETCHING HOMEPAGE: https://comando.la")
    print("=" * 60)
    page = await fetcher.async_fetch("https://comando.la")
    print(f"Status: {page.status}")
    print(f"URL: {page.url}")
    print()

    # Print page title
    title = page.css("title")
    print(f"Page title: {title[0].text if title else 'N/A'}")
    print()

    # Find main navigation links
    print("--- NAVIGATION LINKS ---")
    nav_links = page.css("nav a, .nav a, #nav a, header a, .menu a, .navbar a")
    for link in nav_links[:20]:
        print(f"  [{link.text.strip()}] -> {link.attrib.get('href', '')}")
    print()

    # Find category/menu links
    print("--- ALL HEADER/MENU LINKS ---")
    header = page.css("header")
    if header:
        links = header[0].css("a")
        for link in links[:30]:
            print(f"  [{link.text.strip()}] -> {link.attrib.get('href', '')}")
    print()

    # Find main content area - article cards
    print("--- ARTICLE/POST CARDS ---")
    # Try various selectors
    selectors = [
        "article",
        ".post",
        ".card",
        ".item",
        ".movie",
        ".serie",
        ".entry",
        "[class*='post']",
        "[class*='card']",
        "[class*='item']",
    ]
    for sel in selectors:
        items = page.css(sel)
        if items:
            print(f"  Selector '{sel}': found {len(items)} items")
            if items:
                first = items[0]
                print(f"    First item classes: {first.attrib.get('class', '')}")
                print(f"    First item HTML (200 chars): {str(first)[:200]}")
    print()

    # Find all anchor tags with images (likely movie/show cards)
    print("--- LINKS WITH IMAGES (likely content cards) ---")
    links_with_img = page.css("a img")
    print(f"Found {len(links_with_img)} links with images")
    seen = set()
    for img in links_with_img[:10]:
        parent_a = img.parent
        while parent_a and parent_a.tag != "a":
            parent_a = parent_a.parent
        if parent_a and parent_a.tag == "a":
            href = parent_a.attrib.get("href", "")
            if href not in seen:
                seen.add(href)
                title_el = img.attrib.get("alt", "") or img.attrib.get("title", "")
                print(f"  Title: {title_el}")
                print(f"  URL: {href}")
                print(f"  Img src: {img.attrib.get('src', img.attrib.get('data-src', ''))}")
                print()
    print()

    # Look for pagination
    print("--- PAGINATION ---")
    pagination_sels = [
        ".pagination",
        ".paginacion",
        ".pages",
        ".nav-links",
        "[class*='page']",
        ".next",
        ".prev",
    ]
    for sel in pagination_sels:
        items = page.css(sel)
        if items:
            print(f"  Found pagination with selector '{sel}': {len(items)} elements")
            for item in items[:3]:
                print(f"    {str(item)[:300]}")
    print()

    # Look for search form
    print("--- SEARCH FORM ---")
    search_sels = [
        "form[action*='search']",
        "form[method='get']",
        "form[role='search']",
        "input[type='search']",
        "input[name='s']",
        "input[name='q']",
        "input[placeholder*='earch']",
        "input[placeholder*='usca']",
        ".search",
        "#search",
    ]
    for sel in search_sels:
        items = page.css(sel)
        if items:
            print(f"  Found with '{sel}': {str(items[0])[:200]}")
    print()

    # Print body structure overview
    print("--- BODY STRUCTURE (main sections) ---")
    body_children = page.css("body > *")
    for child in body_children:
        print(f"  <{child.tag} class='{child.attrib.get('class', '')}' id='{child.attrib.get('id', '')}'>")
    print()

    # Print raw HTML snippet of main content
    print("--- MAIN CONTENT AREA HTML ---")
    main_sels = ["main", "#main", ".main", "#content", ".content", "#primary", ".primary", "article"]
    for sel in main_sels:
        items = page.css(sel)
        if items:
            print(f"Selector '{sel}' -> {len(items)} items")
            print(str(items[0])[:1000])
            print()
            break

    return page


async def explore_movie_listing():
    fetcher = StealthyFetcher(auto_match=False)
    print("\n" + "=" * 60)
    print("FETCHING MOVIES/SERIES LISTING PAGE")
    print("=" * 60)

    # Try common listing URLs
    test_urls = [
        "https://comando.la/peliculas/",
        "https://comando.la/series/",
        "https://comando.la/category/peliculas/",
        "https://comando.la/category/series/",
        "https://comando.la/?cat=peliculas",
    ]

    for url in test_urls:
        print(f"\nTrying: {url}")
        try:
            page = await fetcher.async_fetch(url)
            print(f"Status: {page.status} | Final URL: {page.url}")
            if page.status == 200:
                title = page.css("title")
                print(f"Title: {title[0].text if title else 'N/A'}")

                # Check for content cards
                for sel in ["article", ".post", ".card", ".item", "[class*='post']"]:
                    items = page.css(sel)
                    if items:
                        print(f"  Cards ({sel}): {len(items)}")
                        break
                break
        except Exception as e:
            print(f"  Error: {e}")


async def explore_search():
    fetcher = StealthyFetcher(auto_match=False)
    print("\n" + "=" * 60)
    print("TESTING SEARCH FUNCTIONALITY")
    print("=" * 60)

    test_urls = [
        "https://comando.la/?s=avatar",
        "https://comando.la/search?q=avatar",
        "https://comando.la/?search=avatar",
        "https://comando.la/buscar?q=avatar",
    ]

    for url in test_urls:
        print(f"\nTrying: {url}")
        try:
            page = await fetcher.async_fetch(url)
            print(f"Status: {page.status} | Final URL: {page.url}")
            if page.status == 200:
                title = page.css("title")
                print(f"Title: {title[0].text if title else 'N/A'}")

                # Look for results
                for sel in ["article", ".post", ".card", ".item", ".result", "[class*='post']"]:
                    items = page.css(sel)
                    if items:
                        print(f"  Results ({sel}): {len(items)}")
                        if items:
                            first = items[0]
                            # Get title from first result
                            title_el = first.css("h2, h3, h1, .title, [class*='title']")
                            if title_el:
                                print(f"  First result title: {title_el[0].text.strip()}")
                            link_el = first.css("a")
                            if link_el:
                                print(f"  First result URL: {link_el[0].attrib.get('href', '')}")
                        break
        except Exception as e:
            print(f"  Error: {e}")


async def main():
    homepage = await explore_homepage()
    await explore_movie_listing()
    await explore_search()


asyncio.run(main())
