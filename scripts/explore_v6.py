"""
Exploration script for comando.la using patchright directly with system Chromium.
Run with: uv run --with scrapling --with patchright scripts/explore_v6.py
"""
import asyncio
from patchright.async_api import async_playwright


async def fetch_page(url, label=""):
    print(f"\n{'='*60}")
    print(f"FETCHING: {label or url}")
    print("="*60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="/usr/bin/chromium",
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            locale="pt-BR",
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()

        await page.goto(url, wait_until="networkidle", timeout=30000)
        # Wait a bit for any JS challenges
        await asyncio.sleep(3)

        title = await page.title()
        final_url = page.url
        print(f"Title: {title}")
        print(f"URL: {final_url}")

        # If still on Cloudflare challenge, wait more
        if "just a moment" in title.lower() or "cloudflare" in title.lower():
            print("Cloudflare challenge detected, waiting longer...")
            await asyncio.sleep(8)
            title = await page.title()
            print(f"Title after wait: {title}")

        html = await page.content()
        await browser.close()
        return html, title, final_url


def analyze_html(html, label, save_path):
    from bs4 import BeautifulSoup

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved {len(html)} chars to {save_path}")

    soup = BeautifulSoup(html, "html.parser")

    print(f"\n--- BODY STRUCTURE ---")
    body = soup.find("body")
    if body:
        for child in list(body.children)[:15]:
            if hasattr(child, 'name') and child.name:
                cls = child.get('class', [])
                id_ = child.get('id', '')
                print(f"  <{child.name} class='{' '.join(cls)}' id='{id_}'>")

    print(f"\n--- ALL LINKS (first 40) ---")
    for a in soup.find_all("a")[:40]:
        href = a.get('href', '')
        text = a.get_text(strip=True)[:50]
        print(f"  [{text}] -> {href}")

    print(f"\n--- NAVIGATION ---")
    for sel in [("nav", {}), ("div", {"id": "nav"}), ("div", {"class": "menu"}),
                ("ul", {"class": "menu"}), ("header", {})]:
        tag, attrs = sel
        found = soup.find(tag, attrs)
        if found:
            links = found.find_all("a")
            print(f"  <{tag} {attrs}>: {len(links)} links")
            for l in links[:15]:
                print(f"    [{l.get_text(strip=True)[:40]}] -> {l.get('href', '')}")
            break

    print(f"\n--- CONTENT CARDS ---")
    for sel in ["article", ("div", {"class": "post"}), ("li", {"class": "post"}),
                ("div", {"class": "card"}), ("div", {"class": "item"})]:
        if isinstance(sel, str):
            items = soup.find_all(sel)
        else:
            tag, attrs = sel
            items = soup.find_all(tag, attrs)
        if items:
            print(f"Found {len(items)} cards: {sel}")
            for item in items[:2]:
                # Title
                h = item.find(["h1", "h2", "h3"])
                a = item.find("a", href=True)
                img = item.find("img")
                cat = item.find(class_=lambda c: c and ('cat' in c or 'type' in c or 'genre' in c))
                if h:
                    print(f"  Title: {h.get_text(strip=True)[:80]}")
                if a:
                    print(f"  URL: {a.get('href', '')}")
                if img:
                    print(f"  Img: {img.get('src', img.get('data-src', ''))[:80]}")
                if cat:
                    print(f"  Category: {cat.get_text(strip=True)}")
                print()
            break

    print(f"\n--- PAGINATION ---")
    for cls_kw in ["paginat", "page-nav", "nav-links", "wp-pagenavi"]:
        pag = soup.find(class_=lambda c: c and cls_kw in ' '.join(c).lower())
        if pag:
            print(f"Pagination ({cls_kw}): {str(pag)[:300]}")
            break

    print(f"\n--- SEARCH FORM ---")
    form = soup.find("form")
    if form:
        print(f"  {str(form)[:300]}")
    inp = soup.find("input", {"type": "search"}) or soup.find("input", {"name": "s"})
    if inp:
        print(f"  Search input: {str(inp)[:200]}")

    print(f"\n--- MAGNET LINKS ---")
    magnets = soup.find_all("a", href=lambda x: x and x.startswith("magnet:"))
    print(f"Found {len(magnets)} magnet links")
    for m in magnets[:5]:
        print(f"  title: {m.get('title', '')}")
        print(f"  text: {m.get_text(strip=True)[:60]}")
        print(f"  href (120): {m.get('href', '')[:120]}")
        parent = m.parent
        if parent:
            print(f"  parent: <{parent.name} class='{parent.get('class', '')}'>")
        print()

    print(f"\n--- FIRST 3000 CHARS ---")
    print(html[:3000])


async def main():
    # Homepage
    try:
        html, title, url = await fetch_page("https://comando.la", "HOMEPAGE")
        analyze_html(html, "homepage", "/tmp/comando_home_v6.html")
    except Exception as e:
        print(f"Error: {e}")
        import traceback; traceback.print_exc()

    # Search
    try:
        html, title, url = await fetch_page("https://comando.la/?s=avatar", "SEARCH: avatar")
        analyze_html(html, "search", "/tmp/comando_search_v6.html")
    except Exception as e:
        print(f"Error: {e}")
        import traceback; traceback.print_exc()


asyncio.run(main())
