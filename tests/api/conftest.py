"""Pytest fixtures for API integration tests.

These tests use the actual database for integration testing.
Ensure the database is populated with test data before running.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture(scope="module")
def client():
    """Create a FastAPI test client.

    This client uses the actual database connection for integration testing.
    The client is created once per test module for efficiency.

    Yields:
        TestClient: FastAPI test client instance.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def scripture_search_payload():
    """Basic scripture search request payload."""
    return {
        "query": "faith in Jesus Christ",
        "lang": "en",
        "limit": 5,
    }


@pytest.fixture
def cfm_search_payload():
    """Basic CFM lesson search request payload."""
    return {
        "query": "How can I strengthen my faith?",
        "lang": "en",
        "limit": 5,
    }


@pytest.fixture
def conference_search_payload():
    """Basic conference talk search request payload."""
    return {
        "query": "faith and repentance",
        "lang": "en",
        "limit": 5,
    }
