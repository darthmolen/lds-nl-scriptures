"""Integration tests for Come Follow Me (CFM) lesson search endpoint.

Tests:
- Basic search returns results
- Year filter works
- Testament filter works
- Response structure matches schema
- Response times under 500ms
"""

import pytest


class TestCFMSearchBasic:
    """Basic tests for the CFM lesson search endpoint."""

    def test_search_returns_200(self, client, cfm_search_payload):
        """Test POST /api/v1/cfm/search returns 200 status code."""
        response = client.post("/api/v1/cfm/search", json=cfm_search_payload)
        assert response.status_code == 200

    def test_search_returns_results(self, client, cfm_search_payload):
        """Test search returns non-empty results list."""
        response = client.post("/api/v1/cfm/search", json=cfm_search_payload)
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)
        assert len(data["results"]) > 0

    def test_search_returns_meta(self, client, cfm_search_payload):
        """Test search returns metadata with query, total_results, and search_time_ms."""
        response = client.post("/api/v1/cfm/search", json=cfm_search_payload)
        data = response.json()
        assert "meta" in data
        meta = data["meta"]
        assert "query" in meta
        assert "total_results" in meta
        assert "search_time_ms" in meta
        assert meta["query"] == cfm_search_payload["query"]


class TestCFMSearchResponseStructure:
    """Tests for CFM search response structure matching schema."""

    def test_result_has_required_fields(self, client, cfm_search_payload):
        """Test each result has all required fields from CFMResult schema."""
        response = client.post("/api/v1/cfm/search", json=cfm_search_payload)
        data = response.json()
        result = data["results"][0]

        # Check all required fields exist
        required_fields = [
            "id",
            "year",
            "lesson_id",
            "content_preview",
            "lang",
            "similarity",
        ]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

    def test_result_types_are_correct(self, client, cfm_search_payload):
        """Test result field types match expected schema types."""
        response = client.post("/api/v1/cfm/search", json=cfm_search_payload)
        data = response.json()
        result = data["results"][0]

        assert isinstance(result["id"], int)
        assert isinstance(result["year"], int)
        assert isinstance(result["lesson_id"], str)
        assert isinstance(result["content_preview"], str)
        assert isinstance(result["lang"], str)
        assert isinstance(result["similarity"], float)

    def test_similarity_in_valid_range(self, client, cfm_search_payload):
        """Test similarity scores are between 0 and 1."""
        response = client.post("/api/v1/cfm/search", json=cfm_search_payload)
        data = response.json()

        for result in data["results"]:
            assert 0.0 <= result["similarity"] <= 1.0

    def test_optional_fields_present_when_available(self, client, cfm_search_payload):
        """Test optional fields are present in response structure."""
        response = client.post("/api/v1/cfm/search", json=cfm_search_payload)
        data = response.json()
        result = data["results"][0]

        # These fields are optional but should be present (may be None)
        optional_fields = ["testament", "title", "date_range", "scripture_refs"]
        for field in optional_fields:
            assert field in result, f"Optional field not in response: {field}"


