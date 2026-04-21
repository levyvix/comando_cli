"""Web scrapers for torrent sites using Scrapling."""

import hashlib
import json
import logging
import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Any
from typing import Optional, Pattern
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from scrapling import Fetcher

from comando_cli.config import ensure_directories
from comando_cli.models import Episode, MediaType, QualityOption, Title

logger = logging.getLogger(__name__)
_CACHE_TTL_SECONDS = 3600


class _TorrentResultsCache:
    """Simple file-based JSON cache with TTL."""

    def __init__(self, namespace: str, ttl_seconds: int = _CACHE_TTL_SECONDS):
        base_cache_dir = ensure_directories().cache_dir / "torrent-results"
        self.cache_dir = base_cache_dir / namespace
        self.ttl_seconds = ttl_seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.json"

    def get(self, key: str) -> tuple[bool, Any]:
        if os.environ.get("PYTEST_CURRENT_TEST"):
            return False, None

        path = self._cache_path(key)
        if not path.exists():
            return False, None

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            cached_at = float(payload.get("cached_at", 0))
            age = time.time() - cached_at
            if age > self.ttl_seconds:
                path.unlink(missing_ok=True)
                return False, None
            return True, payload.get("value")
        except Exception:
            path.unlink(missing_ok=True)
            return False, None

    def set(self, key: str, value: Any) -> None:
        if os.environ.get("PYTEST_CURRENT_TEST"):
            return

        path = self._cache_path(key)
        payload = {"cached_at": time.time(), "value": value}
        try:
            path.write_text(json.dumps(payload), encoding="utf-8")
        except Exception:
            logger.debug("Failed to write cache file: %s", path, exc_info=True)


def _normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.upper()


def _classify_language(context_text: str) -> str:
    normalized = _normalize_text(context_text)
    if "DUAL" in normalized:
        return "Dual Audio"
    if "DUBLADO" in normalized or ".DUB." in normalized:
        return "Dublado"
    if "LEGENDADO" in normalized or ".LEG." in normalized:
        return "Legendado"
    if "PORTUGUESE" in normalized or "PORTUGUES" in normalized:
        return "Portuguese"
    if "ENGLISH" in normalized or "INGLES" in normalized:
        return "English"
    return "Unknown"


def _parse_quality_options(html: str) -> list[QualityOption]:
    """Extract quality and language options from magnet links.

    Used by GratistorrentScraper. ComandoLaScraper has its own implementation.
    """
    from urllib.parse import unquote

    soup = BeautifulSoup(html, "html.parser")
    options = []

    magnet_pattern: Pattern[str] = re.compile(r"^magnet:")
    magnet_links = soup.find_all("a", href=magnet_pattern)

    for link in magnet_links:
        magnet_url: str = str(link.get("href", ""))
        if not magnet_url:
            continue

        title_attr = str(link.get("title", ""))
        prev_span = link.find_previous("span", class_="botao_dublado")
        text_before = prev_span.text.strip() if prev_span else ""

        full_text = _normalize_text(text_before + " " + title_attr)

        quality = "Unknown"
        for pattern in [
            "1080P",
            "720P",
            "480P",
            "4K",
            "HDTV",
            "BLURAY",
            "DVDRIP",
            "MKV",
        ]:
            if pattern in full_text:
                quality = pattern
                break

        # Prefer link title metadata for language detection.
        # On gratistorrent some legendado links can be under a stale previous
        # span from the dual section, so mixing both sources may misclassify.
        title_language = _classify_language(title_attr)
        if title_language != "Unknown":
            language = title_language
        else:
            language = _classify_language(full_text)

        episode = None
        dn_match = re.search(r"dn=([^&]+)", magnet_url)
        if dn_match:
            filename = unquote(dn_match.group(1))
            ep_match = re.search(r"[Ss](\d{1,2})[Ee](\d{1,2})", filename)
            if ep_match:
                episode = int(ep_match.group(2))

        options.append(
            QualityOption(
                quality=quality,
                language=language,
                magnet_link=magnet_url,
                display_name=title_attr or text_before or None,
                episode=episode,
            )
        )

    return options


