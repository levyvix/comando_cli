# Change: Add Scraper Plugin for comando.la

## Why
comando.la é a fonte primária de conteúdo para a CLI. Possui catálogo mais atualizado que gratistorrent.com e deve ter prioridade máxima. O site usa Cloudflare, portanto requer `StealthySession` com `solve_cloudflare=True` (diferente do `Fetcher` usado no scraper atual). O autor já tem um scraper funcional para o site (https://github.com/levyvix/scraper-filmes) que valida a abordagem técnica.

## What Changes
- **NEW**: `ComandoLaScraper` em `src/comando_cli/scraper.py` usando `StealthySession(solve_cloudflare=True)`
- **MODIFIED**: `cli.py` usa `ComandoLaScraper` como scraper padrão
- **MODIFIED**: `GratistorrentScraper` fica disponível como fallback via config `scraper = "gratistorrent"`
- **MODIFIED**: `config.py` expõe campo `scraper` para selecionar a fonte

## Impact
- **Affected specs**: `search` (change `add-streaming-cli`)
- **Affected code**: `scraper.py`, `cli.py`, `config.py`
- **External dependencies**: Scrapling `StealthySession` + `camoufox` (já presentes como dependências)
- **Breaking changes**: Nenhum — mesma interface pública (`search()` / `fetch_metadata()`)

## Architecture Highlights

### Fetcher
`StealthySession` (síncrona, sessão persistente) com `solve_cloudflare=True` e `headless=True`.
Padrão do scraper de referência: abre sessão camoufox uma única vez, reutiliza para múltiplas requisições na mesma execução — evita overhead de inicialização por chamada.

### DOM Structure (comando.la)
Baseado no scraper de referência + estrutura WordPress típica:

**Listagem / busca** (`https://comando.la/?s=<query>`):
- Cards: `article > header > h2 > a` → href (URL detalhe) e texto (título)
- Categoria: inferida da URL (`/filmes/` → movie, `/series/` → series)

**Página de detalhe**:
- Metadados (título, qualidade, idioma etc.): `div.entry-content.cf > p:nth-child(3)::text`
- Sinopse: `div.entry-content.cf > p:nth-child(4)::text`
- Poster: `div.entry-content.cf img::attr(src)`
- Magnet links: `a[href^="magnet:"]`
- Qualidade/idioma: `span.botao_dublado` precedendo cada magnet link (mesmo padrão gratistorrent)

### Interface (duck typing com GratistorrentScraper)
```python
class ComandoLaScraper:
    def search(self, query: str) -> list[Title]: ...
    def fetch_metadata(self, title_url: str) -> Title | None: ...
```