class TestCFMSearchFilters:
    """Tests for CFM search filtering functionality."""

    def test_year_filter(self, client):
        """Test filtering by year returns only results from that year."""
        payload = {
            "query": "How can I strengthen my faith?",
            "lang": "en",
            "limit": 10,
            "year": 2024,
        }
        response = client.post("/api/v1/cfm/search", json=payload)
        data = response.json()

        # If there are results, verify they match the filter
        if len(data["results"]) > 0:
            for result in data["results"]:
                assert result["year"] == 2024

    def test_testament_filter_bom(self, client):
        """Test filtering by Book of Mormon testament."""
        payload = {
            "query": "faith",
            "lang": "en",
            "limit": 10,
            "testament": "bom",
        }
        response = client.post("/api/v1/cfm/search", json=payload)
        data = response.json()

        # If there are results, verify they match the filter
        if len(data["results"]) > 0:
            for result in data["results"]:
                assert result["testament"] == "bom"

    def test_testament_filter_nt(self, client):
        """Test filtering by New Testament."""
        payload = {
            "query": "love one another",
            "lang": "en",
            "limit": 10,
            "testament": "nt",
        }
        response = client.post("/api/v1/cfm/search", json=payload)
        data = response.json()

        # If there are results, verify they match the filter
        if len(data["results"]) > 0:
            for result in data["results"]:
                assert result["testament"] == "nt"

    def test_combined_year_and_testament_filter(self, client):
        """Test filtering by both year and testament."""
        payload = {
            "query": "faith",
            "lang": "en",
            "limit": 10,
            "year": 2024,
            "testament": "bom",
        }
        response = client.post("/api/v1/cfm/search", json=payload)
        data = response.json()

        # If there are results, verify they match both filters
        if len(data["results"]) > 0:
            for result in data["results"]:
                assert result["year"] == 2024
                assert result["testament"] == "bom"

    def test_language_filter(self, client):
        """Test filtering by language returns correct language results."""
        payload = {
            "query": "faith",
            "lang": "en",
            "limit": 5,
        }
        response = client.post("/api/v1/cfm/search", json=payload)
        data = response.json()

        for result in data["results"]:
            assert result["lang"] == "en"

    def test_limit_constraint(self, client):
        """Test limit parameter constrains result count."""
        for limit in [1, 3, 5]:
            payload = {
                "query": "faith and repentance",
                "lang": "en",
                "limit": limit,
            }
            response = client.post("/api/v1/cfm/search", json=payload)
            data = response.json()

            assert len(data["results"]) <= limit
            assert data["meta"]["total_results"] <= limit


class TestCFMSearchPerformance:
    """Tests for CFM search response time performance."""

    def test_search_time_under_500ms(self, client, cfm_search_payload):
        """Test typical search completes in under 500ms."""
        response = client.post("/api/v1/cfm/search", json=cfm_search_payload)
        data = response.json()

        assert data["meta"]["search_time_ms"] < 500, (
            f"Search took {data['meta']['search_time_ms']}ms, expected < 500ms"
        )

    def test_filtered_search_time_under_500ms(self, client):
        """Test filtered search completes in under 500ms."""
        payload = {
            "query": "How can I strengthen my faith?",
            "lang": "en",
            "limit": 10,
            "year": 2024,
            "testament": "bom",
        }
        response = client.post("/api/v1/cfm/search", json=payload)
        data = response.json()

        assert data["meta"]["search_time_ms"] < 500, (
            f"Search took {data['meta']['search_time_ms']}ms, expected < 500ms"
        )


class TestCFMSearchValidation:
    """Tests for input validation on CFM search endpoint."""

    def test_query_too_short_returns_422(self, client):
        """Test query shorter than 3 characters returns 422."""
        payload = {
            "query": "ab",  # Too short
            "lang": "en",
            "limit": 5,
        }
        response = client.post("/api/v1/cfm/search", json=payload)
        assert response.status_code == 422

    def test_year_out_of_range_returns_422(self, client):
        """Test year outside 2019-2030 returns 422."""
        payload = {
            "query": "faith",
            "lang": "en",
            "limit": 5,
            "year": 2010,  # Before CFM began
        }
        response = client.post("/api/v1/cfm/search", json=payload)
        assert response.status_code == 422

    def test_invalid_testament_returns_422(self, client):
        """Test invalid testament value returns 422."""
        payload = {
            "query": "faith",
            "lang": "en",
            "limit": 5,
            "testament": "invalid",
        }
        response = client.post("/api/v1/cfm/search", json=payload)
        assert response.status_code == 422

    def test_limit_out_of_range_returns_422(self, client):
        """Test limit > 50 returns 422."""
        payload = {
            "query": "faith",
            "lang": "en",
            "limit": 100,  # Too high
        }
        response = client.post("/api/v1/cfm/search", json=payload)
        assert response.status_code == 422
