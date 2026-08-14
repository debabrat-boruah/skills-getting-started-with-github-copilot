"""
Pytest configuration and fixtures for API tests.

Provides:
- TestClient for making HTTP requests to the FastAPI app
- Fresh test data for each test to ensure isolation
"""

import pytest
from copy import deepcopy
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Provides a FastAPI TestClient for making requests to the app."""
    return TestClient(app)


@pytest.fixture
def sample_activities():
    """
    Provides a fresh copy of activities data for test isolation.
    
    Each test gets its own deep copy to prevent test interference.
    This isolates state changes in one test from affecting others.
    """
    return deepcopy(activities)


@pytest.fixture
def app_with_test_data(sample_activities, monkeypatch):
    """
    Patches the app's global activities dict with fresh test data.
    
    This ensures each test starts with a clean slate while using
    the real app instance. The monkeypatch reverts after each test.
    
    Returns:
        The patched app instance (same as global app, but with isolated data).
    """
    # Replace the global activities with a fresh copy
    monkeypatch.setattr("src.app.activities", sample_activities)
    return app