class GratistorrentScraper:
    """Scraper for gratistorrent.com content."""

    BASE_URL = "https://gratistorrent.com"
    SEARCH_ENDPOINT = "/index.php"

    def __init__(self):
        """Initialize the scraper with Scrapling Fetcher."""
        self.fetcher = Fetcher
        self._cache = _TorrentResultsCache("gratistorrent")

    def _get_cache(self) -> _TorrentResultsCache:
        cache = getattr(self, "_cache", None)
        if cache is None:
            cache = _TorrentResultsCache("gratistorrent")
            self._cache = cache
        return cache

    def search(self, query: str) -> list[Title]:
        """Search for titles on gratistorrent.com.

        Args:
            query: Search query

        Returns:
            List of Title objects
        """
        try:
            cache_key = f"search:{query.strip().lower()}"
            found, cached = self._get_cache().get(cache_key)
            if found:
                return [Title.model_validate(item) for item in (cached or [])]

            result = self.fetcher.get(
                self.BASE_URL + self.SEARCH_ENDPOINT, params={"s": query}
            )

            if not result:
                self._get_cache().set(cache_key, [])
                return []

            # Get HTML content from the Scrapling response
            html = (
                getattr(result, "html_content", None)
                or getattr(result, "text", None)
                or ""
            )

            titles = self._parse_search_results(html)
            self._get_cache().set(
                cache_key, [title.model_dump(mode="json") for title in titles]
            )
            return titles

        except Exception as e:
            raise ScraperError(f"Search failed: {e}") from e

    def fetch_metadata(self, title_url: str) -> Optional[Title]:
        """Fetch metadata for a specific title.

        Args:
            title_url: URL of the title page

        Returns:
            Title object with metadata, or None if fetch fails
        """
        try:
            cache_key = f"metadata:{title_url}"
            found, cached = self._get_cache().get(cache_key)
            if found:
                return Title.model_validate(cached) if cached else None

            result = self.fetcher.get(title_url)

            if not result:
                self._get_cache().set(cache_key, None)
                return None

            # Get HTML content from the Scrapling response
            html = (
                getattr(result, "html_content", None)
                or getattr(result, "text", None)
                or ""
            )

            title = self._parse_title_page(html, title_url)
            self._get_cache().set(
                cache_key, title.model_dump(mode="json") if title else None
            )
            return title

        except Exception as e:
            raise ScraperError(f"Metadata fetch failed: {e}") from e

    def _parse_search_results(self, html: str) -> list[Title]:
        """Parse search results HTML.

        Args:
            html: HTML content

        Returns:
            List of Title objects
        """
        titles = []
        soup = BeautifulSoup(html, "html.parser")

        # Find all content items with class capa_lista
        items = soup.find_all("div", class_="capa_lista")

        for item in items:
            # Get the link (href) from the first <a> tag
            link = item.find("a", href=True)
            if not link:
                continue

            url = link.get("href", "")
            if not url:
                continue

            # Get title from h3 inside dados_capa
            title_elem = item.find("h3")
            title_name = title_elem.text.strip() if title_elem else "Unknown"

            # Determine media type from categoria span
            categoria_elem = item.find("span", class_="capa_categoria")
            categoria_text = (
                categoria_elem.text.strip().lower() if categoria_elem else "filme"
            )
            media_type = (
                MediaType.SERIES if "série" in categoria_text else MediaType.MOVIE
            )

            # Extract ID from URL
            title_id = urlparse(str(url)).path.strip("/").split("/")[-1]

            title = Title(
                id=title_id,
                name=title_name,
                media_type=media_type,
                url=str(url),
            )

            titles.append(title)

        return titles

    def _parse_title_page(self, html: str, url: str) -> Optional[Title]:
        """Parse title metadata page.

        Args:
            html: HTML content of title page
            url: URL of the title page

        Returns:
            Title object with metadata
        """
        soup = BeautifulSoup(html, "html.parser")

        # Extract title from h1
        h1 = soup.find("h1")
        title_name = h1.text.strip() if h1 else "Unknown"

        # Determine media type from URL and title
        media_type = MediaType.SERIES if "temporada" in url else MediaType.MOVIE

        # If still not detected, check title for season indicators (Portuguese)
        if media_type == MediaType.MOVIE:
            title_lower = title_name.lower()
            if any(
                term in title_lower
                for term in ["temporada", "1ª", "1a", "2ª", "2a", "season"]
            ):
                media_type = MediaType.SERIES

        # Extract ID from URL
        title_id = urlparse(url).path.strip("/").split("/")[-1]

        # Extract poster URL (look for img with poster in src)
        poster_url = None
        poster_pattern: Pattern[str] = re.compile(r"poster", re.IGNORECASE)
        img = soup.find("img", src=poster_pattern)
        if img:
            poster_url = img.get("src")

        # Extract episodes (for series)
        episodes: list[Episode] = []
        if media_type == MediaType.SERIES:
            episodes = self._parse_episodes(html)

        # Extract quality/language options
        quality_options = self._parse_quality_options(html)

        title = Title(
            id=title_id,
            name=title_name,
            media_type=media_type,
            url=url,
            poster_url=str(poster_url) if poster_url else None,
            episodes=episodes,
            quality_options=quality_options,
        )

        return title

    def _parse_episodes(self, html: str) -> list[Episode]:
        """Extract episode list from series page.

        Args:
            html: HTML content

        Returns:
            List of Episode objects
        """
        episodes = []

        # Look for episode links/listings - pattern may vary per site
        episode_pattern = r"Episode\s+(\d+)\s*-?\s*([^<]*)"
        matches = re.finditer(episode_pattern, html, re.IGNORECASE)

        for match in matches:
            episode_num = int(match.group(1))
            episode_title = match.group(2).strip() if match.group(2) else None

            episode = Episode(
                number=episode_num,
                title=episode_title,
            )
            episodes.append(episode)

        return episodes

    def _parse_quality_options(self, html: str) -> list[QualityOption]:
        return _parse_quality_options(html)


