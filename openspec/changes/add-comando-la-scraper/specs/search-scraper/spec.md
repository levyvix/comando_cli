## MODIFIED Requirements

### Requirement: Primary Scraper uses StealthySession with Cloudflare Bypass
The system SHALL use `ComandoLaScraper` as the default scraper, fetching content from comando.la via `StealthySession(solve_cloudflare=True, headless=True)`.

#### Scenario: Successful search
- **WHEN** user runs `comando search <query>`
- **THEN** system opens a `StealthySession` with `solve_cloudflare=True`
- **AND** fetches `https://comando.la/?s=<query>`
- **AND** parses `article > header > h2 > a` elements for title and URL
- **AND** returns list of `Title` objects with `name`, `url`, `media_type`

#### Scenario: Cloudflare challenge solved transparently
- **WHEN** comando.la returns a Cloudflare challenge page
- **THEN** `StealthySession` with `solve_cloudflare=True` resolves it automatically
- **AND** the actual page content is returned to the parser

#### Scenario: Fetch fails after retries
- **WHEN** the page cannot be fetched after 3 attempts
- **THEN** system raises `ScraperError` with a clear message
- **AND** CLI shows the error to the user

### Requirement: Detail Page Metadata Extraction
The system SHALL parse the comando.la detail page to extract `Title` metadata including quality options and magnet links.

#### Scenario: Movie detail page
- **WHEN** user selects a movie result
- **THEN** system fetches the detail URL
- **AND** extracts title from `h1`
- **AND** extracts poster from `div.entry-content.cf img::attr(src)`
- **AND** extracts magnet links from `a[href^="magnet:"]`
- **AND** extracts quality/language labels from preceding `span.botao_dublado`
- **AND** returns a `Title` with populated `quality_options`

#### Scenario: Series detail page
- **WHEN** user selects a series result
- **THEN** system detects `media_type = SERIES` from URL path (`/series/`) or title keywords
- **AND** extracts episode numbers from `dn=` parameter in magnet URLs (`SxxExx` pattern)
- **AND** populates `episodes` list

### Requirement: Scraper Selection via Config
The system SHALL allow selecting the scraper source via `config.toml`.

#### Scenario: Default scraper is comando.la
- **WHEN** no `scraper` field is set in config
- **THEN** system uses `ComandoLaScraper`

#### Scenario: Fallback to gratistorrent
- **WHEN** config contains `scraper = "gratistorrent"`
- **THEN** system uses `GratistorrentScraper` instead
