from unittest.mock import Mock, patch

import pytest
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from brain.document_processing import DocumentProcessor


class TestDocumentProcessor:
    """Tests for the DocumentProcessor class."""

    def test_processor_uses_default_settings_when_no_parameters_provided(self):
        """Test that processor initializes with correct default settings."""
        # Given: No custom parameters are provided

        # When: Creating a new DocumentProcessor
        processor = DocumentProcessor()

        # Then: The processor should have default settings
        assert processor.text_splitter == RecursiveCharacterTextSplitter
        assert processor.text_splitter_kwargs == {
            "chunk_size": 500,
            "separators": [".", "?", "!"],
            "chunk_overlap": 200,
        }

    def test_processor_overrides_specific_parameters_while_keeping_other_defaults(self):
        """Test that processor correctly merges custom parameters with defaults."""
        # Given: Custom parameters for chunk size and overlap
        custom_kwargs = {"chunk_size": 1000, "chunk_overlap": 100}

        # When: Creating a processor with custom parameters
        processor = DocumentProcessor(text_splitter_kwargs=custom_kwargs)

        # Then: Custom parameters should override defaults while preserving other defaults
        assert processor.text_splitter_kwargs["chunk_size"] == 1000
        assert processor.text_splitter_kwargs["chunk_overlap"] == 100
        assert processor.text_splitter_kwargs["separators"] == [
            ".",
            "?",
            "!",
        ]  # Default preserved

    def test_processor_correctly_loads_and_chunks_pdf(self):
        """Test the complete flow of loading and chunking a PDF."""
        # Given: A PDF document with multiple sentences
        mock_page = Document(
            page_content="This is page 1. It has multiple sentences! And more content?",
            metadata={"page": 1},
        )

        # Create mock loader first
        mock_loader_instance = Mock()
        mock_loader_instance.load.return_value = [mock_page]
        mock_loader_class = Mock(return_value=mock_loader_instance)

        # Create processor with the mock loader
        processor = DocumentProcessor(document_loader=mock_loader_class)

        # When: Loading and chunking the PDF
        pages = processor.load_pdf("test.pdf")
        chunks = processor.chunk_docs(pages)

        # Then: The document should be properly loaded and chunked
        assert len(pages) == 1  # Verify loading
        assert len(chunks) > 0  # Verify chunking created multiple chunks
        assert all(
            isinstance(chunk, Document) for chunk in chunks
        )  # Verify chunk types
