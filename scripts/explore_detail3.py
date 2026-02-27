"""
Fetch movie detail pages from Wayback Machine - using HTTPS.
Run with: uv run --with beautifulsoup4 --with requests scripts/explore_detail3.py
"""
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
}


def fetch(url, timeout=30):
    print(f"Fetching: {url[:100]}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        print(f"  Status: {resp.status_code}, Size: {len(resp.text)}")
        return resp.text
    except Exception as e:
        print(f"  Error: {e}")
        return None


def analyze_detail(html, label, save_path):
    if not html:
        return
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Saved to {save_path}")

    soup = BeautifulSoup(html, "html.parser")

    h1 = soup.find("h1")
    print(f"\n  H1: {h1.get_text(strip=True)[:80] if h1 else 'N/A'}")

    # Check if it's a Wayback Machine page or actual content
    title = soup.find("title")
    if title:
        print(f"  Title: {title.get_text()[:80]}")

    if "Wayback Machine" in (title.get_text() if title else ""):
        print("  -> Got Wayback Machine index page, not actual content")
        return

    entry = (soup.find(class_="entry-content") or
             soup.find(class_="post-content") or
             soup.find(class_="content-area"))

    if not entry:
        # Try finding by article
        article = soup.find("article")
        if article:
            entry = article
        else:
            print("  No entry-content found!")
            print("  Body snippet:", str(soup.find("body"))[:300] if soup.find("body") else "no body")
            return

    print(f"\n  Entry content length: {len(str(entry))}")

    # Find magnet links
    magnets = soup.find_all("a", href=lambda x: x and x.startswith("magnet:"))
    print(f"\n  MAGNET LINKS: {len(magnets)}")
    for i, m in enumerate(magnets[:8]):
        href = m.get('href', '')
        title_attr = m.get('title', '')
        cls = ' '.join(m.get('class', []))
        text = m.get_text(strip=True)

        print(f"\n    [{i+1}] text='{text[:50]}' title='{title_attr[:60]}'")
        print(f"        class='{cls}'")
        print(f"        href={href[:160]}")

        # Navigate context
        parent = m.parent
        if parent:
            print(f"        parent=<{parent.name} class='{' '.join(parent.get('class', []))}'> text='{parent.get_text(strip=True)[:60]}'")
            gp = parent.parent
            if gp:
                print(f"        grandparent=<{gp.name} class='{' '.join(gp.get('class', []))}'> text='{gp.get_text(strip=True)[:80]}'")

        # Look for preceding span with language/quality info
        prev_span = m.find_previous("span")
        if prev_span:
            print(f"        prev_span=<span class='{' '.join(prev_span.get('class', []))}'>: '{prev_span.get_text(strip=True)[:50]}'")

        # Check nearby text nodes
        prev_elements = []
        current = m
        for _ in range(5):
            current = current.find_previous()
            if current:
                name = getattr(current, 'name', 'text')
                text_content = getattr(current, 'get_text', lambda s: str(current))(strip=True)
                prev_elements.append(f"<{name}>: {str(text_content)[:40]}")
            else:
                break
        if prev_elements:
            print(f"        prev elements: {prev_elements}")

    # All spans near magnets
    print(f"\n  BOTAO SPANS:")
    botaos = soup.find_all("span", class_="botao_dublado")
    if not botaos:
        botaos = soup.find_all(class_=lambda c: c and "botao" in ' '.join(c if isinstance(c, list) else [c]).lower())
    print(f"    Found {len(botaos)} botao spans")
    for span in botaos[:5]:
        print(f"    <span class='{' '.join(span.get('class', []))}'>: '{span.get_text(strip=True)}'")
        next_a = span.find_next("a")
        if next_a and next_a.get('href', '').startswith("magnet:"):
            print(f"      -> next magnet: {next_a.get('href', '')[:100]}")

    # Full entry content HTML
    print(f"\n  FULL ENTRY CONTENT HTML (first 4000 chars):")
    entry_str = str(entry)
    print(entry_str[:4000])

    print(f"\n  FULL ENTRY CONTENT HTML (last 2000 chars):")
    print(entry_str[-2000:])


# Use known archive snapshots from the filmes listing page we already got
# The listing page had timestamp 20240617125042 in the URLs
# Let's try direct movie URLs from that listing

movie_urls = [
    # These are the exact URLs from the listing
    ("https://web.archive.org/web/20240617125042/https://comando.la/todo-o-silencio-torrent-2023-dual-audio-dublado-web-dl-1080p/", "Todo o Silencio"),
    ("https://web.archive.org/web/20240617125042/https://comando.la/the-retreat-torrent-2021-dublado-dual-audio-5-1-legendado-web-dl-1080p-download-4k-hd/", "Lutar ou Morrer"),
]

series_urls = [
    ("https://web.archive.org/web/20240520230952/https://comando.la/o-veu-1a-temporada-torrent-2024-dual-audio-web-dl-1080p/", "O Veu S1"),
    ("https://web.archive.org/web/20240520230952/https://comando.la/young-sheldon-7a-temporada-torrent-2024-dual-audio-5-1-dublado-web-dl-720p-1080p-2160p-4k-download/", "Young Sheldon S7"),
]

print("=== MOVIE DETAIL PAGES ===")
for url, label in movie_urls[:2]:
    html = fetch(url)
    analyze_detail(html, label, f"/tmp/detail_{label.replace(' ', '_')}.html")

print("\n=== SERIES DETAIL PAGES ===")
for url, label in series_urls[:2]:
    html = fetch(url)
    analyze_detail(html, label, f"/tmp/detail_{label.replace(' ', '_')}.html")
