"""
Fetch detail pages of movies/series from Wayback Machine.
Run with: uv run --with beautifulsoup4 --with requests scripts/explore_detail2.py
"""
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
}

def fetch(url):
    print(f"Fetching: {url}")
    resp = requests.get(url, headers=HEADERS, timeout=30)
    print(f"Status: {resp.status_code}")
    return resp.text


def find_available_snapshot(path):
    """Find an available snapshot for a URL."""
    import json
    cdx_url = f"http://web.archive.org/cdx/search/cdx?url={path}&output=json&limit=5&fl=timestamp,statuscode&from=20230101&to=20241231&filter=statuscode:200"
    try:
        resp = requests.get(cdx_url, headers=HEADERS, timeout=15)
        data = json.loads(resp.text)
        if len(data) > 1:
            for row in data[1:]:
                ts, status = row
                if status == '200':
                    return ts
    except:
        pass
    return None


def analyze_detail(html, label, save_path):
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(html)

    soup = BeautifulSoup(html, "html.parser")
    print(f"\n{'='*60}")
    print(f"DETAIL PAGE: {label}")
    print("="*60)

    h1 = soup.find("h1")
    print(f"H1: {h1.get_text(strip=True) if h1 else 'N/A'}")

    # Entry content
    entry = soup.find(class_="entry-content")
    if not entry:
        entry = soup.find(class_="post-content")
    if not entry:
        entry = soup.find("article")

    if not entry:
        print("No entry content found")
        print("Body snippet:", str(soup.find("body"))[:500] if soup.find("body") else "no body")
        return

    # Images
    print("\n--- IMAGES ---")
    for img in entry.find_all("img")[:5]:
        src = img.get('src', img.get('data-src', img.get('data-lazy-src', '')))
        alt = img.get('alt', '')
        cls = ' '.join(img.get('class', []))
        print(f"  src: {src[:80]}, alt: {alt[:40]}, class: {cls}")

    # Magnet links
    print("\n--- MAGNET LINKS ---")
    magnets = soup.find_all("a", href=lambda x: x and x.startswith("magnet:"))
    print(f"Total: {len(magnets)}")
    for i, m in enumerate(magnets[:10]):
        href = m.get('href', '')
        title = m.get('title', '')
        cls = ' '.join(m.get('class', []))
        text = m.get_text(strip=True)

        print(f"\n  Magnet #{i+1}:")
        print(f"    text: '{text[:60]}'")
        print(f"    title: '{title[:80]}'")
        print(f"    class: '{cls}'")
        print(f"    href (180): {href[:180]}")

        # Context: parent
        parent = m.parent
        if parent:
            print(f"    parent: <{parent.name} class='{' '.join(parent.get('class', []))}'>")
            # Siblings
            prev_sib = m.find_previous_sibling()
            if prev_sib:
                print(f"    prev sibling: <{prev_sib.name if hasattr(prev_sib, 'name') else 'text'}>: {str(prev_sib)[:80]}")
            # Look for nearby span with quality/language info
            nearby_span = m.find_previous("span")
            if nearby_span:
                print(f"    prev span: <span class='{' '.join(nearby_span.get('class', []))}'>: {nearby_span.get_text(strip=True)[:60]}")
        gp = parent.parent if parent else None
        if gp:
            print(f"    grandparent: <{gp.name} class='{' '.join(gp.get('class', []))}'>")
            gp_text = gp.get_text(separator=' ', strip=True)[:100]
            print(f"    grandparent text: {gp_text}")

    # Quality labels
    print("\n--- QUALITY/LANGUAGE ELEMENTS ---")
    for sel in [".botao_dublado", "[class*=botao]", "[class*=quality]",
                "span[class*=dub]", "span[class*=leg]", "p strong"]:
        items = entry.select(sel)
        if items:
            print(f"\n  '{sel}': {len(items)}")
            for item in items[:5]:
                print(f"    {str(item)[:200]}")

    # Show full entry content
    print("\n--- ENTRY CONTENT HTML (first 3000 chars) ---")
    print(str(entry)[:3000])

    print("\n--- ENTRY CONTENT HTML (last 2000 chars) ---")
    entry_str = str(entry)
    print(entry_str[-2000:])


# Find a specific movie page that has a 200 snapshot
print("Finding snapshots...")
urls_to_try = [
    "https://comando.la/todo-o-silencio-torrent-2023-dual-audio-dublado-web-dl-1080p/",
    "https://comando.la/the-big-cigar-a-fuga-1a-temporada-torrent-2024-dual-audio-5-1-dublado-web-dl-720p-1080p-2160p-4k-download/",
    "https://comando.la/o-veu-1a-temporada-torrent-2024-dual-audio-web-dl-1080p/",
    "https://comando.la/young-sheldon-7a-temporada-torrent-2024-dual-audio-5-1-dublado-web-dl-720p-1080p-2160p-4k-download/",
]

for target_url in urls_to_try[:2]:
    ts = find_available_snapshot(target_url)
    if ts:
        print(f"Found snapshot {ts} for {target_url}")
        wayback_url = f"https://web.archive.org/web/{ts}/{target_url}"
        try:
            html = fetch(wayback_url)
            if len(html) > 10000:
                label = target_url.split('/')[-2][:30]
                save_path = f"/tmp/detail_{label}.html"
                analyze_detail(html, label, save_path)
                break
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"No snapshot found for {target_url}")

# Also try direct search page
try:
    ts = find_available_snapshot("https://comando.la/?s=avatar")
    if ts:
        print(f"\nSearch snapshot: {ts}")
        html = fetch(f"https://web.archive.org/web/{ts}/https://comando.la/?s=avatar")
        if len(html) > 10000:
            analyze_detail(html, "Search Results: avatar", "/tmp/search_avatar.html")
except Exception as e:
    print(f"Search error: {e}")
