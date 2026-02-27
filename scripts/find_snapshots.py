"""
Find available Wayback Machine snapshots for comando.la pages.
Run with: uv run --with requests scripts/find_snapshots.py
"""
import requests
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
}


def find_snapshots(url, limit=10):
    cdx_url = (
        f"http://web.archive.org/cdx/search/cdx"
        f"?url={url}&output=json&limit={limit}"
        f"&fl=timestamp,statuscode,original"
        f"&from=20220101"
    )
    resp = requests.get(cdx_url, headers=HEADERS, timeout=30)
    print(f"CDX status: {resp.status_code}")
    try:
        data = json.loads(resp.text)
        return data[1:] if len(data) > 1 else []
    except:
        print(f"Parse error: {resp.text[:200]}")
        return []


# Find snapshots for movie detail pages
test_urls = [
    "https://comando.la/*torrent*1080p*",  # Wildcard for any movie
    "https://comando.la/avatar*",
    "https://comando.la/*temporada*",
    "https://comando.la/",
]

for url in test_urls:
    print(f"\nSearching snapshots for: {url}")
    snaps = find_snapshots(url, limit=5)
    for snap in snaps[:5]:
        print(f"  {snap}")