class ComandoLaScraper:
    """Scraper for comando.la content using StealthySession (Cloudflare bypass)."""

    BASE_URL = "https://comando.la"
    _MAX_RETRIES = 3
    _RETRY_DELAY = 2.0

    def __init__(self):
        """Initialize the scraper with StealthyFetcher for Cloudflare bypass."""
        from scrapling import StealthyFetcher

        self._fetcher = StealthyFetcher
        self._cache = _TorrentResultsCache("comando-la")

    def _get_cache(self) -> _TorrentResultsCache:
        cache = getattr(self, "_cache", None)
        if cache is None:
            cache = _TorrentResultsCache("comando-la")
            self._cache = cache
        return cache

    def search(self, query: str) -> list[Title]:
        """Search for titles on comando.la.

        Args:
            query: Search query

        Returns:
            List of Title objects
        """
        from urllib.parse import urlencode

        try:
            cache_key = f"search:{query.strip().lower()}"
            found, cached = self._get_cache().get(cache_key)
            if found:
                return [Title.model_validate(item) for item in (cached or [])]

            url = f"{self.BASE_URL}/?{urlencode({'s': query})}"
            result = self._fetch_with_retry(url)
            if not result:
                self._get_cache().set(cache_key, [])
                return []
            html = (
                getattr(result, "html_content", None)
                or getattr(result, "text", None)
                or ""
            )
            parsed = self._parse_search_results(html)
            self._get_cache().set(
                cache_key, [title.model_dump(mode="json") for title in parsed]
            )
            return parsed
        except Exception as e:
            raise ScraperError(f"Search failed: {e}") from e

    def fetch_metadata(self, title_url: str) -> Optional[Title]:
        """Fetch metadata for a specific title.

        Args:
            title_url: URL of the title page

        Returns:
            Title object with metadata, or None if fetch fails
        """
        try:
            cache_key = f"metadata:{title_url}"
            found, cached = self._get_cache().get(cache_key)
            if found:
                return Title.model_validate(cached) if cached else None

            result = self._fetch_with_retry(title_url)
            if not result:
                self._get_cache().set(cache_key, None)
                return None
            html = (
                getattr(result, "html_content", None)
                or getattr(result, "text", None)
                or ""
            )
            parsed = self._parse_title_page(html, title_url)
            self._get_cache().set(
                cache_key, parsed.model_dump(mode="json") if parsed else None
            )
            return parsed
        except Exception as e:
            raise ScraperError(f"Metadata fetch failed: {e}") from e

    def _fetch_with_retry(self, url: str):
        """Fetch URL: try CloakBrowser first, fallback to StealthyFetcher with retries."""

        # Primary: CloakBrowser (faster, 2.5x speed improvement)
        try:
            return self._fetch_with_cloak(url)
        except Exception as e:
            logger.debug(f"CloakBrowser fetch failed ({e}), falling back to Scrapling")

        # Fallback: Scrapling StealthyFetcher with retry logic
        last_exc: Exception = RuntimeError("No strategies attempted")
        for attempt in range(self._MAX_RETRIES):
            try:
                result = self._fetcher.fetch(
                    url,
                    headless=True,
                    network_idle=True,
                    google_search=False,
                    solve_cloudflare=True,
                )
                status = getattr(result, "status", None)
                if status is not None and status >= 400:
                    last_exc = ScraperError(f"HTTP {status} fetching {url}")
                    time.sleep(self._RETRY_DELAY * (2**attempt))
                    continue
                return result
            except ScraperError:
                raise
            except Exception as e:
                last_exc = e
                if attempt < self._MAX_RETRIES - 1:
                    time.sleep(self._RETRY_DELAY * (2**attempt))
        raise last_exc

    def _fetch_with_cloak(self, url: str):
        """Fetch URL with CloakBrowser (persistent context, Cloudflare auto-resolve).

        Returns an object compatible with Scrapling result (has .text and .html_content attributes).
        """
        from pathlib import Path

        from cloakbrowser import launch_persistent_context

        logger.debug(f"Fetching from cloakbrowser: {url}")

        # Persistent context saves cookies, so Cloudflare only needs to be solved once
        profile_dir = Path.home() / ".local/share/comando-cli/cloak_profile"
        profile_dir.parent.mkdir(parents=True, exist_ok=True)

        ctx = launch_persistent_context(str(profile_dir), headless=True, humanize=True)
        page = ctx.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=15000)
            time.sleep(3)  # Cloudflare auto-resolve
            html = page.content()
        finally:
            page.close()
            ctx.close()

        # Return object compatible with Scrapling's response interface
        logger.debug("Success fetching from cloakbrowser")
        return type("CloakResult", (), {"text": html, "html_content": html})()

    def _parse_search_results(self, html: str) -> list[Title]:
        """Parse search results HTML from comando.la.

        Args:
            html: HTML content

        Returns:
            List of Title objects
        """
        soup = BeautifulSoup(html, "html.parser")
        titles = []

        for article in soup.find_all("article"):
            header = article.find("header")
            if not header:
                continue
            h2 = header.find("h2")
            if not h2:
                continue
            a = h2.find("a", href=True)
            if not a:
                continue

            url = a.get("href", "")
            title_name = a.text.strip()
            if not url or not title_name:
                continue

            if "/series/" in url or "/serie/" in url:
                media_type = MediaType.SERIES
            elif any(kw in title_name.lower() for kw in ["temporada", "season"]):
                media_type = MediaType.SERIES
            else:
                media_type = MediaType.MOVIE

            title_id = urlparse(str(url)).path.strip("/").split("/")[-1]
            titles.append(
                Title(
                    id=title_id,
                    name=title_name,
                    media_type=media_type,
                    url=str(url),
                )
            )

        return titles

    def _parse_title_page(self, html: str, url: str) -> Optional[Title]:
        """Parse title metadata page from comando.la.

        Args:
            html: HTML content of title page
            url: URL of the title page

        Returns:
            Title object with metadata
        """
        soup = BeautifulSoup(html, "html.parser")

        h1 = soup.find("h1")
        title_name = h1.text.strip() if h1 else "Unknown"

        if "/series/" in url or "/serie/" in url:
            media_type = MediaType.SERIES
        elif any(
            kw in title_name.lower()
            for kw in ["temporada", "season", "1ª", "1a", "2ª", "2a"]
        ):
            media_type = MediaType.SERIES
        else:
            media_type = MediaType.MOVIE

        title_id = urlparse(url).path.strip("/").split("/")[-1]

        poster_url = None
        entry_content = soup.find("div", class_="entry-content")
        if entry_content:
            img = entry_content.find("img")
            if img:
                poster_url = img.get("src")

        episodes: list[Episode] = []
        if media_type == MediaType.SERIES:
            episodes = self._parse_episodes(html)

        quality_options = self._parse_quality_options(html)

        return Title(
            id=title_id,
            name=title_name,
            media_type=media_type,
            url=url,
            poster_url=str(poster_url) if poster_url else None,
            episodes=episodes,
            quality_options=quality_options,
        )

    def _parse_episodes(self, html: str) -> list[Episode]:
        """Extract episode list from a comando.la series page.

        Args:
            html: HTML content

        Returns:
            List of Episode objects (deduplicated by number)
        """
        soup = BeautifulSoup(html, "html.parser")
        seen: set[int] = set()
        episodes: list[Episode] = []

        entry_content = soup.find("div", class_="entry-content")
        if not entry_content:
            return episodes

        for p in entry_content.find_all("p"):
            strong = p.find("strong")
            if not strong:
                continue
            text = strong.get_text(strip=True)
            # Match "Episódio 01:" or "Ep. 1:" or "Episode 1"
            ep_match = re.search(r"[Ee]p(?:is[oó]dio)?\.?\s*(\d+)", text)
            if not ep_match:
                continue
            ep_num = int(ep_match.group(1))
            if ep_num not in seen:
                seen.add(ep_num)
                episodes.append(Episode(number=ep_num))

        return sorted(episodes, key=lambda e: e.number)

    def _parse_quality_options(self, html: str) -> list[QualityOption]:
        """Extract quality and language options from comando.la magnet links.

        Parses link text for quality ("1080p", "720p", "2160p 4K") and
        infers language from surrounding context and the magnet dn= param.

        Args:
            html: HTML content of title page

        Returns:
            List of QualityOption objects
        """
        from urllib.parse import unquote

        soup = BeautifulSoup(html, "html.parser")
        options: list[QualityOption] = []

        entry_content = soup.find("div", class_="entry-content")
        if not entry_content:
            return options

        magnet_pattern: Pattern[str] = re.compile(r"^magnet:")
        magnet_links = entry_content.find_all("a", href=magnet_pattern)

        for link in magnet_links:
            magnet_url: str = str(link.get("href", ""))
            if not magnet_url:
                continue

            # Quality from link text ("1080p", "720p", "2160p 4K", "Download Magnet")
            link_text = _normalize_text(link.get_text(strip=True))
            quality = "Unknown"
            for q in ["2160P", "4K", "1080P", "720P", "480P"]:
                if q in link_text:
                    quality = q.replace("P", "p") if q.endswith("P") else q
                    break

            # Fallback: extract quality from magnet dn= param
            if quality == "Unknown":
                dn_match = re.search(r"dn=([^&]+)", magnet_url)
                if dn_match:
                    dn = unquote(dn_match.group(1)).upper()
                    for q in ["2160P", "4K", "1080P", "720P", "480P"]:
                        if q in dn:
                            quality = q.replace("P", "p") if q.endswith("P") else q
                            break

            # Language from surrounding <p> and <strong> text and dn= param
            context_parts: list[str] = []
            parent_p = link.find_parent("p")
            if parent_p:
                context_parts.append(parent_p.get_text(" ", strip=True))

            # Walk up to find language headers (e.g. <strong>DUAL ÁUDIO</strong>)
            prev = link.find_previous("strong")
            if prev:
                context_parts.append(prev.get_text(strip=True))

            dn_match = re.search(r"dn=([^&]+)", magnet_url)
            dn_upper = unquote(dn_match.group(1)).upper() if dn_match else ""
            if dn_upper:
                context_parts.append(dn_upper)

            language = _classify_language(" ".join(context_parts))

            # Episode range from magnet dn= param
            # Handles: S02E04, S02E01-02-03, S02E05-06, S02E07-08-09
            episode = None
            episode_end = None
            ep_match = re.search(r"[Ss]\d{1,2}[Ee](\d{1,2})((?:-\d{2})+)?", dn_upper)
            if ep_match:
                episode = int(ep_match.group(1))
                if ep_match.group(2):
                    last = ep_match.group(2).rsplit("-", 1)[-1]
                    episode_end = int(last)

            options.append(
                QualityOption(
                    quality=quality,
                    language=language,
                    magnet_link=magnet_url,
                    display_name=parent_p.get_text(" ", strip=True) if parent_p else link.get_text(" ", strip=True),
                    episode=episode,
                    episode_end=episode_end,
                )
            )

        return options


class ScraperError(Exception):
    """Scraper-specific error."""

    pass
