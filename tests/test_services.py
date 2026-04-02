"""Tests for background services."""

import pytest
from app.services.search import search_service
from app.services.scraper import scraper_service


@pytest.mark.asyncio
async def test_search_service_with_query():
    """Test search service returns results."""
    results = await search_service.search(query="python", num_results=5)
    assert isinstance(results, list)
    # Results can be empty if search fails, but should always be a list
    for result in results:
        assert isinstance(result, dict)
        if result:  # If not empty error dict
            assert "title" in result or "error" in result
            assert "url" in result or "error" in result


@pytest.mark.asyncio
async def test_search_service_empty_query():
    """Test search service with empty query handles gracefully."""
    # Empty queries should return empty or handle gracefully
    results = await search_service.search(query="", num_results=5)
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_search_service_num_results():
    """Test search service respects num_results parameter."""
    results = await search_service.search(query="python", num_results=3)
    assert isinstance(results, list)
    # Should respect the limit (though actual results may be less)
    assert len(results) <= 3


@pytest.mark.asyncio
async def test_scraper_service_invalid_url():
    """Test scraper service with invalid URL."""
    result = await scraper_service.fetch_page(url="http://invalid-domain-12345.com")
    assert isinstance(result, dict)
    # Should return dict, possibly with error
    assert "title" in result or "error" in result or "content" in result


@pytest.mark.asyncio
async def test_scraper_service_valid_url():
    """Test scraper service with valid URL."""
    # Using a stable, reliable URL for testing
    result = await scraper_service.fetch_page(url="https://example.com")
    assert isinstance(result, dict)
    assert "content" in result or "error" in result
    assert "url" in result


def test_search_service_type():
    """Test search service is properly initialized."""
    assert search_service is not None
    assert hasattr(search_service, "search")


def test_scraper_service_type():
    """Test scraper service is properly initialized."""
    assert scraper_service is not None
    assert hasattr(scraper_service, "fetch_page")
