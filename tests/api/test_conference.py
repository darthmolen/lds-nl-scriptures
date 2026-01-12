"""Integration tests for General Conference talk search endpoint.

Tests:
- Basic search returns results
- Year/month filter works
- Speaker filter works (partial match)
- Response structure matches schema
- Response times under 500ms
"""

import pytest


class TestConferenceSearchBasic:
    """Basic tests for the conference talk search endpoint."""

    def test_search_returns_200(self, client, conference_search_payload):
        """Test POST /api/v1/conference/search returns 200 status code."""
        response = client.post("/api/v1/conference/search", json=conference_search_payload)
        assert response.status_code == 200

    def test_search_returns_results(self, client, conference_search_payload):
        """Test search returns non-empty results list."""
        response = client.post("/api/v1/conference/search", json=conference_search_payload)
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)
        assert len(data["results"]) > 0

    def test_search_returns_meta(self, client, conference_search_payload):
        """Test search returns metadata with query, total_results, and search_time_ms."""
        response = client.post("/api/v1/conference/search", json=conference_search_payload)
        data = response.json()
        assert "meta" in data
        meta = data["meta"]
        assert "query" in meta
        assert "total_results" in meta
        assert "search_time_ms" in meta
        assert meta["query"] == conference_search_payload["query"]


class TestConferenceSearchResponseStructure:
    """Tests for conference search response structure matching schema."""

    def test_result_has_required_fields(self, client, conference_search_payload):
        """Test each result has all required fields from ConferenceResult schema."""
        response = client.post("/api/v1/conference/search", json=conference_search_payload)
        data = response.json()
        result = data["results"][0]

        # Check all required fields exist
        required_fields = [
            "id",
            "year",
            "month",
            "talk_uri",
            "paragraph_num",
            "text",
            "lang",
            "similarity",
        ]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

    def test_result_types_are_correct(self, client, conference_search_payload):
        """Test result field types match expected schema types."""
        response = client.post("/api/v1/conference/search", json=conference_search_payload)
        data = response.json()
        result = data["results"][0]

        assert isinstance(result["id"], int)
        assert isinstance(result["year"], int)
        assert isinstance(result["month"], str)
        assert isinstance(result["talk_uri"], str)
        assert isinstance(result["paragraph_num"], int)
        assert isinstance(result["text"], str)
        assert isinstance(result["lang"], str)
        assert isinstance(result["similarity"], float)

    def test_similarity_in_valid_range(self, client, conference_search_payload):
        """Test similarity scores are between 0 and 1."""
        response = client.post("/api/v1/conference/search", json=conference_search_payload)
        data = response.json()

        for result in data["results"]:
            assert 0.0 <= result["similarity"] <= 1.0

    def test_optional_fields_present_when_available(self, client, conference_search_payload):
        """Test optional fields are present in response structure."""
        response = client.post("/api/v1/conference/search", json=conference_search_payload)
        data = response.json()
        result = data["results"][0]

        # These fields are optional but should be present (may be None)
        optional_fields = [
            "session",
            "talk_title",
            "speaker_name",
            "speaker_role",
            "context_text",
            "scripture_refs",
        ]
        for field in optional_fields:
            assert field in result, f"Optional field not in response: {field}"


