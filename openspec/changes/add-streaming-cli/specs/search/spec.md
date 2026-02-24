## ADDED Requirements

### Requirement: Cloudflare-Protected Website Scraping
The system SHALL fetch content from gratistorrent.com using Scrapling's StealthyFetcher with Cloudflare challenge solving enabled.

#### Scenario: Scrape search results
- **WHEN** user initiates search with `comando search <query>`
- **THEN** system fetches search results from gratistorrent.com via StealthyFetcher
- **AND** extracts title, URL, media_type (movie/series), and thumbnail from HTML
- **AND** returns list of matches to user

#### Scenario: Handle Cloudflare blocks
- **WHEN** Cloudflare returns 403/429
- **THEN** system retries with exponential backoff (max 3 attempts)
- **AND** shows spinner during retry
- **AND** fails with clear error message if all retries exhausted

### Requirement: Title Search with Fuzzy Selection
The system SHALL provide interactive title search using fzf for user selection.

#### Scenario: Search and select
- **WHEN** user runs `comando search demolidor`
- **THEN** system queries gratistorrent.com
- **AND** displays results in fzf (formatted as "Title [Movie/Series]")
- **AND** returns selected title with its metadata (URL, type)

#### Scenario: Empty search results
- **WHEN** user searches for non-existent title
- **THEN** system shows "No results found for: <query>"
- **AND** prompts user to try different search term

### Requirement: Content Metadata Extraction
The system SHALL fetch and extract detailed metadata for selected titles.

#### Scenario: Fetch series metadata
- **WHEN** user selects series title
- **THEN** system fetches title page from gratistorrent.com
- **AND** extracts episode count, seasons, available qualities, available languages, synopsis
- **AND** returns structured metadata object

#### Scenario: Fetch movie metadata
- **WHEN** user selects movie title
- **THEN** system fetches title page
- **AND** extracts available qualities, available languages, synopsis, release date
- **AND** returns metadata object (episodes field null)

### Requirement: Cached Metadata
The system SHALL cache scraped metadata locally to reduce API load.

#### Scenario: Cache metadata
- **WHEN** title metadata is fetched successfully
- **THEN** system stores result in SQLite cache with timestamp
- **AND** subsequent requests for same title use cached data if <1 hour old
- **AND** allow cache refresh with --refresh flag

#### Scenario: Stale cache
- **WHEN** cached metadata is >1 hour old
- **THEN** system refetches from website
- **AND** updates cache with new data
