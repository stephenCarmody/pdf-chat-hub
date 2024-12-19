import uuid
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from models.api_models import AppInfo
from routers.router import router
from services.pdf_chat_service import PDFChatService


@pytest.fixture
def mock_pdf_service():
    """Create a mock PDF service."""
    mock_service = Mock(spec=PDFChatService)
    mock_service.query.return_value = "Mock response"
    return mock_service


@pytest.fixture
def test_client(mock_pdf_service):
    """Create a test client with mocked dependencies."""
    
    def get_test_pdf_service():
        return mock_pdf_service

    # Override the dependency
    router.dependency_overrides[get_pdf_service] = get_test_pdf_service
    client = TestClient(router)
    yield client
    router.dependency_overrides.clear()


class TestAPIRouter:
    def test_read_root(self, test_client):
        """Test the root endpoint returns correct app info."""
        response = test_client.get("/prod/")
        assert response.status_code == 200
        
        expected = AppInfo(
            name="Chat with PDFs",
            version="0.1.0",
            description="A simple chatbot that can answer questions about a PDF file.",
        )
        assert response.json() == expected.model_dump()

    def test_get_session(self, test_client):
        """Test session generation endpoint."""
        with patch('uuid.uuid4', return_value='test-uuid'):
            response = test_client.get("/prod/session")
            assert response.status_code == 200
            assert response.json() == {"session": "test-uuid"}

    def test_query_endpoint(self, test_client, mock_pdf_service):
        """Test the query endpoint."""
        request_data = {
            "query": "What is this about?",
            "session_id": "test-session",
            "chat_history": [("Hello", "Hi there")]
        }

        response = test_client.post("/prod/query", json=request_data)
        
        assert response.status_code == 200
        assert response.json() == {"message": "Mock response"}
        
        # Verify PDF service was called correctly
        mock_pdf_service.query.assert_called_once_with(
            query="What is this about?",
            session_id="test-session",
            chat_history=[("Hello", "Hi there")]
        )

    def test_upload_endpoint(self, test_client, mock_pdf_service, tmp_path):
        """Test the file upload endpoint."""
        # Create a test PDF file
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"fake PDF content")
        
        # Mock file upload
        with open(test_file, "rb") as f:
            response = test_client.post(
                "/prod/upload",
                files={"file": ("test.pdf", f, "application/pdf")},
                params={"session_id": "test-session"}
            )

        assert response.status_code == 200
        assert response.json() == {
            "message": "File uploaded successfully!",
            "filename": "test.pdf"
        }
        
        # Verify PDF service was called
        mock_pdf_service.upload.assert_called_once()
        # The file path will be dynamic, so we just check if it was called with the session_id
        assert mock_pdf_service.upload.call_args[0][1] == "test-session"

    def test_upload_endpoint_failure(self, test_client, mock_pdf_service):
        """Test upload endpoint handles errors properly."""
        mock_pdf_service.upload.side_effect = Exception("PDF processing failed")

        with open(__file__, "rb") as f:  # Use this test file as fake upload
            response = test_client.post(
                "/prod/upload",
                files={"file": ("test.pdf", f, "application/pdf")},
                params={"session_id": "test-session"}
            )

        assert response.status_code == 400
        assert "PDF processing failed" in response.json()["detail"]
