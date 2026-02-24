"""Tests for scraper module."""

from unittest.mock import MagicMock, patch

import pytest

from comando_cli.models import MediaType
from comando_cli.scraper import ComandoLaScraper, GratistorrentScraper, ScraperError


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

            # Test series URL (uses "temporada" keyword in URL)
            result = scraper.fetch_metadata("https://example.com/temporada-1/test/")
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
        """Test search uses index.php endpoint with 's' parameter."""
        with patch.object(scraper.fetcher, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.html_content = "<html></html>"
            mock_get.return_value = mock_response

            scraper.search("matrix")

            # Verify the endpoint and parameters
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert call_args[0][0] == "https://gratistorrent.com/index.php"
            assert call_args[1]['params'] == {'s': 'matrix'}



class TestComandoLaScraperSearchResults:
    """Tests for ComandoLaScraper._parse_search_results."""

    def test_parse_search_results_movie(self):
        scraper = ComandoLaScraper.__new__(ComandoLaScraper)
        html = """
        <article>
            <header>
                <h2><a href="https://comando.la/filmes/test-movie/">Test Movie</a></h2>
            </header>
        </article>
        """
        results = scraper._parse_search_results(html)
        assert len(results) == 1
        assert results[0].name == "Test Movie"
        assert results[0].media_type == MediaType.MOVIE
        assert results[0].url == "https://comando.la/filmes/test-movie/"

    def test_parse_search_results_series_by_url(self):
        scraper = ComandoLaScraper.__new__(ComandoLaScraper)
        html = """
        <article>
            <header>
                <h2><a href="https://comando.la/series/breaking-bad/">Breaking Bad</a></h2>
            </header>
        </article>
        """
        results = scraper._parse_search_results(html)
        assert len(results) == 1
        assert results[0].media_type == MediaType.SERIES

    def test_parse_search_results_series_by_keyword(self):
        scraper = ComandoLaScraper.__new__(ComandoLaScraper)
        html = """
        <article>
            <header>
                <h2><a href="https://comando.la/show-temporada-1/">Show 1ª Temporada</a></h2>
            </header>
        </article>
        """
        results = scraper._parse_search_results(html)
        assert results[0].media_type == MediaType.SERIES

    def test_parse_search_results_empty(self):
        scraper = ComandoLaScraper.__new__(ComandoLaScraper)
        results = scraper._parse_search_results("<html></html>")
        assert results == []

    def test_parse_search_results_extracts_id(self):
        scraper = ComandoLaScraper.__new__(ComandoLaScraper)
        html = """
        <article>
            <header>
                <h2><a href="https://comando.la/filmes/inception-2010/">Inception</a></h2>
            </header>
        </article>
        """
        results = scraper._parse_search_results(html)
        assert results[0].id == "inception-2010"

    def test_parse_search_results_multiple(self):
        scraper = ComandoLaScraper.__new__(ComandoLaScraper)
        html = """
        <article>
            <header><h2><a href="https://comando.la/filmes/movie-1/">Movie 1</a></h2></header>
        </article>
        <article>
            <header><h2><a href="https://comando.la/filmes/movie-2/">Movie 2</a></h2></header>
        </article>
        """
        results = scraper._parse_search_results(html)
        assert len(results) == 2
        assert results[0].name == "Movie 1"
        assert results[1].name == "Movie 2"


class TestComandoLaScraperTitlePage:
    """Tests for ComandoLaScraper._parse_title_page."""

    def test_parse_title_page_basic(self):
        scraper = ComandoLaScraper.__new__(ComandoLaScraper)
        html = "<h1>Test Movie</h1>"
        result = scraper._parse_title_page(html, "https://comando.la/filmes/test-movie/")
        assert result.name == "Test Movie"
        assert result.media_type == MediaType.MOVIE

    def test_parse_title_page_series_url(self):
        scraper = ComandoLaScraper.__new__(ComandoLaScraper)
        html = "<h1>Breaking Bad</h1>"
        result = scraper._parse_title_page(html, "https://comando.la/series/breaking-bad/")
        assert result.media_type == MediaType.SERIES

    def test_parse_title_page_poster(self):
        scraper = ComandoLaScraper.__new__(ComandoLaScraper)
        html = """
        <h1>Test Movie</h1>
        <div class="entry-content cf">
            <img src="https://exemplo.com/poster.jpg" />
        </div>
        """
        result = scraper._parse_title_page(html, "https://comando.la/filmes/test/")
        assert result.poster_url == "https://exemplo.com/poster.jpg"

    def test_parse_title_page_no_poster(self):
        scraper = ComandoLaScraper.__new__(ComandoLaScraper)
        html = "<h1>Test Movie</h1>"
        result = scraper._parse_title_page(html, "https://comando.la/filmes/test/")
        assert result.poster_url is None

    def test_parse_title_page_magnet_links(self):
        scraper = ComandoLaScraper.__new__(ComandoLaScraper)
        html = """
        <h1>Test Movie</h1>
        <span class="botao_dublado">1080P DUBLADO</span>
        <a href="magnet:?xt=urn:btih:abc123">DOWNLOAD</a>
        """
        result = scraper._parse_title_page(html, "https://comando.la/filmes/test/")
        assert len(result.quality_options) == 1
        assert result.quality_options[0].quality == "1080P"
        assert result.quality_options[0].magnet_link == "magnet:?xt=urn:btih:abc123"

    def test_parse_title_page_episode_from_magnet(self):
        scraper = ComandoLaScraper.__new__(ComandoLaScraper)
        html = """
        <h1>Breaking Bad</h1>
        <span class="botao_dublado">720P DUBLADO</span>
        <a href="magnet:?xt=urn:btih:abc&dn=Breaking.Bad.S01E03.mkv">DOWNLOAD</a>
        """
        result = scraper._parse_title_page(html, "https://comando.la/series/breaking-bad/")
        assert result.quality_options[0].episode == 3

    def test_parse_title_page_series_by_title_keyword(self):
        scraper = ComandoLaScraper.__new__(ComandoLaScraper)
        html = "<h1>Show 1ª Temporada</h1>"
        result = scraper._parse_title_page(html, "https://comando.la/show-temporada/")
        assert result.media_type == MediaType.SERIES


class TestComandoLaScraperIntegration:
    """Integration tests for ComandoLaScraper search/fetch_metadata with mocked session."""

    def _make_scraper_with_mock(self, html):
        scraper = ComandoLaScraper.__new__(ComandoLaScraper)
        mock_fetcher = MagicMock()
        mock_response = MagicMock()
        mock_response.html_content = html
        mock_fetcher.fetch.return_value = mock_response
        scraper._fetcher = mock_fetcher
        return scraper, mock_fetcher

    def test_search_calls_correct_url(self):
        scraper, mock_fetcher = self._make_scraper_with_mock("<html></html>")
        scraper.search("matrix")
        mock_fetcher.fetch.assert_called_once()
        call_args = mock_fetcher.fetch.call_args
        assert "comando.la" in call_args[0][0]
        assert "s=matrix" in call_args[0][0]

    def test_search_returns_empty_on_no_results(self):
        scraper, _ = self._make_scraper_with_mock("<html></html>")
        assert scraper.search("nada") == []

    def test_search_raises_scraper_error_on_failure(self):
        scraper = ComandoLaScraper.__new__(ComandoLaScraper)
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.side_effect = Exception("network error")
        scraper._fetcher = mock_fetcher
        scraper._MAX_RETRIES = 1
        with pytest.raises(ScraperError, match="Search failed"):
            scraper.search("test")

    def test_fetch_metadata_raises_scraper_error_on_failure(self):
        scraper = ComandoLaScraper.__new__(ComandoLaScraper)
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.side_effect = Exception("network error")
        scraper._fetcher = mock_fetcher
        scraper._MAX_RETRIES = 1
        with pytest.raises(ScraperError, match="Metadata fetch failed"):
            scraper.fetch_metadata("https://comando.la/filmes/test/")

    def test_fetch_metadata_returns_none_when_no_response(self):
        scraper, mock_fetcher = self._make_scraper_with_mock("")
        mock_fetcher.fetch.return_value = None
        result = scraper.fetch_metadata("https://comando.la/filmes/test/")
        assert result is None
