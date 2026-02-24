# Gratistorrent.com Site Analysis

## Key Findings

### Scrapling Fetcher Usage
- Use `html_content` attribute to get parsed HTML (not `text` which is empty)
- Scrapling Response object has: `html_content` (parsed), `body` (raw bytes)
- The site loads successfully with status 200

### Site Structure
- Homepage: https://gratistorrent.com/
- Search: appears to be `/search?q=query` format (not `/?s=query`)
- Title/Series pages: /filme/ or /series/ paths
- The HTML is fully rendered by Scrapling

## HTML Structure Found

### Homepage & Search Results Structure
- Content items: `<div class="capa_lista">`
- Title: `<h3>` inside `<div class="dados_capa">`
- Link to detail page: Full absolute URL in `<a href="...">`
- Quality: `<span class="capa_qualidade">` (e.g., "HD")
- Category: `<span class="capa_categoria">` (e.g., "Filme")
- Language: `<span class="capa_idioma">` (e.g., "Dual Áudio")
- Rating: `<span class="capa_imdb">` (e.g., "Imdb: 5.7")

### Search Form
- Method: GET
- Action: index.php
- Parameter: `s` (not `q`)
- Endpoint: Root URL `https://gratistorrent.com/?s=QUERY`

### Detail Page Structure
- Title: `<h1>` tag
- Downloads section: `<h2 id="linksdownload">` 
- Download options grouped in `<p id="lista_download">`
- Quality/Language info in preceding `<span class="botao_dublado">`
- Magnet links: `<a href="magnet:...">DOWNLOAD</a>`
- All info also in magnet link title attribute

Pattern:
```
<span class="botao_dublado">DESCRIPTION (has quality/language info)</span>
<a href="magnet:...">DOWNLOAD</a>
```

Quality indicators in title: "1080p", "720p", "480p", "HDTV", "BluRay"
Language: "Portuguese", "English", "Dublado", "Legendado"

## Next Steps
1. Update scraper.py to use `html_content` instead of `text`
2. Study actual HTML structure with BeautifulSoup to refine CSS selectors
3. Test search and detail page parsing
