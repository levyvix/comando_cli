# Tasks: add-comando-la-scraper

## Phase 1: ComandoLaScraper

- [x] Implementar `ComandoLaScraper` em `scraper.py` com `StealthyFetcher.fetch(solve_cloudflare=True, headless=True)`
  - `search(query) -> list[Title]`: GET `https://comando.la/?s=<query>`, parsear `article > header > h2 > a`
  - `fetch_metadata(url) -> Title | None`: parsear detail page (h1, poster, magnet links, botao_dublado)
  - Detecção de `media_type`: URL path `/series/` ou keywords no título (temporada, season)
  - Extração de episódio: `dn=` param em magnet URL → regex `SxxExx`
  - Retry: 3 tentativas com backoff (reusar padrão existente ou tenacity)

## Phase 2: Integração

- [x] Adicionar campo `scraper: str = "comando_la"` em `Config` (`config.py`)
- [x] Atualizar `cli.py`: instanciar scraper conforme `config.scraper` (`"comando_la"` → `ComandoLaScraper`, `"gratistorrent"` → `GratistorrentScraper`)
- [x] Atualizar `config_template.toml` com o novo campo

## Phase 3: Testes

- [x] Testes unitários para `_parse_search_results` e `_parse_title_page` do `ComandoLaScraper` (HTML fixture)
- [x] Teste de seleção de scraper via config
- [x] Verificar cobertura ≥ 80% nos módulos alterados (84% total, 92% scraper, 100% config)
