"""Web scrapers for torrent sites using Scrapling."""

import re
import time
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from scrapling import Fetcher

from .models import Episode, MediaType, QualityOption, Title


def _parse_quality_options(html: str) -> list[QualityOption]:
    """Extract quality and language options from magnet links.

    Used by GratistorrentScraper. ComandoLaScraper has its own implementation.
    """
    from urllib.parse import unquote

    soup = BeautifulSoup(html, "html.parser")
    options = []

    magnet_links = soup.find_all("a", href=lambda x: x and x.startswith("magnet:"))

    for link in magnet_links:
        magnet_url = link.get("href", "")
        if not magnet_url:
            continue

        title_attr = link.get("title", "")
        prev_span = link.find_previous("span", class_="botao_dublado")
        text_before = prev_span.text.strip() if prev_span else ""

        full_text = (text_before + " " + title_attr).upper()

        quality = "Unknown"
        for pattern in ["1080P", "720P", "480P", "4K", "HDTV", "BLURAY", "DVDRIP", "MKV"]:
            if pattern in full_text:
                quality = pattern
                break

        language = "Portuguese"
        for pattern in ["DUBLADO", "LEGENDADO", "DUAL", "ENGLISH", "PORTUGUESE"]:
            if pattern in full_text:
                language = pattern.capitalize()
                break

        episode = None
        dn_match = re.search(r"dn=([^&]+)", magnet_url)
        if dn_match:
            filename = unquote(dn_match.group(1))
            ep_match = re.search(r"[Ss](\d{1,2})[Ee](\d{1,2})", filename)
            if ep_match:
                episode = int(ep_match.group(2))

        options.append(QualityOption(
            quality=quality,
            language=language,
            magnet_link=magnet_url,
            episode=episode,
        ))

    return options


class GratistorrentScraper:
    """Scraper for gratistorrent.com content."""

    BASE_URL = "https://gratistorrent.com"
    SEARCH_ENDPOINT = "/index.php"

    def __init__(self):
        """Initialize the scraper with Scrapling Fetcher."""
        self.fetcher = Fetcher

    def search(self, query: str) -> list[Title]:
        """Search for titles on gratistorrent.com.

        Args:
            query: Search query

        Returns:
            List of Title objects
        """
        try:
            result = self.fetcher.get(
                self.BASE_URL + self.SEARCH_ENDPOINT, params={"s": query}
            )

            if not result:
                return []

            # Get HTML content from the Scrapling response
            html = (
                getattr(result, "html_content", None)
                or getattr(result, "text", None)
                or ""
            )

            titles = self._parse_search_results(html)
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
            result = self.fetcher.get(title_url)

            if not result:
                return None

            # Get HTML content from the Scrapling response
            html = (
                getattr(result, "html_content", None)
                or getattr(result, "text", None)
                or ""
            )

            title = self._parse_title_page(html, title_url)
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
        img = soup.find("img", src=lambda x: x and "poster" in x.lower())
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

    def search(self, query: str) -> list[Title]:
        """Search for titles on comando.la.

        Args:
            query: Search query

        Returns:
            List of Title objects
        """
        from urllib.parse import urlencode
        try:
            url = f"{self.BASE_URL}/?{urlencode({'s': query})}"
            result = self._fetch_with_retry(url)
            if not result:
                return []
            html = (
                getattr(result, "html_content", None)
                or getattr(result, "text", None)
                or ""
            )
            return self._parse_search_results(html)
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
            result = self._fetch_with_retry(title_url)
            if not result:
                return None
            html = (
                getattr(result, "html_content", None)
                or getattr(result, "text", None)
                or ""
            )
            return self._parse_title_page(html, title_url)
        except Exception as e:
            raise ScraperError(f"Metadata fetch failed: {e}") from e

    def _fetch_with_retry(self, url: str):
        """Fetch URL with real Chrome to bypass bot detection."""
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
                    time.sleep(self._RETRY_DELAY * (2 ** attempt))
                    continue
                return result
            except ScraperError:
                raise
            except Exception as e:
                last_exc = e
                if attempt < self._MAX_RETRIES - 1:
                    time.sleep(self._RETRY_DELAY * (2 ** attempt))
        raise last_exc

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

            title_id = urlparse(url).path.strip("/").split("/")[-1]
            titles.append(Title(
                id=title_id,
                name=title_name,
                media_type=media_type,
                url=url,
            ))

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
        elif any(kw in title_name.lower() for kw in ["temporada", "season", "1ª", "1a", "2ª", "2a"]):
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

        magnet_links = entry_content.find_all(
            "a", href=lambda x: x and x.startswith("magnet:")
        )

        for link in magnet_links:
            magnet_url = link.get("href", "")
            if not magnet_url:
                continue

            # Quality from link text ("1080p", "720p", "2160p 4K", "Download Magnet")
            link_text = link.get_text(strip=True).upper()
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
            context_text = ""
            parent_p = link.find_parent("p")
            if parent_p:
                context_text = parent_p.get_text(" ", strip=True).upper()

            # Walk up to find language headers (e.g. <strong>DUAL ÁUDIO</strong>)
            prev = link.find_previous("strong")
            if prev:
                context_text += " " + prev.get_text(strip=True).upper()

            dn_match = re.search(r"dn=([^&]+)", magnet_url)
            dn_upper = unquote(dn_match.group(1)).upper() if dn_match else ""
            context_text += " " + dn_upper

            language = "Portuguese"
            if "DUAL" in context_text:
                language = "Dual"
            elif "DUBLADO" in context_text or ".DUB." in context_text:
                language = "Dubbed"
            elif "LEGENDADO" in context_text or ".LEG." in context_text:
                language = "Subtitled"

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

            options.append(QualityOption(
                quality=quality,
                language=language,
                magnet_link=magnet_url,
                episode=episode,
                episode_end=episode_end,
            ))

        return options


class ScraperError(Exception):
    """Scraper-specific error."""

    pass
