from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from dependencies.services import get_pdf_service
from routers.router import router


@pytest.fixture
def test_app():
    """Create a test FastAPI application with our router"""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def test_client(test_app):
    """Create a test client with mocked PDF service"""
    # Create mock PDF service
    mock_pdf_service = Mock()
    mock_pdf_service.query.return_value = "Mock response"

    # Override the dependency
    test_app.dependency_overrides[get_pdf_service] = lambda: mock_pdf_service

    # Create and return test client
    client = TestClient(test_app)
    return client, mock_pdf_service


def test_query_endpoint(test_client):
    """Test the query endpoint"""
    client, mock_pdf_service = test_client

    # Test data
    test_request = {
        "query": "test question",
        "session_id": "test-session",
        "chat_history": [],
    }

    # Make request
    response = client.post("/prod/query", json=test_request)

    # Assert response
    assert response.status_code == 200
    assert response.json() == {"message": "Mock response"}

    # Verify service was called correctly
    mock_pdf_service.query.assert_called_once_with(
        query="test question", session_id="test-session", chat_history=[]
    )