class TestConferenceSearchFilters:
    """Tests for conference search filtering functionality."""

    def test_year_filter(self, client):
        """Test filtering by year returns only results from that year."""
        payload = {
            "query": "faith and repentance",
            "lang": "en",
            "limit": 10,
            "year": 2024,
        }
        response = client.post("/api/v1/conference/search", json=payload)
        data = response.json()

        # If there are results, verify they match the filter
        if len(data["results"]) > 0:
            for result in data["results"]:
                assert result["year"] == 2024

    def test_month_filter_april(self, client):
        """Test filtering by April conference."""
        payload = {
            "query": "faith",
            "lang": "en",
            "limit": 10,
            "month": "04",
        }
        response = client.post("/api/v1/conference/search", json=payload)
        data = response.json()

        # If there are results, verify they match the filter
        if len(data["results"]) > 0:
            for result in data["results"]:
                assert result["month"] == "04"

    def test_month_filter_october(self, client):
        """Test filtering by October conference."""
        payload = {
            "query": "faith",
            "lang": "en",
            "limit": 10,
            "month": "10",
        }
        response = client.post("/api/v1/conference/search", json=payload)
        data = response.json()

        # If there are results, verify they match the filter
        if len(data["results"]) > 0:
            for result in data["results"]:
                assert result["month"] == "10"

    def test_year_and_month_filter(self, client):
        """Test filtering by both year and month."""
        payload = {
            "query": "faith",
            "lang": "en",
            "limit": 10,
            "year": 2024,
            "month": "04",
        }
        response = client.post("/api/v1/conference/search", json=payload)
        data = response.json()

        # If there are results, verify they match both filters
        if len(data["results"]) > 0:
            for result in data["results"]:
                assert result["year"] == 2024
                assert result["month"] == "04"

    def test_speaker_filter_partial_match(self, client):
        """Test speaker filter performs partial match."""
        payload = {
            "query": "faith",
            "lang": "en",
            "limit": 10,
            "speaker": "Nelson",
        }
        response = client.post("/api/v1/conference/search", json=payload)
        data = response.json()

        # If there are results, verify speaker name contains filter value
        if len(data["results"]) > 0:
            for result in data["results"]:
                if result["speaker_name"]:
                    assert "Nelson" in result["speaker_name"] or "nelson" in result["speaker_name"].lower()

    def test_combined_filters(self, client):
        """Test filtering by year, month, and speaker together."""
        payload = {
            "query": "faith",
            "lang": "en",
            "limit": 10,
            "year": 2024,
            "month": "04",
            "speaker": "Nelson",
        }
        response = client.post("/api/v1/conference/search", json=payload)
        data = response.json()

        # If there are results, verify all filters match
        if len(data["results"]) > 0:
            for result in data["results"]:
                assert result["year"] == 2024
                assert result["month"] == "04"

    def test_language_filter(self, client):
        """Test filtering by language returns correct language results."""
        payload = {
            "query": "faith",
            "lang": "en",
            "limit": 5,
        }
        response = client.post("/api/v1/conference/search", json=payload)
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
            response = client.post("/api/v1/conference/search", json=payload)
            data = response.json()

            assert len(data["results"]) <= limit
            assert data["meta"]["total_results"] <= limit


class TestConferenceSearchPerformance:
    """Tests for conference search response time performance."""

    def test_search_time_under_500ms(self, client, conference_search_payload):
        """Test typical search completes in under 500ms."""
        response = client.post("/api/v1/conference/search", json=conference_search_payload)
        data = response.json()

        assert data["meta"]["search_time_ms"] < 500, (
            f"Search took {data['meta']['search_time_ms']}ms, expected < 500ms"
        )

    def test_filtered_search_time_under_500ms(self, client):
        """Test filtered search completes in under 500ms."""
        payload = {
            "query": "faith and repentance",
            "lang": "en",
            "limit": 10,
            "year": 2024,
            "month": "04",
        }
        response = client.post("/api/v1/conference/search", json=payload)
        data = response.json()

        assert data["meta"]["search_time_ms"] < 500, (
            f"Search took {data['meta']['search_time_ms']}ms, expected < 500ms"
        )


class TestConferenceSearchValidation:
    """Tests for input validation on conference search endpoint."""

    def test_query_too_short_returns_422(self, client):
        """Test query shorter than 3 characters returns 422."""
        payload = {
            "query": "ab",  # Too short
            "lang": "en",
            "limit": 5,
        }
        response = client.post("/api/v1/conference/search", json=payload)
        assert response.status_code == 422

    def test_year_out_of_range_returns_422(self, client):
        """Test year outside 2014-2030 returns 422."""
        payload = {
            "query": "faith",
            "lang": "en",
            "limit": 5,
            "year": 2010,  # Before conference ingestion began
        }
        response = client.post("/api/v1/conference/search", json=payload)
        assert response.status_code == 422

    def test_invalid_month_returns_422(self, client):
        """Test month other than '04' or '10' returns 422."""
        payload = {
            "query": "faith",
            "lang": "en",
            "limit": 5,
            "month": "06",  # Not a conference month
        }
        response = client.post("/api/v1/conference/search", json=payload)
        assert response.status_code == 422

    def test_speaker_too_short_returns_422(self, client):
        """Test speaker filter shorter than 2 characters returns 422."""
        payload = {
            "query": "faith",
            "lang": "en",
            "limit": 5,
            "speaker": "N",  # Too short
        }
        response = client.post("/api/v1/conference/search", json=payload)
        assert response.status_code == 422

    def test_limit_out_of_range_returns_422(self, client):
        """Test limit > 50 returns 422."""
        payload = {
            "query": "faith",
            "lang": "en",
            "limit": 100,  # Too high
        }
        response = client.post("/api/v1/conference/search", json=payload)
        assert response.status_code == 422
