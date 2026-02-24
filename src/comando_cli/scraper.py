"""Web scraper for gratistorrent.com using Scrapling."""

import re
from typing import Optional
from urllib.parse import urljoin, urlparse

from scrapling import Fetcher

from .models import Episode, MediaType, QualityOption, Title


class GratistorrentScraper:
    """Scraper for gratistorrent.com content."""

    BASE_URL = "https://www.gratistorrent.com"
    SEARCH_URL = f"{BASE_URL}/search"

    def __init__(self):
        """Initialize the scraper with Scrapling Fetcher."""
        self.fetcher = Fetcher()

    def search(self, query: str) -> list[Title]:
        """Search for titles on gratistorrent.com.

        Args:
            query: Search query

        Returns:
            List of Title objects
        """
        try:
            result = self.fetcher.get(self.SEARCH_URL, params={"q": query})

            if not result:
                return []

            # Try to get HTML content from the response
            html = getattr(result, 'text', None) or getattr(result, 'content', None) or ""
            if isinstance(html, bytes):
                html = html.decode('utf-8', errors='ignore')

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

            # Try to get HTML content from the response
            html = getattr(result, 'text', None) or getattr(result, 'content', None) or ""
            if isinstance(html, bytes):
                html = html.decode('utf-8', errors='ignore')

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

        # Find all title containers - look for links to filme/ or series/
        link_pattern = r'href="([^"]*(?:filme|series)/[^"]*)"[^>]*>([^<]+)<'
        links = re.findall(link_pattern, html, re.IGNORECASE)

        for link_url, title_name in links:
            full_url = urljoin(self.BASE_URL, link_url)

            # Determine media type from URL
            media_type = MediaType.SERIES if "/series/" in full_url else MediaType.MOVIE

            # Extract ID from URL
            title_id = urlparse(full_url).path.strip("/").split("/")[-1]

            title = Title(
                id=title_id,
                name=title_name.strip(),
                media_type=media_type,
                url=full_url,
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
        # Extract title from page
        title_match = re.search(r"<h1[^>]*>([^<]+)</h1>", html)
        title_name = title_match.group(1).strip() if title_match else "Unknown"

        # Determine media type from URL
        media_type = MediaType.SERIES if "/series/" in url else MediaType.MOVIE

        # Extract ID from URL
        title_id = urlparse(url).path.strip("/").split("/")[-1]

        # Extract poster URL
        poster_match = re.search(r'<img[^>]+src="([^"]*poster[^"]*)"', html, re.IGNORECASE)
        poster_url = poster_match.group(1) if poster_match else None

        # Extract synopsis
        synopsis_match = re.search(r'<p[^>]*class="[^"]*synopsis[^"]*"[^>]*>([^<]+)</p>', html)
        synopsis = synopsis_match.group(1).strip() if synopsis_match else None

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
            poster_url=poster_url,
            synopsis=synopsis,
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
        """Extract quality and language options.

        Args:
            html: HTML content

        Returns:
            List of QualityOption objects
        """
        options = []

        # Look for magnet links with quality indicators
        magnet_pattern = r"(magnet:\?[^\"\s<]+)"
        quality_pattern = r"(\d{3,4}p|HDTV|BluRay|DVDRip)"
        language_pattern = r"(Português|English|Dublado|Legendado|PT|EN|PTBR|ENG)"

        magnets = re.findall(magnet_pattern, html)
        qualities = re.findall(quality_pattern, html, re.IGNORECASE)
        languages = re.findall(language_pattern, html, re.IGNORECASE)

        # Create combinations if available
        for magnet in magnets[:5]:
            quality = qualities[0] if qualities else "Unknown"
            language = languages[0] if languages else "Portuguese"

            option = QualityOption(
                quality=quality,
                language=language,
                magnet_link=magnet,
            )
            options.append(option)

        return options


class ScraperError(Exception):
    """Scraper-specific error."""

    pass
