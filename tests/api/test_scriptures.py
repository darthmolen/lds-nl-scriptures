"""Integration tests for scripture search endpoint.

Tests:
- Basic search returns results
- Volume filter works
- Language filter works
- Limit constraint works
- Response structure matches schema
- Response times under 500ms
"""

import pytest


class TestScriptureSearchBasic:
    """Basic tests for the scripture search endpoint."""

    def test_search_returns_200(self, client, scripture_search_payload):
        """Test POST /api/v1/scriptures/search returns 200 status code."""
        response = client.post("/api/v1/scriptures/search", json=scripture_search_payload)
        assert response.status_code == 200

    def test_search_returns_results(self, client, scripture_search_payload):
        """Test search returns non-empty results list."""
        response = client.post("/api/v1/scriptures/search", json=scripture_search_payload)
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)
        assert len(data["results"]) > 0

    def test_search_returns_meta(self, client, scripture_search_payload):
        """Test search returns metadata with query, total_results, and search_time_ms."""
        response = client.post("/api/v1/scriptures/search", json=scripture_search_payload)
        data = response.json()
        assert "meta" in data
        meta = data["meta"]
        assert "query" in meta
        assert "total_results" in meta
        assert "search_time_ms" in meta
        assert meta["query"] == scripture_search_payload["query"]


class TestScriptureSearchResponseStructure:
    """Tests for scripture search response structure matching schema."""

    def test_result_has_required_fields(self, client, scripture_search_payload):
        """Test each result has all required fields from ScriptureResult schema."""
        response = client.post("/api/v1/scriptures/search", json=scripture_search_payload)
        data = response.json()
        result = data["results"][0]

        # Check all required fields exist
        required_fields = [
            "id",
            "volume",
            "book",
            "chapter",
            "verse",
            "text",
            "lang",
            "similarity",
            "reference",
        ]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

    def test_result_types_are_correct(self, client, scripture_search_payload):
        """Test result field types match expected schema types."""
        response = client.post("/api/v1/scriptures/search", json=scripture_search_payload)
        data = response.json()
        result = data["results"][0]

        assert isinstance(result["id"], int)
        assert isinstance(result["volume"], str)
        assert isinstance(result["book"], str)
        assert isinstance(result["chapter"], int)
        assert isinstance(result["verse"], int)
        assert isinstance(result["text"], str)
        assert isinstance(result["lang"], str)
        assert isinstance(result["similarity"], float)
        assert isinstance(result["reference"], str)

    def test_similarity_in_valid_range(self, client, scripture_search_payload):
        """Test similarity scores are between 0 and 1."""
        response = client.post("/api/v1/scriptures/search", json=scripture_search_payload)
        data = response.json()

        for result in data["results"]:
            assert 0.0 <= result["similarity"] <= 1.0


class TestScriptureSearchFilters:
    """Tests for scripture search filtering functionality."""

    def test_volume_filter_book_of_mormon(self, client):
        """Test filtering by Book of Mormon volume returns only BOM results."""
        payload = {
            "query": "faith in Jesus Christ",
            "lang": "en",
            "limit": 10,
            "volume": "bookofmormon",
        }
        response = client.post("/api/v1/scriptures/search", json=payload)
        data = response.json()

        assert len(data["results"]) > 0
        for result in data["results"]:
            assert result["volume"] == "bookofmormon"

    def test_volume_filter_old_testament(self, client):
        """Test filtering by Old Testament volume."""
        payload = {
            "query": "covenant with Abraham",
            "lang": "en",
            "limit": 10,
            "volume": "oldtestament",
        }
        response = client.post("/api/v1/scriptures/search", json=payload)
        data = response.json()

        for result in data["results"]:
            assert result["volume"] == "oldtestament"

    def test_volume_filter_new_testament(self, client):
        """Test filtering by New Testament volume."""
        payload = {
            "query": "love one another",
            "lang": "en",
            "limit": 10,
            "volume": "newtestament",
        }
        response = client.post("/api/v1/scriptures/search", json=payload)
        data = response.json()

        for result in data["results"]:
            assert result["volume"] == "newtestament"

    def test_language_filter_english(self, client):
        """Test filtering by English language returns only English results."""
        payload = {
            "query": "faith",
            "lang": "en",
            "limit": 5,
        }
        response = client.post("/api/v1/scriptures/search", json=payload)
        data = response.json()

        for result in data["results"]:
            assert result["lang"] == "en"

    def test_limit_constraint(self, client):
        """Test limit parameter constrains result count."""
        for limit in [1, 3, 5, 10]:
            payload = {
                "query": "faith",
                "lang": "en",
                "limit": limit,
            }
            response = client.post("/api/v1/scriptures/search", json=payload)
            data = response.json()

            assert len(data["results"]) <= limit
            assert data["meta"]["total_results"] <= limit


class TestScriptureSearchPerformance:
    """Tests for scripture search response time performance."""

    def test_search_time_under_500ms(self, client, scripture_search_payload):
        """Test typical search completes in under 500ms."""
        response = client.post("/api/v1/scriptures/search", json=scripture_search_payload)
        data = response.json()

        assert data["meta"]["search_time_ms"] < 500, (
            f"Search took {data['meta']['search_time_ms']}ms, expected < 500ms"
        )

    def test_filtered_search_time_under_500ms(self, client):
        """Test filtered search completes in under 500ms."""
        payload = {
            "query": "faith in Jesus Christ",
            "lang": "en",
            "limit": 10,
            "volume": "bookofmormon",
        }
        response = client.post("/api/v1/scriptures/search", json=payload)
        data = response.json()

        assert data["meta"]["search_time_ms"] < 500, (
            f"Search took {data['meta']['search_time_ms']}ms, expected < 500ms"
        )


class TestScriptureSearchValidation:
    """Tests for input validation on scripture search endpoint."""

    def test_query_too_short_returns_422(self, client):
        """Test query shorter than 3 characters returns 422."""
        payload = {
            "query": "ab",  # Too short
            "lang": "en",
            "limit": 5,
        }
        response = client.post("/api/v1/scriptures/search", json=payload)
        assert response.status_code == 422

    def test_limit_out_of_range_returns_422(self, client):
        """Test limit > 50 returns 422."""
        payload = {
            "query": "faith",
            "lang": "en",
            "limit": 100,  # Too high
        }
        response = client.post("/api/v1/scriptures/search", json=payload)
        assert response.status_code == 422

    def test_invalid_volume_returns_422(self, client):
        """Test invalid volume value returns 422."""
        payload = {
            "query": "faith",
            "lang": "en",
            "limit": 5,
            "volume": "invalidvolume",
        }
        response = client.post("/api/v1/scriptures/search", json=payload)
        assert response.status_code == 422

    def test_invalid_language_returns_422(self, client):
        """Test invalid language value returns 422."""
        payload = {
            "query": "faith",
            "lang": "fr",  # Not supported
            "limit": 5,
        }
        response = client.post("/api/v1/scriptures/search", json=payload)
        assert response.status_code == 422
