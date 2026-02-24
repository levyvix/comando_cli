"""Tests for scraper module."""

from unittest.mock import MagicMock, patch

import pytest

from comando_cli.models import MediaType
from comando_cli.scraper import GratistorrentScraper, ScraperError


@pytest.fixture
def scraper():
    """Create a scraper instance."""
    return GratistorrentScraper()


class TestSearchResults:
    """Tests for search functionality."""

    def test_search_returns_titles(self, scraper):
        """Test search returns list of Title objects."""
        html = """
        <div class="capa_lista">
            <a href="https://gratistorrent.com/test-movie-download/">
                <h3>Test Movie</h3>
            </a>
            <span class="capa_categoria">Filme</span>
        </div>
        """

        with patch.object(scraper.fetcher, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.html_content = html
            mock_get.return_value = mock_response

            results = scraper.search("test")

            assert len(results) == 1
            assert results[0].name == "Test Movie"
            assert results[0].media_type == MediaType.MOVIE

    def test_search_handles_empty_results(self, scraper):
        """Test search handles empty results."""
        html = "<html></html>"

        with patch.object(scraper.fetcher, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.html_content = html
            mock_get.return_value = mock_response

            results = scraper.search("nonexistent")

            assert results == []

    def test_search_identifies_series(self, scraper):
        """Test search identifies series vs movies."""
        html = """
        <div class="capa_lista">
            <a href="https://gratistorrent.com/test-series-download/">
                <h3>Test Series</h3>
            </a>
            <span class="capa_categoria">Série</span>
        </div>
        """

        with patch.object(scraper.fetcher, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.html_content = html
            mock_get.return_value = mock_response

            results = scraper.search("test")

            assert results[0].media_type == MediaType.SERIES

    def test_search_extracts_title_id(self, scraper):
        """Test search extracts title ID from URL."""
        html = """
        <div class="capa_lista">
            <a href="https://gratistorrent.com/test-movie-2024-download/">
                <h3>Test Movie</h3>
            </a>
            <span class="capa_categoria">Filme</span>
        </div>
        """

        with patch.object(scraper.fetcher, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.html_content = html
            mock_get.return_value = mock_response

            results = scraper.search("test")

            assert results[0].id == "test-movie-2024-download"

    def test_search_handles_fetcher_failure(self, scraper):
        """Test search handles fetcher returning None."""
        with patch.object(scraper.fetcher, 'get') as mock_get:
            mock_get.return_value = None

            results = scraper.search("test")

            assert results == []

    def test_search_multiple_results(self, scraper):
        """Test search returns multiple results."""
        html = """
        <div class="capa_lista">
            <a href="https://gratistorrent.com/movie-1/">
                <h3>Movie 1</h3>
            </a>
            <span class="capa_categoria">Filme</span>
        </div>
        <div class="capa_lista">
            <a href="https://gratistorrent.com/movie-2/">
                <h3>Movie 2</h3>
            </a>
            <span class="capa_categoria">Filme</span>
        </div>
        """

        with patch.object(scraper.fetcher, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.html_content = html
            mock_get.return_value = mock_response

            results = scraper.search("movie")

            assert len(results) == 2
            assert results[0].name == "Movie 1"
            assert results[1].name == "Movie 2"


class TestMetadataFetch:
    """Tests for metadata fetching."""

    def test_fetch_metadata_extracts_title(self, scraper):
        """Test fetch_metadata extracts title."""
        html = """
        <h1>Test Movie Title</h1>
        """

        with patch.object(scraper.fetcher, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.html_content = html
            mock_get.return_value = mock_response

            result = scraper.fetch_metadata("https://example.com/test/")

            assert result.name == "Test Movie Title"

    def test_fetch_metadata_extracts_poster(self, scraper):
        """Test fetch_metadata extracts poster URL."""
        html = """
        <h1>Test Movie</h1>
        <img src="https://example.com/poster/test.jpg" />
        """

        with patch.object(scraper.fetcher, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.html_content = html
            mock_get.return_value = mock_response

            result = scraper.fetch_metadata("https://example.com/test/")

            assert result.poster_url == "https://example.com/poster/test.jpg"

    def test_fetch_metadata_handles_missing_poster(self, scraper):
        """Test fetch_metadata handles missing poster."""
        html = "<h1>Test Movie</h1>"

        with patch.object(scraper.fetcher, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.html_content = html
            mock_get.return_value = mock_response

            result = scraper.fetch_metadata("https://example.com/test/")

            assert result.poster_url is None

    def test_fetch_metadata_determines_media_type_from_url(self, scraper):
        """Test fetch_metadata determines media type from URL."""
        html = "<h1>Test Series</h1>"

        with patch.object(scraper.fetcher, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.html_content = html
            mock_get.return_value = mock_response

            # Test series URL
            result = scraper.fetch_metadata("https://example.com/series/test/")
            assert result.media_type == MediaType.SERIES

            # Test movie URL
            result = scraper.fetch_metadata("https://example.com/filme/test/")
            assert result.media_type == MediaType.MOVIE

    def test_fetch_metadata_extracts_quality_options(self, scraper):
        """Test fetch_metadata extracts quality options."""
        html = """
        <h1>Test Movie</h1>
        <span class="botao_dublado">1080P DUBLADO</span>
        <a href="magnet:?xt=urn:btih:test1" title="Test 1080P">DOWNLOAD</a>
        <span class="botao_dublado">720P LEGENDADO</span>
        <a href="magnet:?xt=urn:btih:test2" title="Test 720P">DOWNLOAD</a>
        """

        with patch.object(scraper.fetcher, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.html_content = html
            mock_get.return_value = mock_response

            result = scraper.fetch_metadata("https://example.com/test/")

            assert len(result.quality_options) == 2
            assert result.quality_options[0].quality in ["1080P", "1080p"]
            assert result.quality_options[1].quality in ["720P", "720p"]

    def test_fetch_metadata_handles_missing_magnet_links(self, scraper):
        """Test fetch_metadata handles missing magnet links."""
        html = "<h1>Test Movie</h1>"

        with patch.object(scraper.fetcher, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.html_content = html
            mock_get.return_value = mock_response

            result = scraper.fetch_metadata("https://example.com/test/")

            assert result.quality_options == []

    def test_fetch_metadata_extracts_language(self, scraper):
        """Test fetch_metadata extracts language."""
        html = """
        <h1>Test Movie</h1>
        <span class="botao_dublado">1080P DUBLADO</span>
        <a href="magnet:?xt=urn:btih:test" title="Test">DOWNLOAD</a>
        """

        with patch.object(scraper.fetcher, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.html_content = html
            mock_get.return_value = mock_response

            result = scraper.fetch_metadata("https://example.com/test/")

            assert len(result.quality_options) > 0
            assert result.quality_options[0].language.lower() in ["dublado", "english", "portuguese"]

    def test_fetch_metadata_returns_none_on_failure(self, scraper):
        """Test fetch_metadata returns None on failure."""
        with patch.object(scraper.fetcher, 'get') as mock_get:
            mock_get.return_value = None

            result = scraper.fetch_metadata("https://example.com/test/")

            assert result is None

    def test_fetch_metadata_extracts_magnet_link(self, scraper):
        """Test fetch_metadata extracts actual magnet link."""
        magnet_url = "magnet:?xt=urn:btih:abc123&dn=test"
        html = f"""
        <h1>Test Movie</h1>
        <span class="botao_dublado">1080P</span>
        <a href="{magnet_url}" title="Test">DOWNLOAD</a>
        """

        with patch.object(scraper.fetcher, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.html_content = html
            mock_get.return_value = mock_response

            result = scraper.fetch_metadata("https://example.com/test/")

            assert result.quality_options[0].magnet_link == magnet_url


class TestErrorHandling:
    """Tests for error handling."""

    def test_search_exception_raises_scraper_error(self, scraper):
        """Test search exceptions are wrapped in ScraperError."""
        with patch.object(scraper.fetcher, 'get') as mock_get:
            mock_get.side_effect = Exception("Network error")

            with pytest.raises(ScraperError, match="Search failed"):
                scraper.search("test")

    def test_metadata_exception_raises_scraper_error(self, scraper):
        """Test metadata fetch exceptions are wrapped in ScraperError."""
        with patch.object(scraper.fetcher, 'get') as mock_get:
            mock_get.side_effect = Exception("Network error")

            with pytest.raises(ScraperError, match="Metadata fetch failed"):
                scraper.fetch_metadata("https://example.com/test/")


class TestSearchEndpoint:
    """Tests for search endpoint configuration."""

    def test_search_uses_correct_endpoint(self, scraper):
        """Test search uses root endpoint with 's' parameter."""
        with patch.object(scraper.fetcher, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.html_content = "<html></html>"
            mock_get.return_value = mock_response

            scraper.search("matrix")

            # Verify the endpoint and parameters
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert call_args[0][0] == "https://gratistorrent.com/"
            assert call_args[1]['params'] == {'s': 'matrix'}
