"""Web scraper for gratistorrent.com using Scrapling."""

import re
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from scrapling import Fetcher

from .models import Episode, MediaType, QualityOption, Title


class GratistorrentScraper:
    """Scraper for gratistorrent.com content."""

    BASE_URL = "https://gratistorrent.com"
    SEARCH_ENDPOINT = "/index.php"

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
            result = self.fetcher.get(self.BASE_URL + self.SEARCH_ENDPOINT, params={"s": query})

            if not result:
                return []

            # Get HTML content from the Scrapling response
            html = getattr(result, 'html_content', None) or getattr(result, 'text', None) or ""

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
            html = getattr(result, 'html_content', None) or getattr(result, 'text', None) or ""

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
        soup = BeautifulSoup(html, 'html.parser')

        # Find all content items with class capa_lista
        items = soup.find_all('div', class_='capa_lista')

        for item in items:
            # Get the link (href) from the first <a> tag
            link = item.find('a', href=True)
            if not link:
                continue

            url = link.get('href', '')
            if not url:
                continue

            # Get title from h3 inside dados_capa
            title_elem = item.find('h3')
            title_name = title_elem.text.strip() if title_elem else 'Unknown'

            # Determine media type from categoria span
            categoria_elem = item.find('span', class_='capa_categoria')
            categoria_text = categoria_elem.text.strip().lower() if categoria_elem else 'filme'
            media_type = MediaType.SERIES if 'série' in categoria_text else MediaType.MOVIE

            # Extract ID from URL
            title_id = urlparse(url).path.strip('/').split('/')[-1]

            title = Title(
                id=title_id,
                name=title_name,
                media_type=media_type,
                url=url,
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
        soup = BeautifulSoup(html, 'html.parser')

        # Extract title from h1
        h1 = soup.find('h1')
        title_name = h1.text.strip() if h1 else "Unknown"

        # Determine media type from URL
        media_type = MediaType.SERIES if "/series/" in url else MediaType.MOVIE

        # Extract ID from URL
        title_id = urlparse(url).path.strip("/").split("/")[-1]

        # Extract poster URL (look for img with poster in src)
        poster_url = None
        img = soup.find('img', src=lambda x: x and 'poster' in x.lower())
        if img:
            poster_url = img.get('src')

        # Extract synopsis
        synopsis = None
        p_tags = soup.find_all('p')
        for p in p_tags:
            text = p.get_text(separator=' ')
            if len(text) > 100 and 'sinopse' in text.lower():
                synopsis = text.strip()[:500]
                break

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
        soup = BeautifulSoup(html, 'html.parser')
        options = []

        # Find all magnet links
        magnet_links = soup.find_all('a', href=lambda x: x and x.startswith('magnet:'))

        for link in magnet_links:
            magnet_url = link.get('href', '')
            if not magnet_url:
                continue

            # Extract quality and language from title attribute and nearby text
            title_attr = link.get('title', '')
            text_before = ''

            # Get preceding span with class botao_dublado
            prev_span = link.find_previous('span', class_='botao_dublado')
            if prev_span:
                text_before = prev_span.text.strip()

            # Combine title and preceding text
            full_text = (text_before + ' ' + title_attr).upper()

            # Extract quality
            quality = 'Unknown'
            quality_patterns = ['1080p', '720p', '480p', '4k', 'hdtv', 'bluray', 'dvdrip']
            for pattern in quality_patterns:
                if pattern.upper() in full_text:
                    quality = pattern.upper()
                    break

            # Extract language
            language = 'Portuguese'
            language_patterns = ['Portuguese', 'English', 'Dublado', 'Legendado', 'Dual']
            for pattern in language_patterns:
                if pattern.upper() in full_text:
                    language = pattern.capitalize()
                    break

            option = QualityOption(
                quality=quality,
                language=language,
                magnet_link=magnet_url,
            )
            options.append(option)

        return options


class ScraperError(Exception):
    """Scraper-specific error."""

    pass
